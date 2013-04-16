#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
spike – a package manager running on top of git

Copyright © 2012, 2013  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import sys
import os
import re as regex
import grp as groupmodule
import pwd as usermodule
from subprocess import Popen, PIPE



_dragonsuite_directory_stack = []

class DragonSuite():
    '''
    A collection of utilities mimicing standard unix commands, however not full-blown
    '''
    
    @staticmethod
    def pipe(data, *commands):
        '''
        Process data through a filter pipeline
        
        @param   data:?           Input data
        @param   commands:*(?)→?  List of functions
        @return  :?               Output data
        '''
        rc = data
        for command in commands:
            rc = command(rc)
        return rc
    
    
    @staticmethod
    def basename(path):
        '''
        Strip the directory form one or more filenames
        
        @param   path:str|itr<str>  A filename or a list, or otherwise iteratable, of filenames
        @return  :str|list<str>     The filename strip, or if multiple, a list of stripped filenames
        '''
        if isinstance(path, str):
            return path[path.rfind(os.sep) + 1:] if os.sep in path else path
        else:
            return [(p[p.rfind(os.sep) + 1:] if os.sep in p else p) for p in path]
    
    
    @staticmethod
    def dirname(path):
        '''
        Strip last component from one or more filenames
        
        @param   path:str|itr<str>  A filename or a list, or otherwise iteratable, of filenames
        @return  :str|list<str>     The filename strip, or if multiple, a list of stripped filenames
        '''
        def _dirname(p):
            if os.sep in p[:-1]:
                rc = p[:p[:-1].rfind(os.sep)]
                return rc[:-1] if p.endswith(os.sep) else rc
            else:
                return '.'
        if isinstance(path, str):
            return _dirname(path)
        else:
            return [_dirname(p) for p in path]
    
    
    @staticmethod
    def uniq(items, issorted = True):
        '''
        Remove duplicates
        
        @param   items:itr<¿E?>  An iteratable of items
        @param   issorted:bool   Whether the items are already sorted, otherwise a standard sort is preform
        @return  :list<¿E?>      A list with the input items but without duplicates
        '''
        if len(items) == 0:
            return []
        rc = [items[0]]
        last = items[0]
        sorteditems = items if issorted else sorted(items)
        for item in sorteditems:
            if item != last:
                rc.append(item)
                last = item
        return rc
    
    
    @staticmethod
    def sort(items, reverse = True):
        '''
        Sort a list of items
        
        @param   items:list<¿E?>  Unsorted list of items
        @param   reverse:bool     Whether to sort in descending order
        @return  :list<¿E?>       Sort list of items
        '''
        return sorted(items, reverse = reverse)
    
    
    @staticmethod
    def tac(items):
        '''
        Reverse a list of items
        
        @param   items:list<¿E?>  The list of items
        @return  :list<¿E?>       The list of items in reversed order
        '''
        return reversed(items)
    
    
    @staticmethod
    def readlink(path):
        '''
        Gets the file one or more link is directly pointing to, this is not the realpath, but if
        you do this recursively you should either get the realpath or get stuck in an infinite loop
        
        @param   path:str|itr<str>  A filename or a list, or otherwise iteratable, of filenames
        @return  :str|list<str>     The filename strip, or if multiple, a list of stripped filenames
        '''
        if isinstance(path, str):
            return os.readlink(path)
        else:
            return [os.readlink(p) for p in path]
    
    
    @staticmethod
    def cut(items, delimiter, fields, complement = False, onlydelimited = False, outputdelimiter = None):
        '''
        Remove sections of items by delimiters
        
        @param   items:itr<str>        The items to modify
        @param   delimiter:str         Delimiter
        @param   fields:int|list<int>  Fields to join, in joining order
        @param   complement:bool       Join the fields as in order when not in `fields`
        @param   onlydelimited:bool    Whether to remove items that do not have the delimiter
        @param   outputdelimiter:str?  Joiner, set to same as delimiter if `None`
        @return  :list<str>            The items after the modification
        '''
        rc = []
        od = delimiter if outputdelimiter is None else outputdelimiter
        f = fields if isinstance(fields, list) else [fields]
        if complement:
            f = set(f)
        for item in items:
            if onlydelimited and delimiter not in item:
                continue
            item = item.split(delimiter)
            if complement:
                x = []
                for i in range(0, len(item)):
                    if i not in f:
                        x.append(item[x])
                item = x
            else:
                item = [item[i] for i in f]
            rc.append(od.join(item))
        return rc
    
    
    @staticmethod
    def cat(files, encoding = None):
        '''
        Read one or more files a create a list of all their combined LF lines in order
        
        @param   files:str|itr<str>  The file or files to read
        @param   encoding:str?       The encoding to use, default if `None`
        @return  :list<str>          All lines in all files
        '''
        rc = []
        mode = 'r' if encoding is None else 'rb'
        fs = [files] if isinstance(files, str) else files
        for f in fs:
            with open(f, mode):
                if encoding is None:
                    rc += f.read().split('\n')
                else:
                    rc += f.read().encode(encoding, 'replace').split('\n')
        return rc
    
    
    @staticmethod
    def pwd():
        '''
        Gets the current working directory
        
        @return  :str  The current working directory
        '''
        return os.getcwd()
    
    
    @staticmethod
    def cd(path):
        '''
        Changes the current working directory
        
        @param  path:str  The new current working directory
        '''
        os.chdir(path)
    
    
    @staticmethod
    def pushd(path):
        '''
        Stores the current working directory in a stack change it
        
        @param  path:str  The new current working directory
        '''
        _dragonsuite_directory_stack.append(os.getcwd())
        os.chdir(path)
    
    
    @staticmethod
    def popd():
        '''
        Changes the current working directory to the one in the top of the `pushd` stack and pop it
        '''
        os.chdir(_dragonsuite_directory_stack.pop())
    
    
    @staticmethod
    def umask(mask = 0o22):
        '''
        Sets the current umask and return the previous umask
        
        @param   mask:int  The new umask
        @return  :int      The previous umask
        '''
        return os.umask(mask)
    
    
    @staticmethod
    def comm(list1, list2, mode):
        '''
        Compare two list
        
        @param   list1:itr<¿E?>  The first list
        @param   list2:itr<¿E?>  The second list
        @param   mode:int        0: Keep elements that do not appear in both lists
                                 1: Keep elements that only appear in the first list
                                 2: Keep elements that only appear in the second list
                                 3: Keep elements that only appear in both lists
        @return  :list<¿E?>      The result it will be sorted and contain no duplicates
        '''
        items = [(e, 1) for e in list1] + [(e, 2) for e in list2]
        items = sorted(rc, key = lambda x : x[0])
        last = items[0]
        (rc, tmp) = ([], [])
        for item in items:
            if item[0] == last[0]:
                tmp.pop()
                tmp.append((item[0], item[1] | last[1]))
            else:
                tmp.append(item)
        mode0 = mode == 0;
        for item in tmp:
            if item[1] == mode:
                rc.append(item[0])
            elif mode0 and item[1] != 3:
                rc.append(item[0])
        return rc
    
    
    @staticmethod
    def unset(var):
        '''
        Deletes an environment variable
        
        @param  var:str  The environment variable
        '''
        os.unsetenv(var)
        if var in os.environ:
            del os.environ[var]
    
    
    @staticmethod
    def export(var, value):
        '''
        Sets an environment variable
        
        @param  var:str     The environment variable
        @param  value:str?  The environment variable's new value, deletes it if `None`
        '''
        if value is None:
            unset(var)
        else:
            os.putenv(var, value)
            if var not in os.environ or os.environ[var] != value:
                os.environ[var] = value
    
    
    @staticmethod
    def get(var, default = ''):
        '''
        Gets an environment variable
        
        @param   var:str       The environment variable
        @param   default:str?  Default value to use if not defined
        @return  :str?         The environment variable's value
        '''
        return os.getenv(var, default)
    
    
    @staticmethod
    def chmod(path, mode, mask = ~0):
        '''
        Changes the protection bits of one or more files
        
        @param  path:str|itr<str>  The file or files
        @param  mode:int           The desired protection bits
        @param  mask:int           The portions of `mode` to apply
        '''
        for p in ([path] if isinstance(path, str) else path):
            if mask == ~0:
                os.lchmod(p, mode)
            else:
                cur = os.lstat(path).st_mode
                os.lchmod(p, mode | (cur & ~mask))
    
    
    @staticmethod
    def chown(path, owner = -1, group = -1):
        '''
        Changes the owner or group of one or more files
        
        @param  path:str|itr<str>  The file or files
        @param  owner:int|str      The new owner, `-1` for ignored
        @param  group:int|str      The new group, `-1` for ignored, `-2` to select by owner
        '''
        u = owner if isinstance(owner, int) else usermodule.getpwnam(owner).pw_uid
        g = group if isinstance(group, int) else groupmodule.getgrnam(group).gr_gid
        for p in ([path] if isinstance(path, str) else path):
            os.lchown(p, u, usermodule.getpwuid(os.lstat(path).st_uid).pw_gid if g == -2 else g)
    
    
    @staticmethod
    def chgrp(path, group):
        '''
        Changes the group of one or more files
        
        @param  path:str|itr<str>  The file or files
        @param  group:int|str      The new group
        '''
        chown(path, group = group)
    
    
    @staticmethod
    def ln(source, link, hard = False):
        '''
        Create a symbolic or hard link
        
        @param  source:str  The target of the new link
        @param  link:str    The path of the new link
        @param  hard:bool   Whether to create a hard link
        '''
        if hard:
            os.link(source, link)
        else:
            os.symlink(source, link)
    
    
    @staticmethod
    def touch(path, settime = False):
        '''
        Create one or more files if missing
        
        @param  path:str|itr<str>  The file of files
        @param  settime:bool       Whether to set the timestamps on the files if they already exists
        '''
        for p in ([path] if isinstance(path, str) else path):
            if os.path.exists(p):
                if settime:
                    os.utime(p, None)
            else:
                open(p, 'a').close()
    
    
    @staticmethod
    def rm(path, recursive = False, directories = False):
        '''
        Remove one or more file
        
        @param  path:str|itr<str>  Files to remove
        @param  recursive:bool     Remove directories recursively
        @param  directories:bool   Attempt to remove directories with rmdir, this is forced for recursive removes
        '''
        for p in ([path] if isinstance(path, str) else path):
            if not recursive:
                if dirs and os.path.isdir(p):
                    os.rmdir(p)
                elif get('shred', None) is not None:
                    execute(get('shred').split(' ') + [p], fail = True)
                else:
                    os.remove(p)
            else:
                rm(tac(find(p)), directories = True)
    
    
    @staticmethod
    def rm_r(path):
        '''
        Remove a file or recursively a directory, multile are also possible
        
        @param  path:str|itr<str>  The files to remove
        '''
        rm(path, recursive = True)
    
    
    @staticmethod
    def rmdir(path):
        '''
        Remove one or more directories
        
        @param  path:str|itr<str>  The directories to remove
        '''
        for p in ([path] if isinstance(path, str) else path):
            os.rmdir(p)
    
    
    @staticmethod
    def mkdir(path, recursive = False):
        '''
        Create one or more directories, it will not fail if the path already exists and is a directory
        
        @param  path:str|itr<str>  The directories to create
        @param  recursive:bool     Whether to create all missing intermediate-level directories
        '''
        for p in ([path] if isinstance(path, str) else path):
            if not recursive:
                if not (os.path.exists(p) and os.path.isdir(p)):
                    os.mkdir(p)
            else:
                ps = p.split(os.sep)
                pp = ps[0]
                for _p in ps[1:]:
                    pp += os.sep + _p
                    if not (os.path.exists(pp) and os.path.isdir(pp)):
                        os.mkdir(pp)
    
    
    @staticmethod
    def mkdir_p(path):
        '''
        Create on ore more directories, and create all missing intermediate-level directories
        
        @param  path:str|itr<str>  The directories to create
        '''
        mkdir(path, recursive = True)
    
    
    @staticmethod
    def mkcd(path, recursive = False):
        '''
        Create a directory and `cd` into it, it will not fail if the path already exists and is a directory
        
        @param  path:str        The directory to create and move into
        @param  recursive:bool  Whether to create all missing intermediate-level directories
        '''
        mkdir(path, recursive)
        cd(path)
    
    
    @staticmethod
    def git(*params):
        '''
        Execute git
        
        @param  params:*str  Arguments for the command
        '''
        execute(['git'] + params, fail = True)
    
    
    @staticmethod
    def curl(*params):
        '''
        Execute curl
        
        @param  params:*str  Arguments for the command
        '''
        execute(['curl'] + params, fail = True)
    
    
    @staticmethod
    def wget(*params):
        '''
        Execute wget
        
        @param  params:*str  Arguments for the command
        '''
        execute(['wget'] + params, fail = True)
    
    
    @staticmethod
    def make(*params):
        '''
        Execute make
        
        @param  params:*str  Arguments for the command
        '''
        execute(['make'] + params, fail = True)
    
    
    @staticmethod
    def rename(path, expression, replacement):
        '''
        Rename multiple files with a pattern using util-linux's command rename
        
        @param  path:str|list<str>  File or files to rename
        @param  expression:str      Matching expression
        @param  replacement:str     Replacement
        '''
        files = [path] if isinstance(path, str) else path
        execute(['rename', '--', expression, replacement] + files, fail = True)
    
    
    @staticmethod
    def upx(path, level = 8, overlay = 1, brute = 0):
        '''
        Compress one or more files using the command upx
        
        @param  path:str|list<str>  The files to compress
        @param  level:int           Compression level, [1; 10], 10 for --best
        @param  overlay:int         0: --overlay=skip
                                    1: --overlay=copy
                                    2: --overlay=strip
        @param  brute:int           0: no addition parameter
                                    1: --brute
                                    2: --ultra-brute
        '''
        params = ['upx', '-%i' % level if level < 10 else '--best']
        if overlay == 0:  params += ['--overlay=skip']
        if overlay == 2:  params += ['--overlay=strip']
        if brute == 1:  params += ['--brute']
        if brute == 2:  params += ['--ultra-brute']
        params += ['--', path] if isinstance(path, str) else (['--'] + path)
        execute(params, fail = False)
    
    
    @staticmethod
    def strip(path, *params):
        '''
        Strip symbols from binaries and libraries using the command strip
        
        @param  path:str|list<str>  The files to compress
        @param  params:*str         Arguments for strip
        '''
        cmd = ['strip'] + params + (['--', path] if isinstance(path, str) else (['--'] + path))
        execute(cmd, fail = False)
    
    
    @staticmethod
    def installinfo(path):
        '''
        Update info/dir entries
        
        @param  path:str|list<str>  New or updated entries
        '''
        r = get('root', os.sep)
        i = get('infodir', '%susr%sshare%sinfo' % (os.sep, os.sep, os.sep))
        if not r.endswith(os.sep): r += os.sep
        if i.startswith(os.sep): i = i[1:]
        if not i.endswith(os.sep) and len(i) > 0: i += os.sep
        d = r + i + 'dir'
        for p in (['--', path] if isinstance(path, str) else (['--'] + path)):
            execute(['install-info', '--', p, d], fail = False)
    
    
    @staticmethod
    def mv(source, destination):
        '''
        Move one or more files
        
        @param  source:str|itr<str>  The files to move
        @param  destination:str      The destination, either directory or new file
        '''
        ps = [source] if isinstance(source, str) else source
        d = destination if destination.endswith(os.sep) else (destination + os.sep)
        if len(ps) == 1:
            if os.path.exists(destination) and os.path.isdir(destination):
                os.rename(source, d + basename(source))
            else:
                os.rename(source, destination)
        else:
            if not os.path.exists(destination):
                raise OSError('Destination %s does not exist but must be a directory' % destination)
            elif not os.path.isdir(destination):
                raise OSError('Destination %s exists and is not a directory' % destination)
            else:
                for p in ps:
                    os.rename(p, d + basename(p))
    
    
    @staticmethod
    def echo(text, newline = True, stderr = False):
        '''
        Display a line of text
        
        @param  text:str|list<str>  The text
        @param  newline:bool        Whether to end with a line break
        @param  stderr:bool         Whether to print to stderr
        '''
        s = sys.stdout.buffer if not stderr else sys.stderr.buffer
        if isinstance(text, str):
            s.write((text + ('\n' if newline else '')).encode('utf-8'))
        else
            s.write(('\n'.join(text) + ('\n' if newline else '')).encode('utf-8'))
    
    
    @staticmethod
    def msg(text, submessage = False):
        '''
        Display status message
        
        @param  text:str         The message
        @parma  submessage:bool  Whether this is a submessage
        '''
        message = '\033[01;3%im%s\033[00;01m %s\033[00m\n'
        message %= (2, ' -->', text) if submessage else (4, '==>', text)
        sys.stdout.buffer.write(message.encode('utf-8'))
    
    
    @staticmethod
    def cp(source, destination, recursive = True):
        '''
        Copies files and directories, note that you can do so much more with GNU ocreutils's cp
        
        @param  source:str|itr<str>   Files to copy
        @param  destination:str       Destination filename or directory
        '''
        install(source, destination, parents=False, recursive = recursive, savemode=True, preservecontext=False)
    
    
    @staticmethod
    def cp_r(source, destination):
        '''
        Copies files and directories, recursively
        
        @param  source:str|itr<str>   Files to copy
        @param  destination:str       Destination filename or directory
        '''
        cp(source, destination, True)
    
    
    @staticmethod
    def install(source, destination, owner = -1, group = -1, mode = -1, strip = False,
                directory = False, parents = True, recursive = True, savemode = True):
        '''
        Copies files and set attributes
        
        @param  source:str|itr<str>   Files to copy
        @param  destination:str       Destination filename or directory
        @param  owner:int|str         The new owner, `-1` for preserved
        @param  group:int|str         The new group, `-1` for preserved, `-2` to select by owner
        @param  mode:int              The desired protection bits, `-1` for preserved
        @param  strip:bool            Whether to strip symbol table
        @param  directory:bool        Whether treat all source files is directory names
        @param  parents:bool          Whether create missing directories
        @param  recursive:bool        Copy directories resursively
        @param  savemode:bool         Whether to use the protection bits of already installed versions
        '''
        ps = [source] if isinstance(source, str) else source
        d = destination if destination.endswith(os.sep) else (destination + os.sep)
        pairs = None
        if len(ps) == 1:
            if os.path.exists(destination) and os.path.isdir(destination):
                pairs = [(source, d + basename(source))]
            else:
                pairs = [source, destination)]
        else:
            if not os.path.exists(destination):
                if parents:
                    mkdir_p(destination)
                else:
                    raise OSError('Destination %s does not exist but must be a directory' % destination)
            elif not os.path.isdir(destination):
                raise OSError('Destination %s exists and is not a directory' % destination)
            else:
                for p in ps:
                    pairs = [p, d + basename(p)]
        for (src, dest) in pairs:
            protection = mode
            if savemode and os.path.exists(dest):
                protection = os.lstat(dest).st_mode
            elif mode < 0:
                protection = 0x755 if directory else os.lstat(src).st_mode
            if directory or os.path.isdir(src):
                mkdir(dest)
            else:
                blksize = 8192
                try:
                    blksize = os.stat(os.path.realpath(ifile)).st_blksize
                except:
                    pass
                with open(src, 'rb') as ifile:
                    with open(dest, 'wb') as ofile:
                        while True:
                            chunk = ifile.read(blksize)
                            if len(chunk) == 0:
                                break
                            ofile.write(chunk)
            (u, g) = (owner, group)
            stat = os.lstat(src)
            u = u if isinstance(u, str) or u != -1 else stat.st_uid
            g = g if isinstance(g, str) or g != -1 else stat.st_gid
            chown(dest, u, g)
            os.lchmod(dest, protection)
            if strip and not directory:
                strip(dest)
            if recursive and os.path.isdir(src) and not directory:
                d = dest if dest.endswith(os.sep) else (dest + os.sep)
                sources = [d + f for f in os.listdir()]
                install(sources, dest, owner, group, mode, strip, False, False, True, savemode)
    
    
    @staticmethod
    def find(path, maxdepth = -1, hardlinks = True):
        '''
        Gets all existing subfiles, does not follow links including hardlinks
        
        @param   path:str|itr<str>  Search root or roots
        @param   maxdepth:int       Maximum search depth, `-1` for unbounded
        @param   hardlinks:bool     Whether to list all files with same inode number rather than just the first
        @return  :list<str>         Found files
        '''
        rc = []
        visited = set()
        stack = [path] if isinstance(path, str) else path
        stack = [(e, 0) for e in stack]
        while len(stack) > 0:
            (f, d) = stack.pop()
            if os.path.exists(f):
                f = f if not f.endswith(os.sep) else f[:-1]
                if (not os.path.islink(f)) and os.path.isdir(f):
                    inode = os.lstat(f).st_ino
                    if inode not in visited:
                        visited.add(inode)
                        f += os.sep
                        if d != maxdepth:
                            d += 1
                            for sf in os.listdir():
                                stack.append((f + sf, d))
                    elif not hardlinks:
                        continue
                elif not hardlinks:
                    inode = os.lstat(f).st_ino
                    if inode in visited:
                        continue
                    visited.add(inode)
                rc.append(f)
        return rc
    
    
    @staticmethod
    def path(exprs, existing = False):
        '''
        Gets files matching a pattern
        
        Here     => Regular expression
        {a,b,c}  => (a|b|c)
        {a..g}   => [ag]
        {1..11}  => (1|2|3|4|5|6|7|8|9|10|11)
        *        => .*
        ?        => .
        
        Everything else is matched verbosely and the matching is closed (regex: ^pattern$),
        and \ is used to escape characters do that they are matched verbosely instead of
        getting a special meaning.
        Ending the pattern with / specified that it should be a directory.
        
        @param   exprs:str|itr<str>  Expressions
        @param   existing:bool       Whether to only match to existing files
        @return  :list<str>          Matching files
        '''
        def _(expr)
            ps = ['']
            esc = False
            buf = ''
            b = 0
            for c in expr.replace('\0', '').replace('/', ('\\' if os.sep in '?*{},.\\' else '') + os.sep):
                if esc:
                    esc = False
                    if b > 0:
                        buf += '\\'
                    buf += c
                elif c == '\\': esc = True
                elif c == '?':  buf += '\0?' if b == 0 else '?'
                elif c == '*':  buf += '\0*' if b == 0 else '*'
                elif c == ',':  buf += '\0,' if b == 1 else ','
                elif c == '.':  buf += '\0.' if b == 1 else '.'
                elif c == '{':
                    if b == 0:
                        ps = [p + buf for p in ps]
                        buf = ''
                    b += 1
                elif c == '}':
                    if b == 1:
                        t = [_(tp) for tp in buf.split('\0,')]
                        pz = []
                        for a in ps:
                            for b in t:
                                if '\0.' not in b:
                                    pz.append(a + b)
                                elif (len(b) - len(b.replace('\0.', '')) != 4) and ('\0.\0.' not in b):
                                    pz.append(a + b.replace('\0.', '.'))
                                elif b.startswith('\0.') or b.endswith('\0.')
                                    pz.append(a + b.replace('\0.', '.'))
                                else:
                                    (l, r) = b.split('\0.\0.')
                                    if len(string.strip(l + r, '0123456789')) == 0:
                                        step = 1 if int(l) <= int(r) else -1
                                        x = int(l) if step == 1 else int(r)
                                        n = int(r) if step == 1 else int(l)
                                        while x != n:
                                            pz.append(a + str(x))
                                            x += step
                                        pz.append(a + str(x))
                                    elif len(l) == 1 and len(r) == 1:
                                        step = 1 if ord(l) <= ord(r) else -1
                                        x = ord(l) if step == 1 else ord(r)
                                        n = ord(r) if step == 1 else ord(l)
                                        while x != n:
                                            pz.append(a + chr(x))
                                            x += step
                                        pz.append(a + chr(x))
                                    else:
                                        pz.append(a + b.replace('\0.', '.'))
                        ps = pz
                        pz = None
                        buf = ''
                    else:
                        buf += '}'
                    b -= 1
                else:
                    buf += c
            return [p + buf for p in ps]
        rc = []
        for expr in ([exprs] if isinstance(exprs, str) else exprs):
            for p in _(expr):
                if '\0' not in p:
                    rc.append(p)
                else:
                    f = ['']
                    if os.sep == '?': p = p.replace('\0?', '\0a')
                    if os.sep == '*': p = p.replace('\0*', '\0b')
                    parts = p.split(os.sep)
                    if os.sep == '?': parts = [p.replace('\0a', '\0?') for p in parts]
                    if os.sep == '*': parts = [p.replace('\0b', '\0*') for p in parts]
                    for p in parts:
                        if len(p) == 0:
                            pass
                        elif p == '.':
                            f = [(os.curdir if len(_) == 0 else _) for _ in f]
                        elif p == '..':
                            _f = []
                            for _ in f:
                                if len(_) == 0:
                                    _ = os.pardir
                                elif _ == os.pardir or _.endswith(os.sep + os.pardir):
                                    _ += os.sep + os.pardir
                                else:
                                    _ = _[:_.rfind('/')]
                                _f.append(_)
                            f = _f
                        elif '\0' not in p:
                            f = [(p if len(_) == 0 else (_ + os.sep + p)) for _ in f]
                        else:
                            _f = []
                            for _ in f:
                                root = os.curdir if len(_) == 0 else _
                                if os.path.exists(root) and not os.path.isdir(root):
                                    break
                                subs = os.listdir(root)
                                matches = []
                                s = p
                                for c in '\\.^+$[]|(){}':
                                    s = s.replace(c, '\\' + c)
                                _ = ''
                                esc = False
                                for c in s:
                                    if esc:
                                        _ += {'\0*' : '.*',  '\0?' : '.'}[c]
                                        esc = False
                                    elif c == '\0':
                                        esc = True
                                    else:
                                        _ += c
                                s = '^' + _.replace('?', '\\?').replace('*', '\\*') + '$'
                                matcher = regex.compile(s, regex.DOTALL)
                                for s in subs:
                                    if matcher.match(s) is not None:
                                        matches.append(s)
                                if len(_) > 0:
                                    _ += os.sep
                                for m in matches:
                                    _f.append(_ + m)
                            f = _f
        if not existing:
            return rc
        nrc = []
        for p in rc:
            if os.path.exists(p) and ((not p.endswith(os.sep)) or os.path.isdir(p)):
                nrc.append(p)
        return nrc
    
    
    @staticmethod
    def decompress(path, format = None):
        '''
        Decompres and extract archives
        
        Recognised formats, all using external programs:
        gzip*, bzip2*, xz*, lzma*, lrzip*, lzip*, lzop*, zip, shar, tar, cpio, squashfs
        Formats marked with and asteriks are recognised compressions for tar and cpio.
        
        @param  path:str|itr<str>  The file or files
        @param  format:str?        The format, `None` for automatic detection (currently uses file extension)
        '''
        for p in ([path] if isinstance(path, str) else path):
            p = '\'' + p.replace('\''. '\'\\\'\'') + '\''
            fmt = format
            if fmt is None:
                fmt = fmt[fmt.rfind(os.sep) + 1:]
                if '.tar.' in fmt:
                    fmt = fmt[:fmt.rfind(os.extsep):] + fmt[fmt.rfind(os.extsep) + 1:]
                fmt = fmt[fmt.rfind(os.extsep) + 1:]
            havecpio = False
            for d in get('PATH').split(os.pathsep):
                if not d.endswith(os.sep):
                    d += os.sep
                if os.path.exists(d + 'cpio'):
                    havecpio = True
                    break
            fmt = {'gz' : 'gzip -d %s',
                   'bz' : 'bzip2 -d %s',
                   'bz2' : 'bzip2 -d %s',
                   'xz' : 'xz -d %s',
                   'lzma' : 'lzma -d %s',
                   'lrz' : 'lrzip -d %s',
                   'lz' : 'lzip -d %s',
                   'lzop' : 'lzop -d %s',
                   'z' : 'unzip %s',
                   'tar' : 'tar --get < %s',
                   'tgz' : 'tar --gzip --get < %s',
                   'targz' : 'tar --gzip --get < %s',
                   'tarbz' : 'tar --bzip2 --get < %s',
                   'tarbz2' : 'tar --bzip2 --get < %s',
                   'tarxz' : 'tar --xz --get < %s',
                   'tarlzma' : 'tar --lzma --get < %s',
                   'tarlz' : 'tar --lzip --get < %s',
                   'tarlzop' : 'tar --lzop --get < %s',
                   'tarlrz' : 'lzrip -d < %s | tar --get',
                   'cpio' : 'cpio --extract < %s',
                   'cpiogz' : 'gzip -d < %s | cpio --extract',
                   'cpiobz' : 'bzip2 -d < %s | cpio --extract',
                   'cpiobz2' : 'bzip2 -d < %s | cpio --extract',
                   'cpioxz' : 'xz -d < %s | cpio --extract',
                   'cpiolzma' : 'lzma -d < %s | cpio --extract',
                   'cpiolz' : 'lzip -d < %s | cpio --extract',
                   'cpiolzop' : 'lzop -d < %s | cpio --extract',
                   'cpiolrz' : 'lrzip -d < %s | cpio --extract',
                   'shar' : 'sh %s',
                   'sfs' : 'unsquashfs %s',
                   'squashfs' : 'unsquashfs %s'}[fmt.lower().replace(os.extsep, '').replace('zip', 'z')]
            if not havecpio:
                fmt = fmt.replace('cpio', 'bsdcpio')
            sh(fmt % p, fail = True)


## TODO:
#  grep /usr/bin/egrep (-o = False)
#  patch /usr/bin/patch
#  sed /usr/bin/sed
#  execute (fail = False)
#  bash /bin/sh (fail = False)
#  sha3sum (only keccak[])

