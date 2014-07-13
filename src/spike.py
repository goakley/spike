#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
spike – a package manager running on top of git

Copyright © 2012, 2013, 2014  Mattias Andrée (maandree@member.fsf.org)

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
from subprocess import Popen

from library.libspike import *
from auxiliary.argparser import ArgumentCommandParser
from auxiliary.printhacks import *



SPIKE_VERSION = '0.1'
'''
This version of spike
'''


SPIKE_DEBUG = os.getenv('SPIKE_DEBUG', '') == 'yes'
'''
Whether spike has been started in debug mode
'''



class Spike():
    '''
    Spike is your number one package manager
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        self.version = SPIKE_VERSION
        self.execprog = 'spike'
        self.prog = 'spike'

    
    def mane(self, args):
        '''
        Run this method to invoke Spike as if executed from the shell
        
        Exit values:  0 - Successful
                      1 - Option use error
                      2 - Non-option argument use error
                      3 - -h(--help) was used
                      4 - Invalid option argument
                      5 - Root does not exist
                      6 - Scroll does not exist
                      7 - Pony is not installed
                      8 - Pony conflict
                      9 - Dependency does not exist
                     10 - File is already claimed
                     11 - File was claimed for another pony
                     12 - File does not exist
                     13 - File already exists
                     14 - Information field is not definied
                     15 - Starting interactive mode from pipe
                     16 - Compile error
                     17 - Installation error, usually because --private or root is needed
                     18 - Private installation is not supported
                     19 - Non-private installation is not supported
                     20 - Scroll error
                     21 - Pony ride error
                     22 - Proofread found scroll error
                     23 - File access denied
                     24 - Cannot pull git repository
                     25 - Cannot checkout git repository
                     26 - File is of wrong type, normally a directory or regular file when the other is expected
                     27 - Corrupt database
                     28 - Pony is required by another pony
                     29 - Circular make dependency
                    254 - User aborted
                    255 - Unknown error
        
        @param  args:list<str>  Command line arguments, including invoked program alias ($0)
        '''
        self.execprog = args[0].split('/')[-1]
        
        usage = self.prog + ' [command] [option]... [FILE... | FILE... SCROLL | SCROLL...]'
        usage = usage.replace('spike',   '\033[35m' 'spike'   '\033[00m')
        usage = usage.replace('command', '\033[33m' 'command' '\033[00m')
        usage = usage.replace('option',  '\033[33m' 'option'  '\033[00m')
        usage = usage.replace('FILE',    '\033[04m' 'FILE'    '\033[00m')
        usage = usage.replace('SCROLL',  '\033[04m' 'SCROLL'  '\033[00m')
        if tty:
            usage = usage.replace('\033[04m', '\033[34m')
        
        usage = usage.replace('\033[', '\0')
        for sym in ('[', ']', '(', ')', '|', '...', '*'):
            usage = usage.replace(sym, '\033[02m' + sym + '\033[22m')
        usage = usage.replace('\0', '\033[')
        
        opts = ArgumentCommandParser(
            'spike', usage=usage,
            description='a package manager running on top of git\n\n'
            'spike is used to spike your system with new ponies or and new versions\n'
            'of ponies (known on other systems as packages). spike the capaility of\n'
            'not only installing ponies, but also archive an installation and\n'
            'simply roll back to it in case the system broke, an must have feature\n'
            'on unstable OS:es. spike uses so called scrolls to install ponies,\n'
            'these are written, for maximum simplicity and portability, in Python 3\n'
            'and a collection of these are distributed with spike and updated when\n'
            'spike is updated. But you can add scroll repositories to spike on your\n'
            'local installation.',
            tty=tty
        )
        
        opts.add_command('-v', '--version', nargs=0,
                         help='Print program name and version')
        opts.add_command('-c', '--copyright', nargs=0,
                         help='Print copyright information')

        opts.add_command('-B', '--bootstrap', nargs=0,
                         help='Update spike and scroll repositories',
                         options=['--no-verify'])
        opts.add_command('-F', '--find', nargs='+', metavar='SCROLL',
                         help='Find a scroll either by name or by ownership',
                         options=['--owner', '--written'])
        opts.add_command('-W', '--write', nargs='+', metavar='SCROLL',
                         help='Install a pony (package) from scroll',
                         options=['--pinpal', '--private', '--asdep', '--asexplicit', '--nodep', '--force', '--shred'])
        opts.add_command('-U', '--update', nargs=0,
                         help='Update to new versions of the installed ponies',
                         options=['--pinpal', '--ignore', '--private', '--shred'])
        opts.add_command('-E', '--erase', nargs='+', metavar='SCROLL',
                         help='Uninstall a pony',
                         options=['--pinpal', '--private', '--shred'])
        opts.add_command(None, '--demote', nargs='+', metavar='SCROLL',
                         help='Demote pony to a dependency',
                         options=['--private'])
        opts.add_command(None, '--promote', nargs='+', metavar='SCROLL',
                         help='Promote pony to explicitly installed',
                         options=['--private'])
        opts.add_command('-X', '--ride', nargs=1, metavar='SCROLL',
                         help='Execute a scroll after best effort',
                         options=['--private'])
        opts.add_command('-R', '--read', nargs='+', metavar='SCROLL',
                         help='Get scroll information',
                         options=['--list', '--info', '--written'])
        opts.add_command('-C', '--claim', nargs='+', metavar='FILE',
                         help='Claim one or more files as owned by a pony',
                         options=['--recursive', '--entire', '--private', '--force'])
        opts.add_command('-D', '--disclaim', nargs='+', metavar='FILE',
                         help='Disclaim one or more files as owned by a pony',
                         options=['--recursive', '--private'])
        opts.add_command('-A', '--archive', nargs=1, metavar='ARCHIVE',
                         help='Create an archive of everything that is currently installed.',
                         options=['--scrolls'])
        opts.add_command(None, '--restore-archive', nargs=1, metavar='ARCHIVE',
                         help='Roll back to an archived state of the system',
                         options=['--shared', '--full', '--old', '--downgrade', '--upgrade', '--shred'])
        opts.add_command('-N', '--clean', nargs=0,
                         help='Uninstall unneeded ponies',
                         options=['--private', '--shred'])
        opts.add_command('-P', '--proofread', nargs='+', metavar='SCROLL',
                         help='Verify that a scroll is correct')
        opts.add_command('-S', '--example-shot', nargs='+', metavar='SCROLL',
                         help='Display example shot for scrolls',
                         options=['--viewer', '--all-at-once'])
        opts.add_command('-I', '--interactive', nargs=0,
                         help='Start in interative graphical terminal mode (supports installation and uninstallation only)',
                         options=['--shred'])
        opts.add_command('-3', '--sha3sum', nargs='+', metavar='FILE',
                         help='Calculate the SHA3 checksums for files (do not expect files to be listed in order)')

        opts.add_argument('-o', '--owner', action='store_true',
                          help='Find owner pony for file')
        opts.add_argument('-w', '--written', choices=['y', 'n'], metavar='boolean',
                          help='Search only for installed (\'y\') or not installed (\'n\') ponies')
        opts.add_argument(      '--pinpal', metavar='ROOT',
                                help='Mounted system for which to do installation or unstallation')
        opts.add_argument('-u', '--private', action='store_true',
                          help='Private pony installation')
        opts.add_argument(      '--asdep', action='store_true',
                                help='Install pony as implicitly installed (a dependency)')
        opts.add_argument(      '--asexplicit', action='store_true',
                                help='Install pony as explicitly installed (no longer a dependency)')
        opts.add_argument(      '--nodep', action='store_true',
                                help='Do not install dependencies')
        opts.add_argument(      '--force', action='store_true',
                                help='Ignore file claims')
        opts.add_argument('-i', '--ignore', nargs='+', metavar='SCROLL',
                          help='Ignore update of a pony')
        opts.add_argument('-l', '--list', action='store_true',
                          help='List files claimed (done at installation) for a pony')
        opts.add_argument('-f', '--info', nargs='+', metavar='FIELD',
                          help='Retrieve a specific scroll information field')
        opts.add_argument(      '--recursive', action='store_true',
                                help='Recursively claim or disclaim directories')
        opts.add_argument(      '--entire', action='store_true',
                                help='Recursively claim directories and their future content')
        opts.add_argument('-s', '--scrolls', action='store_true',
                          help='Do only archive scrolls, no installed files')
        opts.add_argument(      '--shared', action='store_true',
                                help='Reinstall only ponies that are currently installed and archived')
        opts.add_argument(      '--full', action='store_true',
                                help='Uninstall ponies that are not archived')
        opts.add_argument(      '--old', action='store_true',
                                help='Reinstall only ponies that are currently not installed')
        opts.add_argument(      '--downgrade', action='store_true',
                                help='Do only perform pony downgrades')
        opts.add_argument(      '--upgrade', action='store_true',
                                help='Do only perform pony upgrades')
        opts.add_argument(      '--shred', action='store_true',
                                help='Perform secure removal with `shred` when removing old files')
        opts.add_argument(      '--no-verify', action='store_true',
                                help='Skip verification of signatures')
        opts.add_argument('-a', '--all-at-once', action='store_true',
                          help='Display all example shots in one single process instance')
        opts.add_argument(      '--viewer', metavar='VIEWER',
                                help='Select image viewer for example shots')

        opts.add_exclusivity('-o', '-w')
        opts.add_exclusivity('--pinpal', '-u')
        opts.add_exclusivity('--pinpal', '--private')
        opts.add_exclusivity('--asdep', '--asexplicit')
        opts.add_exclusivity('-l', '-f')
        opts.add_exclusivity('--recursive', '--entire')
        opts.add_exclusivity('--shared', '--full', '--old')
        opts.add_exclusivity('--downgrade', '--upgrade')
        
        parse = opts.parse_args(args)
        command = parse.COMMAND

        exit_value = 0

        if parse.COMMAND not in ['help', 'version', 'copyright']:
            LibSpike.initialise(shred = parse.shred)

        try:

            if command == 'help':
                opts.help()
                exit_value = 3

            elif command == 'version':
                self.print_version()

            elif command == 'copyright':
                self.print_copyright()

            elif command == 'sha3sum':
                exit_value = self.sha3sum(parse.ARGS)

            elif command == 'bootstrap':
                exit_value = self.bootstrap(parse.no_verify)

            elif command == 'find':
                if parse.written:
                    exit_value = self.find_scroll(parse.ARGS,
                                                  installed    = parse.written == 'y',
                                                  notinstalled = parse.written == 'n')
                elif parse.owner:
                    exit_value = self.find_owner(parse.ARGS)
                else:
                    exit_value = self.find_scroll(parse.ARGS, installed = True, notinstalled = True)

            elif command == 'write':
                exit_value = self.write(parse.ARGS,
                                        root         = parse.pinpal if parse.pinpal else '/',
                                        private      = parse.private,
                                        explicitness = 1 if parse.asexplicit else -1 if parse.asdep else 0,
                                        nodep        = parse.nodep,
                                        force        = parse.force)

            elif command == 'update':
                exit_value = self.update(root    = parse.pinpal if parse.pinpal else '/',
                                         ignores = parse.ignore if parse.ignore else [],
                                         private = parse.private)

            elif command == 'erase':
                exit_value = self.erase(parse.ARGS,
                                        root    = parse.pinpal if parse.pinpal else '/',
                                        private = parse.private)

            elif command == 'ride':
                exit_value = self.ride(parse.ARGS[0],
                                       private = parse.private)

            #elif command == 'demote': ### TODO: implement demote
            #    exit_value = self.demote(parse.ARGS,
            #                             private = parse.private)

            #elif command == 'promote': ### TODO: implement promote
            #    exit_value = self.promote(parse.ARGS,
            #                              private = parse.private)

            elif command == 'read':
                if parse.written:
                    exit_value = self.read_info(parse.ARGS,
                                                field        = parse.info if parse.info else [],
                                                installed    = parse.written == 'y',
                                                notinstalled = parse.written == 'n')
                else:
                    exit_value = self.read_info(parse.ARGS,
                                                field = parse.info if parse.info else [])

            elif command == 'claim':
                exit_value = self.claim(parse.ARGS[:-1], parse.ARGS[-1],
                                        private       = parse.private,
                                        recursiveness = 1 if parse.recursive else -1 if parse.entire else 0,
                                        force         = parse.force)

            elif command == 'disclaim':
                exit_value = self.disclaim(parse.ARGS[:-1], parse.ARGS[-1],
                                           private       = parse.private,
                                           recursiveness = 1 if parse.recursive else -1 if parse.entire else 0,
                                           force         = parse.force)

            elif command == 'archive':
                exit_value = self.archive(parse.ARGS[0],
                                          scrolls = parse.scrolls)
                
            elif command == 'restore_archive':
                exit_value = self.rollback(parse.ARGS[0],
                                           keep      = parse.full,
                                           skip      = parse.shared,
                                           gradeness = 1 if parse.downgrade else -1 if parse.upgrade else 0)

            elif command == 'proofread':
                exit_value = self.proofread(parse.ARGS)

            elif command == 'clean':
                exit_value = self.clean(private=parse.private)

            elif command == 'example_shot':
                env_display = os.environ['DISPLAY']
                default_viewer = 'xloadimage' if (env_display is not None) and env_display.startsWith(':') else 'jfbview'
                exit_value = self.example_shot(parse.ARGS,
                                               viewer      = parse.viewer if parse.viewer else default_viewer,
                                               all_at_once = flags.all_at_once)

            elif command == 'interactive':
                exit_value = self.interactive()

            else:
                raise Exception('Argument list not properly handled')
        
        except Exception as err:
            exit_value = 255
            printerr('%s: %s' % (self.execprog, str(err)))
            if SPIKE_DEBUG:
                raise err
        
        if exit_value == 27:
            printerr('%s: \033[01;31m%s\033[00m' % (self.execprog, 'corrupt database'))
        
        LibSpike.terminate()
        exit(exit_value)
    
    
    
    def print_version(self):
        '''
        Prints spike followed by a blank spacs and the version of spike to stdout
        '''
        print('spike ' + self.version)
    
    
    def print_copyright(self):
        '''
        Prints spike copyright notice to stdout
        '''
        print('spike – a package manager running on top of git\n'
              '\n'
              'Copyright © 2012, 2013, 2014  Mattias Andrée (maandree@member.fsf.org)\n'
              '\n'
              'This program is free software: you can redistribute it and/or modify\n'
              'it under the terms of the GNU General Public License as published by\n'
              'the Free Software Foundation, either version 3 of the License, or\n'
              '(at your option) any later version.\n'
              '\n'
              'This program is distributed in the hope that it will be useful,\n'
              'but WITHOUT ANY WARRANTY; without even the implied warranty of\n'
              'MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n'
              'GNU General Public License for more details.\n'
              '\n'
              'You should have received a copy of the GNU General Public License\n'
              'along with this program.  If not, see <http://www.gnu.org/licenses/>.')
    
    
    
    def bootstrap(self, verify):
        '''
        Update the spike and the scroll archives
        
        @param   verify:bool  Whether to verify signatures
        @return  :byte        Exit value, see description of `mane` 
        '''
        class Agg:
            '''
            aggregator:(str, int)→void
                Feed a directory path and 0 when a directory is enqueued for bootstraping.
                Feed a directory path and 1 when a directory bootstrap process is beginning.
                Feed a directory path and 2 when a directory bootstrap process has ended.
            '''
            def __init__(self):
                self.colour_map = (3, 4, 2)
                self.message_map = ('QUEUED', 'WORKING', 'DONE')
            def __call__(self, directory, state):
                print('\033[01;3%im%s [%s]\033[00m' % (self.colour_map[state], directory, self.message_map[state]))
        
        return LibSpike.bootstrap(Agg(), verify)
    
    
    def find_scroll(self, patterns, installed = True, notinstalled = True):
        '''
        Search for a scroll
        
        @param   patterns:list<str>  Regular expression search patterns
        @param   installed:bool      Look for installed packages
        @param   notinstalled:bool   Look for not installed packages
        @return  :byte               Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str)→void
                Feed a scroll when one matching one of the patterns has been found.
            '''
            def __init__(self):
                pass
            def __call__(self, found):
                print(found)
        
        return LibSpike.find_scroll(Agg(), patterns, installed, notinstalled)
    
    
    def find_owner(self, files):
        '''
        Search for a files owner pony, includes only installed ponies
        
        @param   files:list<string>  Files for which to do lookup
        @return  :byte               Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str, str?)→void
                Feed a file path and a scroll when an owner has been found.
                Feed a file path and `None` when it as been determined that their is no owner.
            '''
            def __init__(self):
                pass
            def __call__(self, filepath, owner):
                if owner is None:
                    print('%s is owner by %s\n' % (filepath, owner))
                else:
                    print('%s has not owner\n' % filepath)
        
        return LibSpike.find_owner(Agg(), files)
    
    
    def write(self, scrolls, root = '/', private = False, explicitness = 0, nodep = False, force = False):
        '''
        Install ponies from scrolls
        
        @param   scrolls:list<str>  Scroll to install
        @param   root:str           Mounted filesystem to which to perform installation
        @param   private:bool       Whether to install as user private
        @param   explicitness:int   -1 for install as dependency, 1 for install as explicit, and 0 for explicit if not previously as dependency
        @param   nodep:bool         Whether to ignore dependencies
        @param   force:bool         Whether to ignore file claims
        @return  :byte              Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str?, int, [*])→(void|bool|str|int?)
                Feed a scroll (`None` only at state 0, 3, 6, 7 and 9) and a state (can be looped) during the process of a scroll.
                The states are: 0 - inspecting installed scrolls
                                1 - proofreading
                                2 - scroll added because of being updated
                                3 - resolving conflicts
                                4 - scroll added because of dependency. Additional parameters: requirers:list<str>
                                5 - scroll removed because due to being replaced. Additional parameters: replacer:str
                                6 - verify installation. Additional parameters: fresh_installs:list<str>, reinstalls:list<str>, update:list<str>, downgrading:list<str>, skipping:list<str>
                                                         Return: accepted:bool
                                7 - inspecting non-install scrolls for providers
                                8 - select provider pony. Additional parameters: options:list<str>
                                                          Return: select provider:str? `None` if aborted
                                9 - select when to build ponies which require interaction. Additional parameters: interactive:list<str>, allowed:int
                                                                                           Return: when:excl-flag? `None` if aborted
                               10 - fetching source. Additional parameters: source:str, progress state:int, progress end:int
                               11 - verifying source. Additional parameters: progress state:int, progress end:int
                               12 - compiling
                               13 - file conflict check: Additional parameters: progress state:int, progress end:int
                               14 - installing files: Additional parameters: progress state:int, progress end:int
                when:excl-flag values: 0 - Build whenever
                                       1 - Build early
                                       2 - Build early and fetch separately
                                       3 - Build late
                allowed:int values: The union of all `1 << when` with allowed `when`
            '''
            def __init__(self):
                self.update_add = set()
                self.dep_add = {}
                self.replace_remove = {}
                self.scrls = []
                for i in range(6):
                    self.scrls.append([0, {}])
                self.scrls[0] = self.scrls[1]
            def __call__(self, scroll, state, *args):
                if type(self) == Spike:
                    if scroll.equals('rarity'):
                        scroll = scroll + '♥'
                    elif scroll.startswith('rarity='):
                        scroll = scroll.replace('=', '♥=')
                if state == 0:
                    print('Inspecting installed scrolls')
                elif state == 1:
                    print('Proofreading: %s' % scroll)
                elif state == 2:
                    self.updateadd.add(scroll[:(scroll + '=').find('=')])
                elif state == 3:
                    print('Resolving conflicts')
                elif state == 4:
                    if scroll in self.dep_add:
                        self.dep_add[scroll] += args[0]
                    else:
                        self.dep_add[scroll] = args[0]
                elif state == 5:
                    if scroll in self.replace_remove:
                        self.replace_remove[scroll] += args[0]
                    else:
                        self.replace_remove[scroll] = args[0]
                elif state == 6:
                    fresh_installs, reinstalls, update, downgrading, skipping = args
                    for scrl in skipping:
                        print('Skipping %s' % scrl)
                    for scrl in fresh_installs:
                        print('Installing %s' % scrl)
                    for scrl in reinstalls:
                        print('Reinstalling %s' % scrl)
                    for scrl in update:
                        if scrl[:scrl.find('=')] not in self.update_add:
                            print('Explicitly updating %s' % scrl)
                    for scrl in update:
                        if scrl[:scrl.find('=')] in self.updat_eadd:
                            print('Updating %s' % scrl)
                    for dep in self.dep_add:
                        print('Adding %s, required by: %s' % (dep, ', '.join(self.dep_add[dep])))
                    for replacee in self.replace_remove:
                        print('Replacing %s with %s' % (replacee, ', '.join(self.replace_remove[replacee])))
                    for scrl in downgrading:
                        print('Downgrading %s' % scrl)
                    while True:
                        print('\033[01mContinue? (y/n)\033[00m')
                        answer = input().lower()
                        if answer.startswith('y') or answer.startswith('n'):
                            return answer.startswith('y')
                elif state == 7:
                    print('Inspecting scroll repository for providers')
                elif state == 8:
                    print('\033[01mSelect provider for virtual pony: %s\033[00m' % scroll)
                    i = 0
                    for prov in args[0]:
                        i += 1
                        print('%i: %s' % (i, prov))
                    print('> ', end='')
                    sel = input()
                    try:
                        sel = int(sel)
                        if 1 <= sel <= len(args):
                            return args[0][sel - 1]
                    except:
                        pass
                    return None
                elif state == 9:
                    print('There are sone scrolls that require pony interaction to be build:')
                    for scroll in args[0]:
                        print('    %s' % scroll)
                    allowed = args[1]
                    print('\033[01mWhen do you want to build scroll that require interaction:\033[00m')
                    if (allowed & (1 << 0)) != 0:
                        print('    w - Whenever, I will not leave my precious magic box')
                    if (allowed & (1 << 1)) != 0:
                        print('    e - Before all other scrolls')
                    if (allowed & (1 << 2)) != 0:
                        print('    E - Before all other scrolls, and download others\' sources afterwards')
                    if (allowed & (1 << 3)) != 0:
                        print('    l - After all other scrolls')
                    print('    a - Abort!')
                    while True:
                        when = input()
                        if (allowed & (1 << 0)) != 0:
                            if when == 'w' or when == 'W':
                                return 0
                        if (allowed & (1 << 1)) != 0:
                            if when == 'e':
                                return 1
                        if (allowed & (1 << 2)) != 0:
                            if when == 'E':
                                return 2
                        if (allowed & (1 << 3)) != 0:
                            if when == 'l' or when == 'L':
                                return 3
                        if when == 'a':
                            return None
                        print('\033[01mInvalid option!\033[00m')
                else:
                    if scroll not in self.scrls[state - 10][1]:
                        self.scrls[state - 10][0] += 1
                        self.scrls[state - 10][1][scroll] = self.scrls[state - 10][0]
                    (scrli, scrln) = (self.scrls[state - 10][1][scroll], self.scrls[state - 10][0])
                    if scrli != scrln:
                        if state != 12:
                            print('\033[%iAm', scrln - scrli)
                    if state == 10:
                        (source, progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Downloading %s: %s' % (bar, scrli, scrln, scroll, source))
                    elif state == 11:
                        (progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Verifing %s' % (bar, scrli, scrln, scroll))
                    elif state == 12:
                        print('(%i/%i) Compiling %s' % (scrli + 1, scrln, scroll))
                    elif state == 13:
                        (progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Checking file conflicts for %s' % (bar, scrli, scrln, scroll))
                    elif state == 14:
                        (progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Installing %s' % (bar, scrli, scrln, scroll))
                    if scrli != scrln:
                        if state != 12:
                            print('\033[%iBm', scrln - (scrli + 1))
                return None
                
        return LibSpike.write(Agg(), scrolls, root, private, explicitness, nodep, force)
    
    
    def update(self, root = '/', ignores = [], private = False):
        '''
        Update installed ponies
        
        @param   root:str           Mounted filesystem to which to perform installation
        @param   ignores:list<str>  Ponies not to update
        @param   private:bool       Whether to update user private packages
        @return  :byte              Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str?, int, [*])→(void|bool|str|int?)
                Feed a scroll (`None` only at state 0, 3, 6, 7 and 9) and a state (can be looped) during the process of a scroll.
                The states are: 0 - inspecting installed scrolls
                                1 - proofreading
                                2 - scroll added because of being updated
                                3 - resolving conflicts
                                4 - scroll added because of dependency. Additional parameters: requirers:list<str>
                                5 - scroll removed because due to being replaced. Additional parameters: replacer:str
                                6 - verify installation. Additional parameters: fresh_installs:list<str>, reinstalls:list<str>, update:list<str>, downgrading:list<str>, skipping:list<str>
                                                         Return: accepted:bool
                                7 - inspecting non-install scrolls for providers
                                8 - select provider pony. Additional parameters: options:list<str>
                                                          Return: select provider:str? `None` if aborted
                                9 - select when to build ponies which require interaction. Additional parameters: interactive:list<str>, allowed:int
                                                                                           Return: when:excl-flag? `None` if aborted
                               10 - fetching source. Additional parameters: source:str, progress state:int, progress end:int
                               11 - verifying source. Additional parameters: progress state:int, progress end:int
                               12 - compiling
                               13 - file conflict check: Additional parameters: progress state:int, progress end:int
                               14 - installing files: Additional parameters: progress state:int, progress end:int
                when:excl-flag values: 0 - Build whenever
                                       1 - Build early
                                       2 - Build early and fetch separately
                                       3 - Build late
                allowed:int values: The union of all `1 << when` with allowed `when`
            '''
            def __init__(self):
                self.update_add = set()
                self.dep_add = {}
                self.replace_remove = {}
                self.scrls = []
                for i in range(6):
                    self.scrls.append([0, {}])
                self.scrls[0] = self.scrls[1]
            def __call__(self, scroll, state, *args):
                if type(self) == Spike:
                    if scroll.equals('rarity'):
                        scroll = scroll + '♥'
                    elif scroll.startswith('rarity='):
                        scroll = scroll.replace('=', '♥=')
                if state == 0:
                    print('Inspecting installed scrolls')
                elif state == 1:
                    print('Proofreading: %s' % scroll)
                elif state == 2:
                    self.update_add.add(scroll[:(scroll + '=').find('=')])
                elif state == 3:
                    print('Resolving conflicts')
                elif state == 4:
                    if scroll in self.dep_add:
                        self.dep_add[scroll] += args[0]
                    else:
                        self.dep_add[scroll] = args[0]
                elif state == 5:
                    if scroll in self.replace_remove:
                        self.replace_remove[scroll] += args[0]
                    else:
                        self.replace_remove[scroll] = args[0]
                elif state == 6:
                    fresh_installs, reinstalls, update, downgrading, skipping = args
                    for scrl in skipping:
                        print('Skipping %s' % scrl)
                    for scrl in fresh_installs:
                        print('Installing %s' % scrl)
                    for scrl in reinstalls:
                        print('Reinstalling %s' % scrl)
                    for scrl in update:
                        print('Updating %s' % scrl)
                    for dep in self.dep_add:
                        print('Adding %s, required by: %s' % (dep, ', '.join(self.dep_add[dep])))
                    for replacee in self.replace_remove:
                        print('Replacing %s with %s' % (replacee, ', '.join(self.replace_remove[replacee])))
                    for scrl in downgrading:
                        print('Downgrading %s' % scrl)
                    while True:
                        print('\033[01mContinue? (y/n)\033[00m')
                        answer = input().lower()
                        if answer.startswith('y') or answer.startswith('n'):
                            return answer.startswith('y')
                elif state == 7:
                    print('Inspecting scroll repository for providers')
                elif state == 8:
                    print('\033[01mSelect provider for virtual pony: %s\033[00m' % scroll)
                    i = 0
                    for prov in args[0]:
                        i += 1
                        print('%i: %s' % (i, prov))
                    print('> ', end='')
                    sel = input()
                    try:
                        sel = int(sel)
                        if 1 <= sel <= len(args):
                            return args[0][sel - 1]
                    except:
                        pass
                    return None
                elif state == 9:
                    print('There are sone scrolls that require pony interaction to be build:')
                    for scroll in args[0]:
                        print('    %s' % scroll)
                    allowed = args[1]
                    print('\033[01mWhen do you want to build scroll that require interaction:\033[00m')
                    if (allowed & (1 << 0)) != 0:
                        print('    w - Whenever, I will not leave my precious magic box')
                    if (allowed & (1 << 1)) != 0:
                        print('    e - Before all other scrolls')
                    if (allowed & (1 << 2)) != 0:
                        print('    E - Before all other scrolls, and download others\' sources afterwards')
                    if (allowed & (1 << 3)) != 0:
                        print('    l - After all other scrolls')
                    print('    a - Abort!')
                    while True:
                        when = input()
                        if (allowed & (1 << 0)) != 0:
                            if when == 'w' or when == 'W':
                                return 0
                        if (allowed & (1 << 1)) != 0:
                            if when == 'e':
                                return 1
                        if (allowed & (1 << 2)) != 0:
                            if when == 'E':
                                return 2
                        if (allowed & (1 << 3)) != 0:
                            if when == 'l' or when == 'L':
                                return 3
                        if when == 'a':
                            return None
                        print('\033[01mInvalid option!\033[00m')
                else:
                    if scroll not in self.scrls[state - 10][1]:
                        self.scrls[state - 10][0] += 1
                        self.scrls[state - 10][1][scroll] = self.scrls[state - 10][0]
                    (scrli, scrln) = (self.scrls[state - 10][1][scroll], self.scrls[state - 10][0])
                    if scrli != scrln:
                        if state != 12:
                            print('\033[%iAm', scrln - scrli)
                    if state == 10:
                        (source, progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Downloading %s: %s' % (bar, scrli, scrln, scroll, source))
                    elif state == 11:
                        (progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Verifing %s' % (bar, scrli, scrln, scroll))
                    elif state == 12:
                        print('(%i/%i) Compiling %s' % (scrli + 1, scrln, scroll))
                    elif state == 13:
                        (progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Checking file conflicts for %s' % (bar, scrli, scrln, scroll))
                    elif state == 14:
                        (progress, end) = args
                        bar = '[\033[01;3%im%s\033[00m]'
                        bar %= (2, 'DONE') if progress == end else (3, '%2.1f' % (progress / end))
                        print('[%s] (%i/%i) Installing %s' % (bar, scrli, scrln, scroll))
                    if scrli != scrln:
                        if state != 12:
                            print('\033[%iBm', scrln - (scrli + 1))
                return None
        
        return LibSpike.update(Agg(), root, ignore)
    
    
    def erase(self, ponies, root = '/', private = False):
        '''
        Uninstall ponies
        
        @param   ponies:list<str>  Ponies to uninstall
        @param   root:str          Mounted filesystem from which to perform uninstallation
        @param   private:bool      Whether to uninstall user private ponies rather than user shared ponies
        @return  :byte             Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str, int, int)→void
                Feed a scroll, removal progress state and removal progress end state, continuously during the progress,
                this begins by feeding the state 0 when a scroll is cleared for removal, when all is enqueued the removal begins.
            '''
            def __init__(self):
                self.scrolls = {}
                self.next = 0
                self.pos = 0
            def __call__(self, scroll, progress, end):
                if type(self) == Spike:
                    if scroll.equals('rarity'):
                        scroll = scroll + '😢'
                    elif scroll.startswith('rarity='):
                        scroll = scroll.replace('=', '😢=')
                if directory not in self.dirs:
                    self.dirs[directory] = self.next
                    self.next += 1
                p = self.dirs[directory]
                if p > self.pos:
                    print('\033[%iBm', p - self.pos)
                elif p < self.pos:
                    print('\033[%iAm', self.pos - p)
                s = '\033[01;3%im%s'
                if progress == 0:
                    s %= (3, 'WAIT')
                elif progress == end:
                    s %= (2, 'DONE')
                else:
                    s %= (1, '%2.1f' % progress * 100 / end)
                print('[%s\033[00m] %s\n' % (s, directory))
                self.pos = p + 1
        
        return LibSpike.erase(Agg(), ponies, root, private)
    
    
    def ride(self, pony, private = False):
        '''
        Execute pony after best effort
        
        @param   private:bool  Whether the pony is user private rather than user shared
        @return  :byte         Exit value, see description of `mane`
        '''
        return LibSpike.ride(pony, private)
    
    
    def read_files(self, ponies):
        '''
        List files installed for ponies
        
        @param   ponies:list<str>  Installed ponies for which to list claimed files
        @return  :byte             Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str, str?, [bool])→void
                Feed the pony and the file when a file is detected,
                but `None` as the file if the pony is not installed.
                If `None` is not passed, an additional argument is
                passed: False normally, and True if the file is
                recursively claimed at detection time.
            '''
            def __init__(self):
                pass
            def __call__(self, owner, filename, entire = False):
                if filename is None:
                    printerr('%s is not installed' % owner)
                elif entire:
                    print('%s:recursive: %s' % (owner, filename))
                else:
                    print('%s: %s' % (owner, filename))
        
        return LibSpike.read_files(Agg(), ponies)
    
    
    def read_info(self, scrolls, field = None, installed = True, notinstalled = True):
        '''
        List information about scrolls
        
        @param   scrolls:list<str>     Scrolls for which to list information
        @param   field:str?|list<str>  Information field or fields to fetch, `None` for everything
        @param   installed:bool        Whether to include installed scrolls
        @param   notinstalled:bool     Whether to include not installed scrolls
        @return  :byte                 Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str, str?, str?, bool)→void
                Feed the scroll, the field name and the information in the field when a scroll's information is read,
                all (desired) fields for a scroll will come once, in an uninterrupted sequence. Additionally it is
                feed whether or not the information concerns a installed or not installed scroll. The values for a
                field is returned in an uninterrupted sequence, first the non-installed scroll, then the installed
                scroll. If a scroll is not found the field name and the value is returned as `None`. If the field
                name is not defined, the value is returned as `None`.
            '''
            def __init__(self):
                self.metaerr = set()
            def __call__(self, scroll, meta, info, isinstalled):
                if meta is None:
                    printerr('Scroll %s was not found' % scroll)
                elif info is None:
                    if meta not in self.metaerr:
                        printerr('Field %s was defined' % meta)
                        self.metaerr.add(meta)
                else:
                    if installed == notinstalled:
                        print('%s: %s: %s: %s' % (scroll, meta, 'installed' if isinstalled else 'not installed', info))
                    else:
                        print('%s: %s: %s' % (scroll, meta, info))
        
        return LibSpike.read_info(Agg(), scrolls, field, installed, notinstalled)
    
    
    def claim(self, files, pony, recursiveness = 0, private = False, force = False):
        '''
        Claim one or more files as a part of a pony
        
        @param   files:list<str>    File to claim
        @param   pony:str           The pony
        @param   recursiveness:int  0 for not recursive, 1 for recursive, 2 for recursive at detection
        @param   private:bool       Whether the pony is user private rather the user shared
        @param   force:bool         Whether to override current file claim
        @return  :byte              Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str, str)→void
                Feed a file and it's owner when a file is already claimed
            '''
            def __init__(self):
                pass
            def __call__(self, filename, owner):
                print('%s is already claimed by %s' % (filename, owner))
        
        return LibSpike.claim(Agg(), files, pony, recursiveness, private, force)
    
    
    def disclaim(self, files, pony, recursive = False, private = False):
        '''
        Disclaim one or more files as a part of a pony
        
        @param   files:list<str>    File to disclaim
        @param   pony:str           The pony
        @param   recursive:bool     Whether to disclaim directories recursively
        @param   private:bool       Whether the pony is user private rather the user shared
        @return  :byte              Exit value, see description of `mane`
        '''
        return LibSpike.disclaim(files, pony, recursive, private)
    
    
    def archive(self, archive, scrolls = False):
        '''
        Archive the current system installation state
        
        @param   archive:str   The archive file to create
        @param   scrolls:bool  Whether to only store scroll states and not installed files
        @return  :byte         Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str, int, int, int, int)→void
                Feed a scroll, scroll index, scroll count, scroll progress state and scroll progress end, continuously during the process
            '''
            def __init__(self):
                self.scrolls = {}
                self.next = 0
                self.pos = 0
            def __call__(self, scroll, scrolli, scrolln, progess, end):
                if directory not in self.dirs:
                    self.dirs[directory] = self.next
                    self.next += 1
                p = self.dirs[directory]
                if p > self.pos:
                    print('\033[%iBm', p - self.pos)
                elif p < self.pos:
                    print('\033[%iAm', self.pos - p)
                s = '\033[01;3%im%s'
                if progress == 0:
                    s %= (3, 'WAIT')
                elif progress == end:
                    s %= (2, 'DONE')
                else:
                    s %= (1, '%2.1f' % progress * 100 / end)
                print('[%s\033[00m] (%i/%i) %s\n' % (s, scrolli, scrolln, scroll))
                self.pos = p + 1
        
        return LibSpike.archive(Agg(), archive, scrolls)
    
    
    def rollback(self, archive, keep = False, skip = False, gradeness = 0):
        '''
        Roll back to an archived state
        
        @param   archive:str    Archive to roll back to
        @param   keep:bool      Keep non-archived installed ponies rather than uninstall them
        @param   skip:bool      Skip rollback of non-installed archived ponies
        @param   gradeness:int  -1 for downgrades only, 1 for upgrades only, 0 for rollback regardless of version
        @return  :byte          Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str, int, int, int, int)→void
                Feed a scroll, scroll index, scroll count, scroll progress state and scroll progress end, continuously during the process
            '''
            def __init__(self):
                self.scrolls = {}
                self.next = 0
                self.pos = 0
            def __call__(self, scroll, scrolli, scrolln, progess, end):
                if directory not in self.dirs:
                    self.dirs[directory] = self.next
                    self.next += 1
                p = self.dirs[directory]
                if p > self.pos:
                    print('\033[%iBm', p - self.pos)
                elif p < self.pos:
                    print('\033[%iAm', self.pos - p)
                s = '\033[01;3%im%s'
                if progress == 0:
                    s %= (3, 'WAIT')
                elif progress == end:
                    s %= (2, 'DONE')
                else:
                    s %= (1, '%2.1f' % progress * 100 / end)
                print('[%s\033[00m] (%i/%i) %s\n' % (s, scrolli, scrolln, scroll))
                self.pos = p + 1
        
        return LibSpike.rollback(Agg(), archive, keep, skipe, gradeness)
    
    
    def proofread(self, scrolls):
        '''
        Look for errors in a scrolls
        
        @param   scrolls:list<str>  Scrolls to proofread
        @return  :byte              Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str, int, [*])→void
                Feed a scroll, 0, scroll index:int, scroll count:int when a scroll proofreading begins
                Feed a scroll, 1, error message:str when a error is found
            '''
            def __init__(self):
                pass
            def __call__(self, scroll, err, *args):
                if err == 0:
                    index = args[0]
                    count = args[1]
                    print('(%i/%i) %s' % (index, count, scroll))
                else:
                    message = args[0]
                    print('Error: %s: %s' % (scroll, message))
        
        return LibSpike.proofread(Agg(), scrolls)
    
    
    def clean(self, private = False):
        '''
        Remove unneeded ponies that are installed as dependencies
        
        @param   private:bool  Whether to uninstall user private ponies rather than user shared ponies
        @return  :byte         Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str, int, int)→void
                Feed a scroll, removal progress state and removal progress end state, continuously during the progress,
                this begins by feeding the state 0 when a scroll is enqueued, when all is enqueued the removal begins.
            '''
            def __init__(self):
                self.scrolls = {}
                self.next = 0
                self.pos = 0
            def __call__(self, scroll, progress, end):
                if directory not in self.dirs:
                    self.dirs[directory] = self.next
                    self.next += 1
                p = self.dirs[directory]
                if p > self.pos:
                    print('\033[%iBm', p - self.pos)
                elif p < self.pos:
                    print('\033[%iAm', self.pos - p)
                s = '\033[01;3%im%s'
                if progress == 0:
                    s %= (3, 'WAIT')
                elif progress == end:
                    s %= (2, 'DONE')
                else:
                    s %= (1, '%2.1f' % progress * 100 / end)
                print('[%s\033[00m] %s\n' % (s, directory))
                self.pos = p + 1
        
        return LibSpike.clean(Agg(), private)
    
    
    def example_shot(self, scrolls, viewer, all_at_once = False):
        '''
        Display example shots for scrolls
        
        @param   scrolls:list<str>  Scrolls of which to display example shots
        @param   viewer:str         The PNG viewer to use
        @param   all_at_once:bool   Whether to display all images in a single process instance
        @return  :byte              Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str, str?)→void
                Feed a scroll and its example shot file when found, or the scroll and `None` if there is not example shot.
            '''
            def __init__(self):
                self.queue = [viewer]
            def __call__(self, scroll, shot):
                if shot is None:
                    print('%s has no example shot' % scroll)
                elif all_at_once:
                    self.queue.append(shot)
                else:
                    print(scroll)
                    Popen([viewer, shot]).communicate()
            def done(self):
                if all_at_once:
                    Popen(self.queue).communicate()
        
        exit_value = LibSpike.example_shot(Agg(), scrolls)
        if exit_value != 0:
            Agg.done()
        return exit_value
    
    def interactive(self):
        '''
        Start interactive mode with terminal graphics
        
        @return  :byte       Exit value, see description of `mane`
        '''
        if not sys.stdout.isatty:
            printerr(self.execprog + ': trying to start interative mode from a pipe')
            return 15
        # TODO interactive mode
        return 0
    
    
    def sha3sum(self, files):
        '''
        Calculate the SHA3 checksum for files to be used in scrolls
        
        @param   files:list<str>  Files for which to calculate the checksum
        @return  :byte            Exit value, see description of `mane`
        '''
        class Agg:
            '''
            aggregator:(str, str?)→void
                Feed a file and its checksum when one has been calculated.
                `None` is returned as the checksum if it is not a regular file or does not exist.
            '''
            def __init__(self):
                pass
            def __call__(self, filename, checksum):
                if checksum is None:
                    if not os.path.exists(filename):
                        printerr('%s is not exist.' % filename)
                    else:
                        printerr('%s is not a regular file.' % filename)
                else:
                    print('\033[01m%s\033[21m  %s' % (checksum, filename));
        
        return LibSpike.sha3sum(Agg(), files)
        




tty = ('TERM' in os.environ) and (os.environ['TERM'] in ('linux', 'hurd'))

if __name__ == '__main__': # sic (`applebloom main`)
    spike = Spike()
    spike.mane(sys.argv)

