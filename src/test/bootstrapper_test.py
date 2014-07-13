#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

import os
import os.path
import tempfile

import sys
sys.path.append("..")
from scales.bootstrapper import Bootstrapper


class Agg:
    def __init__(self):
        self.rset = set()

    def __call__(self, directory, state):
        if state == 0:
            self.rset.add(directory)


class TestBootstrapper(unittest.TestCase):

    def setUp(self):
        self.agg = Agg()
        self.bootstrapper = Bootstrapper(self.agg)
        # temporary directory automatically cleans itself
        self.tld = tempfile.TemporaryDirectory()

    def test_queue(self):
        paths = [
            os.path.join(self.tld.name, 'a'),
            os.path.join(self.tld.name, 'b'),
        ]
        for path in paths:
            os.mkdir(path)
            self.bootstrapper.queue(path)

        # ensure nonexistant directories can't get added
        try:
            self.bootstrapper.queue('z')
            self.fail()
        except NotADirectoryError:
            pass

        self.assertEqual(self.agg.rset, set(paths))

    def test_queue_repository(self):
        paths = [
            os.path.join(self.tld.name, 'a'),
            os.path.join(self.tld.name, 'b'),
        ]
        for path in paths:
            os.mkdir(path)

        # ensure '.git' doesn't get added
        os.mkdir(os.path.join(self.tld.name, '.git'))
        # ensure regular files don't get added
        open(os.path.join(self.tld.name, 'z'), 'a').close()
        open(os.path.join(self.tld.name, 'y'), 'a').close()

        self.bootstrapper.queue_repository(self.tld.name)
        self.assertEqual(self.agg.rset, set(paths))


if __name__ == '__main__':
    unittest.main()
