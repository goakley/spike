#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

INITIALS_LEN = 4

# TODO insert is needed
# TODO paths should be db separated into groups by the binary logarithm of the length of their paths

# keep in mind that it we sould not depend on sorted() and .sort() using a stabil sort


def unique(sorted):
    '''
    Duplicate a sorted list and remove all duplicates
    
    @param   sorted:list<¿E?>  A sorted list, without leading `None`:s, more precisely, all equals elements must be grouped
    @return  :list<¿E?>        `sorted` with all duplicates removed, for example: aaabbc → abc
    '''
    rc = []
    last = None
    for element in sorted:
        if element != last:
            last = element
            rc.append(element)
    return rc


def binsearch(list, item, min, max):
    '''
    Find the index of an item in a list, with time complexity 𝓞(log n) and memory complexity 𝓞(1)
    
    @param   list:[int]→¿E?  Sorted list in which to search
    @param   item:¿E?        Item for which to search
    @param   min:int         The index of the first element in `list` for which to serach
    @param   max:int         The index of the last element (inclusive) in `list` for which to serach
    @return  :int            The index of `item` in `list`, if missing `~x` is returned were `x` is the position it would have if it existed
    '''
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


def __blocksize(file):
    '''
    Gets the block size of the device a file is placed in
    
    @param   file:str  The filename of the file, do not need to be the canonical path
    @return  :int      The block size, fall back to a regular value if not possible to determine
    '''
    try:
        return os.stat(os.path.realpath(file)).st_size
    except:
        return 8 << 10


def multibinsearch(rc, list, items):
    '''
    Find the indices of multiple items in a list, with time complexity 𝓞(log n + m) and memory complexity 𝓞(log m) 
    
    @param  rc:append((int, int))→void  Object to which to append found items, the append items are of tuple (itemIndex:int, listIndex:int)
    @param  list:[int]→¿E?;len()→int    Sorted list in which to search, the number of elements is named ‘n’ in the complexity analysis
    @param  items:[int]→¿E?;len()→int   Sorted List of items for which to search, the number of elements is named ‘m’ in the complexity analysis
    '''
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


class Blocklist():
    '''
    A blockdevice representated as a list
    '''
    def __init__(self, file, lbdevblock, offset, blocksize, itemsize, length):
        '''
        Constructor
        
        @param  file:inputfile  The file, it must be seekable
        @param  lbdevblock:int  The binary logarithm of the device's block size
        @param  offset:int      The list's offset in the file
        @param  blocksize:int   The number of bytes between the start of elements
        @param  itemsize:int    The size of each element
        @param  length:int      The number of elements
        '''
        self.file = file
        self.lbdevblock = lbdevblock
        self.devblock = 1 << lbdevblock
        self.offset = offset
        self.blocksize = blocksize
        self.itemsize = itemsize
        self.position = -1
        self.length = length
        self.buffer = None
    
    def __getitem__(self, index):
        '''
        Gets an element by index
        
        @param   index:int  The index of the element
        @return  :bytes     The element
        '''
        pos = index * self.blocksize + self.offset
        if self.position != pos >> self.lbdevblock:
            self.position = pos >> self.lbdevblock
            self.buffer = self.file.read(self.devblock)
        pos &= self.devblock - 1
        return self.buffer[pos : pos + itemsize]
    
    def getValue(self, index):
        '''
        Gets the associated value to an element by index
        
        @param   index:int  The index of the element
        @return  :bytes     The associated value
        '''
        pos = index * self.blocksize + self.offset
        if self.position != pos >> self.lbdevblock:
            self.position = pos >> self.lbdevblock
            self.buffer = self.file.read(self.devblock)
        pos &= self.devblock - 1
        return self.buffer[pos + itemsize : pos + blocksize]
    
    def __len__(self):
        '''
        Gets the number of elements
        
        @return  :int  The number of elements
        '''
        return self.length


