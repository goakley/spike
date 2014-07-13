#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

import sys
sys.path.append("..")
from auxiliary.argparser import ArgumentCommandParser


class TestParser(unittest.TestCase):

    def setUp(self):
        self.parser = ArgumentCommandParser()
        self.parser.add_command('-C', '--celestia', nargs='+', metavar='attrs',
                                options=['--cadence'])
        self.parser.add_command('-L', '--luna', nargs=1, metavar='things',
                                options=['--bat-pony'])
        self.parser.add_argument('--cadence', action='store_true')
        self.parser.add_argument('--bat-pony', metavar='ponyname')

    def test_required_command(self):
        try:
            self.parser.parse_args([])
        except:
            return
        self.fail()

    def test_mutual_exclusion(self):
        try:
            self.parser.parse_args(['run', '-C', '-L'])
        except:
            return
        self.fail()

    def test_unknown_flags(self):
        try:
            self.parser.parse_args(['run', '-C', '-lyra'])
        except:
            return
        self.fail()

    def test_relevant_flags(self):
        try:
            self.parser.parse_args(['run', '-C', '--bat-pony', 'nightwing'])
        except:
            return
        self.fail()

    def test_consuming_args(self):
        parse = self.parser.parse_args(
            ['run', '--celestia', 'wings', 'ivory', '--cadence', 'horn']
        )
        self.assertEqual(set(parse.ARGS), set(['wings', 'ivory', 'horn']))


class TestCommands(unittest.TestCase):

    def test_action_failure(self):
        parser = ArgumentCommandParser()
        try:
            parser.add_command('-A', '--active', action='store_true')
        except TypeError:
            return
        self.fail()


if __name__ == '__main__':
    unittest.main()
