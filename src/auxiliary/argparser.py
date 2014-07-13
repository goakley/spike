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
import argparse
import re
import sys

from auxiliary.printhacks import *


def _build_option_help(opt, colour):
    '''
    turns an option tuple into (flag output, help output)
    '''
    FLAGTEXT = '\033[2m{shortflag}\033[22m  \033[{colour};1m{longflag} ' \
        '\033[4m{metavar}\033[24m'

    flags = sorted(list(opt[0]), reverse=True)
    nargs = opt[1]['nargs'] if 'nargs' in opt[1] \
        else 0 if 'action' in opt[1] and opt[1]['action'].startswith('store_') \
        else 1

    flagtext = FLAGTEXT.format(
        shortflag=flags[0] if len(flags[0]) == 2 else '  ',
        colour=colour,
        longflag=flags[-1],
        metavar=('' if nargs == 0 else opt[1]['metavar']) +
        ('...' if nargs == '+' else '')
    )
    helptext = opt[1]['help'] if 'help' in opt[1] else '[No help]'

    return (flagtext, helptext)


def _group_by_exclusive(opts, exclusives):
    '''
    groups a list of flags into a list of list of opts based on exclusivity
    each sublist contains mutually exclusive flags
    '''
    eligibles = [[opt for opt in opts if opt in exclusive]
                 for exclusive in exclusives]
    remainder = [[opt] for opt in opts
                 if not any([opt in eligible for eligible in eligibles])]
    remainder.extend(filter(list, eligibles))
    return remainder


def _build_command_help(cmd, colour, exclusives):
    '''
    turns a command tuple into (flag output, help output, slave output)
    slave output will be None if there are no slaves
    '''
    option_result = _build_option_help(cmd, colour)
    if not cmd[1]['options']:
        return (option_result[0], option_result[1], None)

    optgroups = _group_by_exclusive(cmd[1]['options'], exclusives)
    opttext = '\033[{}mflags: '.format(colour)
    opttext += ' '.join(['[' + ' | '.join(grp) + ']' for grp in optgroups])

    return (option_result[0], option_result[1], opttext)