def fetch(rc, db, maxlen, keys, valuelen):
    '''
    Looks up values in a file
    
    @param   rc:append((str, bytes?))→void  Sink to which to append found results
    @param   db:str                         The database file
    @param   maxlen:int                     The length of keys
    @param   keys:list<str>                 Keys for which to search
    @param   valuelen:int                   The length of values
    @return  rc:                            `rc` is returned, filled with `(key:str, value:bytes?)`-pairs. `value` is `None` when not found
    '''
    buckets = {}
    for key in unique(sorted(keys)):
        pos = 0
        initials = ''
        while '/' in key[pos : -1]:
            pos = key.find('/') + 1
            initials += key[pos]
        while len(initials) < INITIALS_LEN:
            pos += 1
            if pos == len(initials):
                break
            initials += keys[pos]
        if len(initials) > INITIALS_LEN:
            initials += initials[:INITIALS_LEN]
        initials = [(ord(c) & 15) for c in initials]
        ivalue = 0
        for initial in initials:
            ivalue = (ivalue << 4) | ivalue
        if ivalue not in buckets:
            buckets[ivalue] = []
        buckets[ivalue].append(value)
    devblocksize = __blocksize(db)
    with open(db, 'rb') as file:
        offset = 0
        position = 0
        amount = 0
        masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
        masterseek = file.read(masterseeklen)
        keyvallen = maxlen + valuelen
        for initials in sorted(buckets.keys()):
            if position >= initials:
                position = 0
                offset = 0
                amount = 0
            while position <= initials:
                offset += amount
                amount = [int(b) for b in list(masterseek[3 * position : 3 * (position + 1)])]
                amount = (amount[0] << 16) | (amount[1] << 8) | amount[2]
                position += 1
            fileoffset = masterseeklen + offset * (maxlen + valuelen)
            bucket = buckets[initials]
            bbucket = [(word + '\0' * (maxlen - len(word.encode('utf-8')))).encode('utf-8') for word in bucket]
            list = Blocklist(file, devblocksize, fileoffset, keyvallen, maxlen, amount)
            class Agg():
                def __init__(self, sink, keyMap, valueMap):
                    self.sink = sink
                    self.keyMap = keyMap;
                    self.valueMap = valueMap;
                def append(self, item):
                    val = item[1]
                    val = None if val < 0 else self.valueMap.getValue(val)
                    self.sink.append((self.keyMap[item[0]], val))
            multibinsearch(Agg(rc, bucket, list), list, bbucket)
    return rc


