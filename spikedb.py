#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os


def fetch(db, values):
    return []

def make(db, pairs):
    pass


if len(sys.args) == 1:
    data = []
    try:
        data.append(input())
    except:
        pass
    make('testdb', [(comb[:comb.find(' ')], comb[comb.find(' ') + 1:]) for comb in data])
else:
    for pair in fetch('testdb', sort([os.path.realpath(f) for f in sys.args[1:]])):
        print('%s --> %s' % pair)

