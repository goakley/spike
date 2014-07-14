#!/usr/bin/env python3
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
from collections import defaultdict
import os
import re

from auxiliary.auxfunctions import *


class ScrollFinder():
    '''
    Module for libspike for finding scrolls
    '''
    @staticmethod
    def regex_match(needle, haystack):
        '''
        Tests if a pattern can be found in a text

        @param   needle:str    The pattern to search for
        @param   haystack:str  The text to search in
        @return  :bool         Whether the pattern can be found in the text
        '''
        return re.search(needle, haystack) is not None

    def __init__(self):
        self._patterns = []
        self._directories = set()

    def add_pattern(self, pattern):
        '''
        Adds a pattern that will be used to find scrolls

        Patterns take the form of 'repo/category/scroll'.  If any slashes are
        omitted, depth has highest precedence (that is, 'a/b' is
        'category/scroll', 'c' is 'scroll').  To search for, say, all scrolls
        in the 'core' repository, use 'core//'.  No more than two slashes may
        exist in a pattern.  Regex (without slashes) is permitted in the
        pattern string.

        @param   pattern:str  The pattern
        @return  :bool        Whether or not the pattern was valid (added
                              successfully)
        '''
        # break down the pattern before storing (also ensures validity)
        slashes = pattern.count('/')
        if slashes > 2:
            return False
        self._patterns.append(('/' * (2 - slashes) + pattern).split('/'))
        return True

    def add_repositories_directory(self, dir):
        '''
        Adds a directory containing repositories to the search path

        Note that the directory being added MUST contain repositories, or at
        least be structured in the same format as a repository directory (that
        is, a directory containg directories containing directories containing
        scrolls).

        @param  dir:str  The directory to add
        '''
        dir = os.path.realpath(dir)
        if not os.path.isdir(dir):
            raise NotADirectoryError('Not a directory: %s' % dir)
        self._directories.add(dir)

    def _find_match_scrolls(self, pattern, cat_path):
        scrolls = [path for path in os.listdir(cat_path)
                   if os.path.isfile(os.path.join(cat_path, path))
                   and path.endswith('.scroll')]
        return [(scroll, os.path.join(cat_path, scroll)) for scroll in scrolls
                if ScrollFinder.regex_match(pattern, scroll)]

    def _find_match_categories(self, pattern, repo_path):
        categories = [path for path in os.listdir(repo_path)
                      if os.path.isdir(os.path.join(repo_path, path))]
        return [(cat, os.path.join(repo_path, cat)) for cat in categories
                if ScrollFinder.regex_match(pattern, cat)]

    def _find_match_repositories(self, pattern, dir_path):
        repositories = [path for path in os.listdir(dir_path)
                        if os.path.isdir(os.path.join(dir_path, path))]
        return [(repo, os.path.join(dir_path, repo)) for repo in repositories
                if ScrollFinder.regex_match(pattern, repo)]

    def _find_match(self, pattern, aggregator):
        '''
        finds all scrolls matches a pattern tuple
        '''
        if not self._directories:
            return []
        result = []
        for dir in self._directories:
            repos = self._find_match_repositories(pattern[0], dir)
            for (repo, repopath) in repos:
                cats = self._find_match_categories(pattern[1], repopath)
                for (cat, catpath) in cats:
                    scrolls = self._find_match_scrolls(pattern[2], catpath)
                    for (scroll, scrollpath) in scrolls:
                        result.append((repo, cat, scroll, scrollpath))
                        if aggregator:
                            aggregator(scrollpath)
        return result

    def find_matches(self, aggregator=None):
        '''
        Finds scrolls in the stored directories matching the stored patterns

        @param  aggregator:(str)→void      Function invoked with a scroll path
                                           when matched
        @return  :iter<(str,str,str,str)>  The (repo, cat, scroll, path)
                                           combination for each matching scroll
        '''
        if not self._patterns:
            return self._find_match(('', '', ''), aggregator)
        return set(sum([self._find_match(p, aggregator)
                        for p in self._patterns], []))