def remove(rc, db, maxlen, keys, valuelen):
    '''
    Looks up values in a file
    
    @param   rc:append(str)→void  Sink on which to append unfound keys
    @param   db:str               The database file
    @param   maxlen:int           The length of keys
    @param   keys:list<str>       Keys for which to search
    @param   valuelen:int         The length of values
    @return  rc:                  `rc` is returned
    '''
    buckets = {}
    for key in unique(sorted(keys)):
        pos = 0
        initials = ''
        while '/' in key[pos : -1]:
            pos = key.find('/') + 1
            initials += key[pos]
        while len(initials) < INITIALS_LEN:
            pos += 1
            if pos == len(initials):
                break
            initials += keys[pos]
        if len(initials) > INITIALS_LEN:
            initials += initials[:INITIALS_LEN]
        initials = [(ord(c) & 15) for c in initials]
        ivalue = 0
        for initial in initials:
            ivalue = (ivalue << 4) | ivalue
        if ivalue not in buckets:
            buckets[ivalue] = []
        buckets[ivalue].append(value)
    devblocksize = __blocksize(db)
    wdata = []
    with open(db, 'rb') as file:
        removelist = []
        diminish = []
        offset = 0
        position = 0
        amount = 0
        masterseeklen = 3 * (1 << (INITIALS_LEN << 2))
        masterseek = list(file.read(masterseeklen))
        keyvallen = maxlen + valuelen
        for initials in sorted(buckets.keys()):
            if position >= initials:
                position = 0
                offset = 0
                amount = 0
            while position <= initials:
                offset += amount
                amount = [int(b) for b in masterseek[3 * position : 3 * (position + 1)]]
                amount = (amount[0] << 16) | (amount[1] << 8) | amount[2]
                position += 1
            fileoffset = masterseeklen + offset * (maxlen + valuelen)
            bucket = buckets[initials]
            bbucket = [(word + '\0' * (maxlen - len(word.encode('utf-8')))).encode('utf-8') for word in bucket]
            curremove = len(removelist)
            list = Blocklist(file, devblocksize, fileoffset, keyvallen, maxlen, amount)
            class Agg():
                def __init__(self, sink, failsink, keyMap, valueMap):
                    self.sink = sink
                    self.failsink = failsink
                    self.keyMap = keyMap;
                    self.valueMap = valueMap;
                def append(self, item):
                    val = item[1]
                    if val < 0:
                        self.failsink.append(self.keyMap[item[0]])
                    else:
                        self.sink.append(val)
            multibinsearch(Agg(removelist, rc, bucket, list), list, bbucket)
            diminishamount = len(removelist) - curremove
            if diminishamount > 0:
                diminish.append(position - 1, diminishamount))
        end = 0
        pos = 0
        while pos < masterseeklen:
            amount = [int(b) for b in masterseek[pos : pos + 3]]
            end += (amount[0] << 16) | (amount[1] << 8) | amount[2]
            pos += 3
        for (index, amount) in diminish:
            pos = 3 * index
            was = [int(b) for b in masterseek[pos : pos + 3]]
            was = (was[0] << 16) | (was[1] << 8) | was[2]
            amount = was - amount
            masterseek[pos : pos + 3] = [b & 255 for b in [amount >> 16, amount >> 8, amount]]
        masterseek = bytes(masterseek)
        wdata.append(masterseek)
        pos = 0
        removelist.sort()
        for indices in (removelist, [end]):
            for index in indices:
                if pos != index:
                    file.seek(offset = masterseeklen + pos * keyvallen, whence = 0) # 0 means from the start of the stream
                    wdata.append(file.read((index - pos) * keyvallen))
                pos = index + 1
    with open(db, 'wb') as file:
        for data in wdata:
            file.write(data)
    return rc


def make(db, maxlen, pairs):
    '''
    Build a database from the ground
    
    @param  db:str                    The database file
    @param  maxlen:int                The length of keys
    @param  pairs:list<(str, bytes)>  Key–value-pairs, all values must be of same length
    '''
    buckets = {}
    for pair in sorted(pairs, key = lambda x : x[0]):
        pos = 0
        initials = ''
        (key, value) = pair
        while '/' in key[pos : -1]:
            pos = key.find('/') + 1
            initials += key[pos]
        while len(initials) < INITIALS_LEN:
            pos += 1
            if pos == len(initials):
                break
            initials += key[pos]
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
        wbuf = bytes([0] * (1 << (INITIALS_LEN << 2)))
        for i in range(3):
            file.write(wbuf)
        wbuf = None
        for initials in sorted(buckets.keys()):
            bucket = buckets[initials]
            for pair in bucket:
                (key, value) = pair
                key = key + '\0' * (maxlen - len(key.encode('utf8')))
                key = key.encode('utf8')
                file.write(key)
                file.write(value)
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
    def _bin(value):
        return bytes([b & 255 for b in [value >> 16, value >> 8, value]])
    make(rc, 'testdb', 50, [(comb[comb.find(' ') + 1:], _bin(hash(comb[:comb.find(' ')]) & 0xFFFFFF)) for comb in data])
else:
    rc = []
    for pair in fetch('testdb', 50, sorted(rc, [os.path.realpath(f)[:50] for f in sys.args[1:]])):
        print('%s --> %s' % pair)

