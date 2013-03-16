#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

INITIALS_LEN = 4

# TODO insert and remove is needed
# TODO paths should be db separated into groups by the binary logarithm of the length of their paths


# keep in mind that it we sould not depend on sorted() using a stabil sort


def binsearch(list, item, min, max):
    mid = 0
    while min <= max:
        mid = (min + max) >> 1
        elem = list[mid]
        if elem == item:
            return mid
        elif elem > item:
            max = mid - 1
        else:
            mid += 1
            min = mid
    return ~mid


def multibinsearch(list, items):
    rc = []
    count = len(items)
    if count > 0:
        minomax = [(0, count - 1, 0, len(list) - 1)]
        while len(minomax) > 0:
            (min, max, lmin, lmax) = minomax.pop()
            while max != min:
                (lastmax, lastlmax) = (max, lmax)
                max = min + ((max - min) >> 1)
                lmax = binsearch(list, items[max], lmin, lmax)
                rc.append((max, lmax))
                if lmax < 0:
                    lmax = ~lmax
                minomax.append((max + 1, lastmax, lmax + 1, lastlmax))
        max = count - 1
        lmax = binsearch(list, items[max], lmin, lmax)
        rc.append((max, lmax))
    return rc



def fetch(db, maxlen, values):
    buckets = {}
    for path in sorted(values):
        pos = 0
        initials = ''
        while '/' in path[pos : -1]:
            pos = path.find('/') + 1
            initials += path[pos]
        while len(initials) < INITIALS_LEN:
            pos += 1
            if pos == len(initials):
                break
            initials += path[pos]
        if len(initials) > INITIALS_LEN:
            initials += initials[:INITIALS_LEN]
        initials = [(ord(c) & 15) for c in initials]
        ivalue = 0
        for initial in initials:
            ivalue = (ivalue << 4) | ivalue
        if ivalue not in buckets:
            buckets[ivalue] = []
        buckets[ivalue].append(value)
    rc = []
    with open(db, 'rb') as file:
        offset = 0
        position = 0
        amount = 0
        masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
        masterseek = file.read(masterseeklen)
        for initials in sorted(buckets.keys()):
            if position >= initials:
                position = 0
                offset = 0
                amount = 0
            while position <= initials:
                offset += amount
                amount = [int(b) for b in list(masterseek[3 * position : 3 * (position + 1)])]
                amount = (amount[0] << 16) + (amount[1] << 8) + amount[2]
                position += 1
            fileoffset = masterseeklen + offset * (maxlen + 3)
            bucket = buckets[initials]
            start = findInFile(bucket[0], maxlen, file, fileoffset, amount, maxlen + 3)
            end = findInFile(bucket[-1], maxlen, file, fileoffset, amount, maxlen + 3)
            start = (start - fileoffset) / (maxlen + 3)
            end = (end - fileoffset) / (maxlen + 3)
            # TODO
    return rc

def findInFile(word, length, file, offset, count, size):
    word = word + '\0' * (length - len(word.encode('utf-8')))
    word = word.encode('utf-8')
    # TODO
    return 0


def make(db, maxlen, pairs):
    buckets = {}
    for pair in sorted(pairs, key = lambda x : x[0]):
        pos = 0
        initials = ''
        (path, package) = pair
        while '/' in path[pos : -1]:
            pos = path.find('/') + 1
            initials += path[pos]
        while len(initials) < INITIALS_LEN:
            pos += 1
            if pos == len(initials):
                break
            initials += path[pos]
        if len(initials) > INITIALS_LEN:
            initials += initials[:INITIALS_LEN]
        initials = [(ord(c) & 15) for c in initials]
        ivalue = 0
        for initial in initials:
            ivalue = (ivalue << 4) | ivalue
        if ivalue not in buckets:
            buckets[ivalue] = []
        buckets[ivalue].append(pair)
    counts = []
    with open(db, 'wb') as file:
        wbuf = [0] * (1 << (INITIALS_LEN << 2))
        for i in range(3):
            file.write(zbuf)
        wbuf = None
        for initials in sorted(buckets.keys()):
            bucket = buckets[initials]
            for pair in bucket:
                (filepath, package) = pair
                filepath = filepath + '\0' * (maxlen - len(filepath.encode('utf8')))
                filepath = filepath.encode('utf8')
                package = bytes([b & 255 for b in [package >> 16, package >> 8, package]])
                file.write(filepath)
                file.write(package)
            counts.append((initials, len(bucket)))
        file.flush()
        for (initials, count) in counts:
            file.seek(offset = 3 * initials, whence = 0) # 0 means from the start of the stream
            wbuf = bytes([b & 255 for b in [count >> 16, count >> 8, count]])
            file.write(wbuf)
        file.flush()



if len(sys.args) == 1:
    data = []
    try:
        data.append(input())
    except:
        pass
    make('testdb', 50, [(comb[comb.find(' ') + 1:], hash(comb[:comb.find(' ')]) & 0xFFFFFF) for comb in data])
else:
    for pair in fetch('testdb', 50, sorted([os.path.realpath(f)[:50] for f in sys.args[1:]])):
        print('%s --> %s' % pair)
