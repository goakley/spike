#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Module for libspike for bootstrapping

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
import os

from library.gitcord import *


class Bootstrapper():
    '''
    Bootstraps some directories using an aggregator
    '''

    def __init__(self, aggregator):
        '''
        @param  aggregator:(dir:, int=0)→void  Feed the directory if it gets
                                               queued
        '''
        self._aggregator = aggregator
        self._repositories = set()
        self._update = []

    def queue(self, dir):
        '''
        Queue a directory for bootstrapping if it is not frozen

        @param  dir:str  The directory
        '''
        dir = os.path.realpath(dir)
        if not os.path.isdir(dir):
            raise NotADirectoryError('Not a directory: %s' % dir)
        self._repositories.add(os.path.realpath(dir))
        if not os.path.exists(os.path.join(dir, '.git/frozen.spike')):
            self._update.append(dir)
            self._aggregator(dir, 0)

    def queue_repository(self, dir):
        '''
        Queue a repository's directory for bootstrapping that are not frozen

        @param  dir:str  The directory of the candidate repository
        '''
        dir = os.path.realpath(dir)
        if not os.path.isdir(dir):
            raise NotADirectoryError('Not a directory: %s' % dir)
        for repo in os.listdir(dir):
            if repo == '.git':
                continue
            repo = os.path.join(dir, repo)
            if os.path.isdir(repo) and repo not in self._repositories:
                self.queue(repo)

    def update(self, verify_signatures):
        '''
        @param   verify_signatures:bool  Whether to verify signatures
        @return  :list<str>              All the directories that failed to
                                         update
        '''
        failures = []
        for directory in self._update:
            self._aggregator(directory, 1)
            if Gitcord(directory).update_branch(verify_signatures):
                self._aggregator(directory, 2)
            else:
                self._aggregator(directory, 3)
                failures.append(directory)
        return failures
