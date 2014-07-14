#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

import os
import os.path
import tempfile

import sys
sys.path.append("..")
from scales.scrollfinder import ScrollFinder


STRUCTURE = {
    'core': {
        'linux': [
            'linux.scroll',
            'README',
            'dolphins.txt',
        ],
        'ed': [
            'ed.scroll',
            'LICENSE',
            'ed.1p.gz',
        ],
    },
    'candy': {},
    'game': {
        'rogue': [
            'rogue',
            'rogue.scroll',
            'rogue.6.gz',
        ],
        'tetravex': [
            '8172eeff',
            'COREDUMP'
        ],
    },
}

ALL = set([
    'core/linux/linux.scroll',
    'core/ed/ed.scroll',
    'game/rogue/rogue.scroll'
])

CORE = set([
    'core/linux/linux.scroll',
    'core/ed/ed.scroll',
])

ED = set(['core/ed/ed.scroll'])


class Agg:
    def __init__(self):
        self.sset = set()

    def __call__(self, scrollpath):
        self.sset.add(scrollpath)


class TestScrollFinder(unittest.TestCase):

    def setUp(self):
        self.agg = Agg()
        self.scrollfinder = ScrollFinder()
        # temporary directory automatically cleans itself
        self.tld = tempfile.TemporaryDirectory()
        # fill the directory with a sample repos
        open(os.path.join(self.tld.name, 'junkfile.dat'), 'a').close()
        for repo, cats in STRUCTURE.items():
            os.mkdir(os.path.join(self.tld.name, repo))
            for cat, files in cats.items():
                path = os.path.join(self.tld.name, repo, cat)
                os.mkdir(path)
                for file in files:
                    open(os.path.join(path, file), 'a').close()
        # ...and add it
        self.scrollfinder.add_repositories_directory(self.tld.name)

    def test_find_all(self):
        orig_result = self.scrollfinder.find_matches(self.agg)
        # check aggregator calls
        result = [val[3] for val in orig_result]
        self.assertEqual(set(result), self.agg.sset)
        # check correct result
        result = [val[len(self.tld.name)+1:] for val in result]
        self.assertEqual(set(result), ALL)
        # check sane result
        self.assertEqual(set(result),
                         set([os.path.join(val[0], val[1], val[2])
                              for val in orig_result]))

    def test_find_core(self):
        self.assertFalse(self.scrollfinder.add_pattern('core///'))
        self.assertTrue(self.scrollfinder.add_pattern('core//'))
        orig_result = self.scrollfinder.find_matches(self.agg)
        # check aggregator calls
        result = [val[3] for val in orig_result]
        self.assertEqual(set(result), self.agg.sset)
        # check correct result
        result = [val[len(self.tld.name)+1:] for val in result]
        self.assertEqual(set(result), CORE)
        # check sane result
        self.assertEqual(set(result),
                         set([os.path.join(val[0], val[1], val[2])
                              for val in orig_result]))

    def test_find_ed_path(self):
        self.assertFalse(self.scrollfinder.add_pattern('//ed/'))
        self.assertTrue(self.scrollfinder.add_pattern('/ed'))
        orig_result = self.scrollfinder.find_matches(self.agg)
        # check aggregator calls
        result = [val[3] for val in orig_result]
        self.assertEqual(set(result), self.agg.sset)
        # check correct result
        result = [val[len(self.tld.name)+1:] for val in result]
        self.assertEqual(set(result), ED)
        # check sane result
        self.assertEqual(set(result),
                         set([os.path.join(val[0], val[1], val[2])
                              for val in orig_result]))

    def test_find_ed_file(self):
        self.assertFalse(self.scrollfinder.add_pattern('/////ed'))
        self.assertTrue(self.scrollfinder.add_pattern('ed'))
        orig_result = self.scrollfinder.find_matches(self.agg)
        # check aggregator calls
        result = [val[3] for val in orig_result]
        self.assertEqual(set(result), self.agg.sset)
        # check correct result
        result = [val[len(self.tld.name)+1:] for val in result]
        self.assertEqual(set(result), ED)
        # check sane result
        self.assertEqual(set(result),
                         set([os.path.join(val[0], val[1], val[2])
                              for val in orig_result]))


if __name__ == '__main__':
    unittest.main()
