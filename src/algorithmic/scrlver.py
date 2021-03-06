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

'''
Scroll Version (scrlver)

This module contains function that has to do with scroll version
'''


class ScrollVersion():
    '''
    Scroll with name and version range
    
    @variable  full:str         The scroll with its version range represent as a string
    @variable  name:str         The name of the scroll
    @variable  lower:Version?   The lower bound in the version range
    @variable  upper:Version?   The upper bound in the version range
    @variable  complement:bool  Whether the range is stored in its complement, can only be true one exact version is specified
    '''
    
    def __init__(self, scroll):
        '''
        Constructor
        
        @param  scroll:version  Scroll with version range
        '''
        parts = scroll.replace('<', '\0<\0').replace('>', '\0>\0').replace('=', '\0=\0').replace('\0\0', '').split('\0')
        self.full = scroll
        self.name = None
        self.lower = None
        self.upper = None
        self.complement = False
        self.union_mode = False
        
        if len(parts) == 1:
            self.name = parts[0]
        elif len(parts) == 3:
            if parts[1] not in ('<', '<=', '>', '>=', '=', '<>'):
                return
            self.name = parts[0]
            ver = ScrollVersion.Version(parts[2], '=' not in parts[1])
            islower = '>' in parts[1]
            isupper = '<' in parts[1]
            if islower == isupper:
                self.complement = islower and isupper
                ver.isopen = False
                (self.lower, self.upper) = (ver, ver)
            elif islower:
                self.lower = ver
            else:
                self.upper = ver
        elif len(parts) == 5:
            if (parts[1] not in ('>', '>=')) or (parts[3] not in ('<', '<=')):
                return
            self.name = parts[0]
            self.lower = ScrollVersion.Version(parts[2], '=' not in parts[1])
            self.upper = ScrollVersion.Version(parts[4], '=' not in parts[3])
    
    
    class Version():
        '''
        A scroll version, not a range and not a scroll name, but with other or not it is open
        '''
        
        def __init__(self, version, open):
            '''
            Constructor
            
            @param  version:str  The version represented in text
            @param  open:bool    Whether this end is open
            '''
            self.version = version
            self.epoch = 0
            self.release = -1
            if ':' in version:
                self.epoch = int(version[:version.find(':')])
                version = version[version.find(':') + 1:]
            if '-' in version:
                self.release = int(version[version.find('-') + 1:])
                version = version[:version.find('-')]
            self.parts = version.split('.')
            self.open = open
        
        
        def as_closed(self, closed = True):
            '''
            Return a version that is closed, or open if you prefer
            
            @param   closed:bool  Whether the new version should be close
            @return               An identical version except possibility when another openness
            '''
            return ScrollVersion.Version(self.version, not closed)
        
        
        def __cmp(self, other):
            '''
            Preforms a comparison of two version numbers, does not compare release number
            
            @param   other:Version  The other version number
            @return  :int           negative if `self` is less, zero if `self` equals `other`, and positive if `other` is less
            '''
            if self.epoch != other.epoch:
                return self.epoch - other.epoch
            
            (n, m) = (len(self.parts), len(other.parts))
            for i in range(min(n, m)):
                (a, b) = (self.parts[i], other.parts[i])
                if a == b:
                    continue
                (_a, _b) = ([], [])
                if len(a) > 0:
                    buf = ''
                    for j in range(len(a)):
                        isnum = '0' <= a[j] <= '9'
                        wantnum = (len(_a) & 1) == 1
                        if isnum != wantnum:
                            _a.append(buf)
                            buf = a[j]
                        else:
                            buf += a[j]
                    _a.append(buf)
                if len(b) > 0:
                    buf = ''
                    for j in range(len(b)):
                        isnum = '0' <= a[j] <= '9'
                        wantnum = (len(_b) & 1) == 1
                        if isnum != wantnum:
                            _b.append(buf)
                            buf = b[j]
                        else:
                            buf += b[j]
                    _b.append(buf)
                (_n, _m) = (len(_a), len(_b))
                for j in range(min(_n, _m)):
                    (a, b) = (_a[j], _b[j])
                    if a != b:
                        if (j & 1) == 1:
                            return int(a) - int(b)
                        else:
                            return -1 if a < b else 1
                if _n != _m:
                    return _n - _m
            
            return n - m
        
        
        def __lt__(self, other):
            '''
            Operator: <
            '''
            return (self <= other) and not (self == other)
        
        
        def __le__(self, other):
            '''
            Operator: <=
            '''
            cmp = self.__cmp(other)
            if cmp != 0:
                return cmp < 0
            if (self.release < 0) or (other.release < 0):
                return not (self.open or other.open)
            if self.open or other.open:
                return self.release < other.release
            else:
                return self.release <= other.release
        
        
        def __eq__(self, other):
            '''
            Operator: ==
            '''
            if (self is None) or (other is None):
                return (self is None) and (other is None)
            
            cmp = self.__cmp(other)
            if cmp != 0:
                return False
            if (self.release < 0) or (other.release < 0):
                return not (self.open or other.open)
            if self.open or other.open:
                return False
            else:
                return self.release == other.release
        
        
        def __ne__(self, other):
            '''
            Operator: !=
            '''
            return not (self == other)
        
        
        def __gt__(self, other):
            '''
            Operator: >
            '''
            return other < self
        
        
        def __ge__(self, other):
            '''
            Operator: >=
            '''
            return other <= self
    
    
    def __hash__(self):
        '''
        Returns hash of the scroll name
        
        @return  The hash of the scroll name
        '''
        return hash(self.name)
    
    
    def __contains__(self, other):
        '''
        Checks if two scrolls intersects
        
        @param   other:ScrollVersion  The other scroll
        @return  :bool                Whether the two scrolls have the same name and their version ranges intersects
        '''
        if self.union_mode:
            if self.joinable_with(other):
                return True
        if self.name != other.name:
            return False
        
        c = lambda version : version.as_closed()
        
        if ((other.lower is None) and (other.upper is None)) or ((self.lower is None) and (self.upper is None)):
            return True
        elif ((self.lower is None) and (other.lower is None)) or ((self.upper is None) and (other.upper is None)):
            return True
        elif self.complement and other.complement:
            return True
        elif  self.lower is None:  return other.complement or (other.lower <= self.upper)
        elif  self.upper is None:  return other.complement or (other.upper >= self.lower)
        elif other.upper is None:  return  self.complement or (other.lower <= self.upper)
        elif other.lower is None:  return  self.complement or (other.upper >= self.lower)
        elif other.complement:     return ( c(self.lower) !=  c(self.upper)) or (c(self.lower) != c(other.lower))
        elif  self.complement:     return (c(other.lower) != c(other.upper)) or (c(self.lower) != c(other.lower))
        elif  self.lower ==  self.upper:  return other.lower <=  self.lower <= other.upper
        elif other.lower == other.upper:  return  self.lower <= other.lower <=  self.upper
        else:
            sl, su =  self.lower,  self.upper
            ol, ou = other.lower, other.upper
            if (sl <= ol <= su) or (sl <= ou <= su):  return True
            if (ol <= sl <= ou) or (ol <= su <= ou):  return True
            if (c(sl) == c(ol)) and (sl < ou): return True
            if (c(ol) == c(sl)) and (ol < su): return True
            if (c(su) == c(ou)) and (sl < ou): return True
            if (c(ou) == c(su)) and (ol < su): return True
            return False
    
    
    def __eq__(self, other):
        '''
        Operator: ==
        
        Implemented as a synomym for `other in self`, checking if they intersect
        '''
        return self in other
    
    
    def __str__(self):
        '''
        Return the object as a string
        
        @return  :str  The object as a string
        '''
        return self.full
    
    
    def joinable_with(self, other):
        '''
        Checks if the scroll version can be joined with another other
        
        @param   other:ScrollVersion  The other scroll
        @return  :bool                Whether a join is possible
        '''
        if self.name != other.name:
            return False
        if ( self.lower is None) and ( self.upper is None):  return False
        if (other.lower is None) and (other.upper is None):  return False
        if ( self.lower is None) and (other.lower is None):  return False
        if ( self.upper is None) and (other.upper is None):  return False
        
        xor = lambda x, y : x != y
        c = lambda v : v.as_closed()
        if self.complement and other.complement:
            return False
        if other.complement:
            return other.joinable_with(self)
        if self.complement:
            return c(self.lower) == other.lower == other.upper
        
        if (self.lower is None) or (other.upper is None):
            return (c(self.upper) == c(other.lower)) and xor(self.upper.open, other.lower.open)
        if (self.upper is None) or (other.lower is None):
            return (c(self.lower) == c(other.upper)) and xor(self.lower.open, other.upper.open)
        
        if other.lower == other.upper:
            return (self.lower != self.upper) and other.joinable_with(self)
        if self.lower == self.upper:
            a = (self.lower == c(other.lower)) and other.lower.open
            b = (self.lower == c(other.upper)) and other.upper.open
            return a or b
        
        a = c(self.upper) == c(other.lower)
        b = c(self.lower) == c(other.upper)
        
        ao = xor(self.upper.open, other.lower.open)
        bo = xor(self.lower.open, other.upper.open)
        
        return xor(a, b) and (ao, bo)[b]
    
    
    def join(self, other):
        '''
        Joins two scroll versions
        
        @param   other:ScrollVersion  The other scroll
        @return  :ScrollVersion       The join of the two scrolls
        '''
        if other.complement or self.complement:
            return ScrollVersion(self.name)
        
        c = lambda v : v.as_closed()
        
        lower = None
        upper = None
        if (self.upper is not None) and (other.lower is not None) and (c(self.upper) == c(other.lower)):
            lower = self.lower
            upper = other.upper
        else:
            lower = other.lower
            upper = self.upper
        
        full = self.name
        if lower is not None:
            full += '>' if lower.open else '>='
            full += lower.version
        if upper is not None:
            full += '<' if upper.open else '<='
            full += upper.version
        return ScrollVersion(full)
    
    
    def union(self, other):
        '''
        Creates a union of two intersecting scroll versions
        
        @param   other:ScrollVersion  The other scrolls 
        @return  :ScrollVersion       The union of the two scrolls
        '''
        if self.union_mode and self.joinable_with(other):
            return self.join(other)
        
        if self.complement:
            return ScrollVersion(self.name) if other in ScrollVersion(self.full.replace('<>', '=')) else self
        if other.complement:
            return other.union(self)
        if (self.lower == self.upper) or (other.lower == other.upper):
            if self.lower is None:
                return self
            if other.lower is None:
                return other
            return self if self.lower.release < 0 else other
        
        name = self.name
        lower = None
        upper = None
        lower_open = None
        upper_open = None
        rellower = True
        relupper = True
        
        if (self.lower is not None) and (other.lower is not None):
            lower = self.lower if self.lower <= other.lower else other.lower
            if self.lower == other.lower:
                rellower = (self.lower.release >= 0) and (other.lower.release >= 0)
            if self.lower.version.split('-')[0] == other.lower.version.split('-')[0]:
                lower_open = self.lower.open and other.lower.open
        if (self.upper is not None) and (other.upper is not None):
            upper = self.upper if self.upper >= other.upper else other.upper
            if self.upper == other.upper:
                relupper = (self.upper.release >= 0) and (other.upper.release >= 0)
            if self.upper.version.split('-')[0] == other.upper.version.split('-')[0]:
                upper_open = self.upper.open and other.upper.open
        
        full = name
        if lower is not None:
            lower_open = lower_open if lower_open is not None else lower.open
            full += '>' if lower_open else '>='
            full += lower.version if rellower else lower.version.split('-')[0]
        if upper is not None:
            upper_open = upper_open if upper_open is not None else upper.open
            full += '<' if upper_open else '<='
            full += upper.version if relupper else upper.version.split('-')[0]
        
        return ScrollVersion(full)
    
    
    def intersection(self, other):
        '''
        Creates a intersection of two intersecting scroll versions
        
        @param   other:ScrollVersion  The other scrolls
        @return  :ScrollVersion?      The union of the two scrolls, `None` if there is no sole intersection
        '''
        if (self.complement and other.complement) and (self.lower.as_closed() != other.lower.as_closed()):
            return None
        if self.complement:
            return other
        if other.complement:
            return self
        if (self.lower == self.upper) or (other.lower == other.upper):
            if (self.lower is not None) and (other.lower is not None):
                return other if self.lower.release < 0 else self
            return self if self.lower is not None else other
        
        name = self.name
        lower = None
        upper = None
        lower_open = None
        upper_open = None
        
        if (self.lower is not None) and (other.lower is not None):
            if self.lower.as_closed() == other.lower.as_closed():
                lower = other.lower if self.lower.release < 0 else self.lower
                lower_open = self.lower.open or other.lower.open
            else:
                lower = self.lower if self.lower >= other.lower else other.lower
        elif (self.lower is not None) != (other.lower is not None):
            lower = self.lower if self.lower is not None else other.lower
        
        if (self.upper is not None) and (other.upper is not None):
            if self.upper.as_closed() == other.upper.as_closed():
                upper = other.upper if self.upper.release < 0 else self.upper
                upper_open = self.upper.open or other.upper.open
            else:
                upper = self.upper if self.upper <= other.upper else other.upper
        elif (self.upper is not None) != (other.upper is not None):
            upper = self.upper if self.upper is not None else other.upper
        
        full = name
        if lower is not None:
            lower_open = lower_open if lower_open is not None else lower.open
            full += '>' if lower_open else '>='
            full += lower.version
        if upper is not None:
            upper_open = upper_open if upper_open is not None else upper.open
            full += '<' if upper_open else '<='
            full += upper.version
        
        return ScrollVersion(full)
    
    
    def union_add(self, scroll_set):
        '''
        Updates a set of ScrollVersion:s by replacing the existing scroll with the union of that and this scroll
        
        @param  scroll_set:set<ScrollVersion>  Set of scrolls
        '''
        self.union_mode = True
        if self in scroll_set:
            others = list(filter(lambda element : self in element, list(scroll_set)))
            while self in scroll_set:
                scroll_set.remove(self)
            others = [self.union(o) for o in others]
            scroll_set.add(others[0])
            for other in others[1:]:
                other.union_add(scroll_set)
        else:
            scroll_set.add(self)
    
    
    def intersection_add(self, scroll_set):
        '''
        Updates a set of ScrollVersion:s by replacing the existing scroll with the intersaction of that and this scroll
        
        @param  scroll_set:set<ScrollVersion>  Set of scrolls
        '''
        ## FIXME  The most be rewritten, it is not commutative
        
        if self.complement:
            a = ScrollVersion(self.name + '>' + self.lower.version)
            b = ScrollVersion(self.name + '<' + self.lower.version)
            _a = a in scroll_set
            _b = b in scroll_set
            if _a or _b:
                if _a: a.intersection_add(scroll_set)
                if _b: b.intersection_add(scroll_set)
            else:
                a.intersection_add(scroll_set)
                b.intersection_add(scroll_set)
        elif self in scroll_set:
            others = list(filter(lambda element : self in element, list(scroll_set)))
            while self in scroll_set:
                scroll_set.remove(self)
            others = [self.intersection(o) for o in others]
            scroll_set.add(others[0])
            for other in others[1:]:
                other.intersection_add(scroll_set)
        else:
            scroll_set.add(self)
    
    
    @staticmethod
    def slice(versions):
        '''
        For a set of ScrollVersion:s, create a list of slices such that for all limits in all versions there exists exactly one limit in the returned list
        
        @param   versions:itr<ScrollVersion>  The ScrollVersion:s
        @return  :list<ScrollVersion>         The slices
        '''
        versions = list(versions)
        if len(versions) <= 1:
            return versions
        name = versions[0].name
        limits = []
        neginf = False
        posinf = False
        for version in versions:
            if version.complement:
                neginf = True
                posinf = True
                limits.append(ScrollVersion.Version(version.version, False))
            else:
                if version.lower is None:
                    neginf = True
                else:
                    limits.append(version.lower)
                if version.upper is None:
                    posinf = True
                else:
                    limits.append(version.upper)
        limits.sort()
        rc = []
        last = None
        for limit in limits:
            if limit != last:
                if last is None:
                    if neginf:
                        rc.append(ScrollVersion('%s%s%s' % (name, '<' if limit.open else '<=', limit.version)))
                else:
                    lower = '%s%s' % ('>' if last.open else '>=', last.version)
                    upper = '%s%s' % ('<' if limit.open else '<=', limit.version)
                    rc.append(ScrollVersion('%s%s%s' % (name, lower, upper)))
                last = limit
        if posinf:
            if last is None:
                rc.append(ScrollVersion(name))
            else:
                rc.append(ScrollVersion('%s%s%s' % (name, '>' if last.open else '>=', last.version)))
        return rc
    
    
    def slice_map(self, scroll_map, value):
        '''
        Updates a map from ScrollVersion:s by splitting up scrolls with version ranges into slices and
        appending a value to a list of values
        
        @param  scroll_map:map<ScrollVersion, list<¿E?>>  Map from scrolls
        @param  value:¿E?                                 The value
        '''
        if self in scroll_map:
            others = [self]
            for other in scroll_map:
                if self in other:
                    other.append(other)
            slices = {}
            for slice in ScrollVersion.slice(others):
                if slice not in slices:
                    slices[slice] = [value]
                slices[slice] += scroll_map[slice]
            while self in scroll_map:
                del scroll_map[self]
            for slice in slices:
                scroll_map[slice] = slices[slice]
        else:
            scroll_map.put(self, [value])
    
    
    def get_all(self, scrollmap):
        '''
        Gets all values associated with any version of a scroll in a range of versions
        
        @param   scroll_map:map<ScrollVersion, list<¿E?>>  The map the look in
        @return  :list<¿E?>                                The values
        '''
        rc = set()
        for scroll in scroll_map:
            if self in scroll:
                for value in scroll_map[scroll]:
                    rc.add(value)
        return list(rc)