class ArgumentCommandParser(argparse.ArgumentParser):
    '''
    The ArgumentCommandParser uses a command-based idiom for parsing arguments

    Each ArgumentCommandParser must contain at least one command, added with
    `add_command`, which takes similar arguments as `add_argument`.

    This parser will pass all trailing argument that are not flags to the
    command, making `parse_known_args` meaningless and thus not implemented.
    '''

    def __init__(self, *args, **kwargs):
        self._commands = [(
            set(['-h', '--help']),
            {'options': [],
             'nargs': 0,
             'help': 'Print this help'}
        )]
        self._options = []
        self._exclusives = []
        self._multis = set()
        if 'tty' in kwargs:
            del kwargs['tty']
        self._tty = kwargs.get('tty')
        super().__init__(*args, **kwargs)
        # set _options again afterwards to remove the --help flag
        self._options = []

    def add_argument(self, *args, **kwargs):
        super().add_argument(*args, **kwargs)
        self._options.append((set(args), kwargs))
        if kwargs.get('nargs') == '+':
            self._multis.update([re.sub(r'^-+', '', arg).replace('-', '_')
                                 for arg in args])

    def add_command(self, shortflag, longflag, **kwargs):
        '''
        Adds a top-level command to the parser

        This method is incredibly similar to `add_argument`, with a few key
        differences.  First, two arguments must be passed, the short and long
        flags for the command.  The short flag may be `None`.  Second, a new
        `options` argument is added, taking in all the flags that may be used
        with this command.  Third, the `action` argument is removed and the
        purpose of the `nargs` argument is modified; passing an `nargs` of 0
        is valid for this method, and implies that the command takes no
        arguments.

        Commands are mutually exclusive.
        This method must be called at least once.
        Exactly one top-level command must always be provided during parsing.

        @param options:list<str> Flags that may be used with this command
        '''
        if 'action' in kwargs:
            raise TypeError('add_command() got an unexpected keyword argument '
                            '\'action\'')
        args = [longflag] if shortflag is None else [shortflag, longflag]

        kwargs.setdefault('options', [])
        options = kwargs['options']
        nargs = kwargs.get('nargs')
        metavar = kwargs.get('metavar')

        del kwargs['options']
        if nargs is not None:
            del kwargs['nargs']
        if metavar is not None:
            del kwargs['metavar']
        kwargs['action'] = 'store_true'
        super().add_argument(*args, **kwargs)

        kwargs['nargs'] = nargs
        kwargs['options'] = options
        kwargs['metavar'] = metavar

        self._commands.append((set(args), kwargs))

    def add_exclusivity(self, *args):
        '''
        Treats all given argument flags as exclusive to each other

        Note that every flag MUST have been added to the parser already
        through `add_argument`.

        @param *args:list<str> Flags that are mutually exclusive
        '''
        argset = set(args)
        for arg in args:
            if not [arg in opt[0] for opt in self._options]:
                raise argparse.ArgumentError(arg, 'does not exist')
        self._exclusives.append(set(sum(
            [list(opt[0]) for opt in self._options for arg in argset
             if arg in opt[0]], []
        )))

    def parse_args(self, args=None, namespace=None):
        '''
        Behaves similar to the parent `parse_args`

        The only difference in this `parse_args` is that the command itself
        will be passed out under the 'COMMAND' attribute as the long flag with
        no dashes(so '--option-made' will be 'option_made') and all the
        remaining arguments will be passed out in the namespace under the
        attribute 'ARGS' (i.e. `namespace.ARG` will give the args to the
        command)
        '''
        argset = set((args or sys.argv)[1:])

        # ensure at least one command exists
        commands = [cmds for cmds in self._commands for arg in args
                    if arg in cmds[0]]
        if not commands:
            self.error('at least one command is required')
        if len(commands) > 1:
            self.error('only one command may be used')
        command = commands[0]

        # ensure no exclusive options occur together
        for exclusive in self._exclusives:
            if len([arg for arg in argset
                    if any([arg in elem for elem in exclusive])]) > 1:
                self.error('mutually exclusive options used')

        # ensure no foreign flags are set
        fulloptions = sum([list(option[0]) for opt in command[1]['options']
                           for option in self._options if opt in option[0]],
                          [])
        present = [arg for arg in argset if arg in fulloptions]
        conflicting = [flag for flag in present if flag not in fulloptions]
        if conflicting:
            raise argparse.ArgumentError(None, '%s '
                                         'has no effect in this command' %
                                         conflicting[0])

        # check for unknown flags
        unknown = [arg for arg in argset
                   if arg[0] == '-'
                   and arg not in command[0]
                   and not any([arg in option[0] for option in self._options])]
        if unknown:
            raise argparse.ArgumentError(None, '%s is not a recognized flag' %
                                         unknown[0])

        # store the command args in '_' after verifying correctness
        namespace, remainder = super().parse_known_args(args, namespace)
        # comma-separate the multi-args if needed
        for multi in self._multis:
            if getattr(namespace, multi, None):
                setattr(namespace, multi,
                        sum([arg.split(',')
                             for arg in getattr(namespace, multi)], []))
        remainder = remainder[1:]
        nargs = command[1]['nargs']
        if nargs is None:
            if len(remainder) != 1:
                self.error('expected 1 argument (got %s)' % len(remainder))
            setattr(namespace, '_', remainder[0])
        if type(nargs) == int:
            if len(remainder) != nargs:
                self.error('expected %s arguments (got %s)' %
                           (nargs, len(remainder)))
            setattr(namespace, '_', remainder)
        elif command[1]['nargs'] == '+':
            if len(remainder) < 1:
                self.error('expected one or more arguments (got %s)'
                           % len(remainder))
            # the following line allows for splitting on commas
            sum([arg.split(',') for arg in remainder], [])
            setattr(namespace, 'ARGS', remainder)
        else:
            raise NotImplementedError()

        # add the COMMAND attribute
        setattr(namespace, 'COMMAND',
                sorted(list(command[0]))[0][2:].replace('-', '_'))

        return namespace

    def parse_known_args(self, *args, **kwargs):
        '''
        Not Implemented
        '''
        raise NotImplementedError()

    def print_help(self, file=sys.stdout):
        output = []

        output.append('\033[1m%s\033[21m %s %s\n\n' %
                      (self.prog, '-' if self._tty else '—', self.description))
        output.append('\033[1mUSAGE:\033[21m\t%s\n\n' % self.usage)
        output.append('\033[1mSYNOPSIS:\033[21m\n')

        primarycolour = True
        indent = 8 + max([len(_build_option_help(cmd, 0)[0])
                          for cmd in (self._commands + self._options)])

        output.append('\033[1m  COMMANDS:\033[21m\n')
        for cmd in self._commands:
            primarycolour = not primarycolour
            flagtext, helptext, slavetext = _build_command_help(
                cmd, 34 if primarycolour else 36, self._exclusives
            )
            output.append(('    ' + flagtext).ljust(indent) +
                          helptext + '\033[00m\n')
            if slavetext is not None:
                output.append(''.ljust(indent - 25) + slavetext + '\033[00m\n')
        output.append('\n')

        output.append('\033[1m  FLAGS:\033[21m\n')
        for opt in self._options:
            primarycolour = not primarycolour
            flagtext, helptext = _build_option_help(
                opt, 34 if primarycolour else 36
            )
            output.append(('    ' + flagtext).ljust(indent) +
                          helptext + '\033[00m\n')
        output.append('\n')

        # ensure proper utf-8 output
        file.buffer.write(''.join(output).encode('utf-8'))
