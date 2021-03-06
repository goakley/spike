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

import os


SOFTWARE_SHAREABLE = 1
SOFTWARE_COMMERCIAL = 2
SOFTWARE_DERIVATIVE = 4
MEDIA_SHAREABLE = 8
MEDIA_COMMERCIAL = 16
MEDIA_DERIVATIVE = 32
TRADEMARKED = 64
PATENTED = 128
MEDIA = MEDIA_SHAREABLE | MEDIA_COMMERCIAL | MEDIA_DERIVATIVE
SOFTWARE = SOFTWARE_SHAREABLE | SOFTWARE_COMMERCIAL | SOFTWARE_DERIVATIVE

UNSUPPORTED = 0
SUPPORTED = 1
MANDITORY = 2

NO_TRADEMARKS = 1
NO_PATENTS = 2
CONTRACT_BASED = 4
COMMERCIAL = 8
DERIVATIVE = 16
FSF_APPROVED = 32
OSI_APPROVED = 64
GPL_COMPATIBLE = 128
COPYLEFT = 256



class ScrollMagick():
    '''
    Functions for playing with scrolls
    '''
    
    def __init__(self, globals):
        '''
        Constructor
        
        @param  globals:dict<str, any>  Should be `globals()`
        '''
        self.globals = globals
    
    
    @staticmethod
    def export_environment():
        '''
        Export environment variables for the scrolls
        '''
        # Set $ARCH and $HOST
        for (var, value) in [('ARCH', os.uname()[4]), ('HOST', '$ARCH-unknown-linux-gnu')]:
            value = os.getenv(var, value.replace('$ARCH', os.getenv('ARCH', '')))
            os.putenv(var, value)
            if var not in os.environ or os.environ[var] != value:
                os.environ[var] = value
    
    
    @staticmethod
    def execute_scroll(scroll, globals):
        '''
        Opens, compiles and executes a scroll
        
        @param  scroll:str              The scroll file
        @param  globals:dict<str, any>  Should be `globals()`
        '''
        code = None
        with open(scroll, 'rb') as file:
            code = file.read().decode('utf8', 'replace') + '\n'
            code = compile(code, scroll, 'exec')
        exec(code, globals)
    
    
    @staticmethod
    def init_fields(globals):
        '''
        Initialise or reset scroll fields, they will be set to global variables
        
        @param  globals:dict<str, any>  Should be `globals()`
        '''
        vars = 'pkgname pkgver pkgdesc upstream arch freedom license metalicense private extension variant patches reason source sha3sums'
        for var in vars.split(' '):
            globals[var] = None
        
        vars = 'conflicts replaces provides patchbefore patchafter groups depends makedepends checkdepends optdepends noextract options backup'
        for var in vars.split(' '):
            globals[var] = []
        
        globals['pkgrel'] = 1
        globals['epoch'] = 0
        globals['interactive'] = False
    
    
    @staticmethod
    def init_methods(globals):
        '''
        Initialise or reset scroll methods, they will be set to global variables
        
        @param  globals:dict<str, any>  Should be `globals()`
        '''
        vars = 'ride build check package patch_build patch_check patch_package'.split(' ')
        for master in ['install', 'upgrade', 'uninstall']:
            vars.append('pre_' + master)
            vars.append('post_' + master)
        for var in vars:
            globals[var] = None
    
    
    def check_type(self, field, with_none, *with_classes):
        '''
        Checks that the value of a field is of a specific class
        
        @param  field:str|itr<str>  The name of the field
        @param  with_none:bool      Whether the value may be `None`
        @param  with_classes:*type  The classes of the value
        '''
        for f in [field] if isinstance(field, str) else field:
            value = self.globals[f]
            if value is None:
                if not with_none:
                    raise Exception('Field \'%s\' may not be `None`' % f)
                else:
                    continue
            isclass = type(value)
            if isclass not in set(with_classes):
                allowed = ', '.join([c.__name__ for c in with_classes])
                if ', ' in allowed:
                    allowed = allowed[:allowed.rfind(', ')] + ' and ' + allowed[allowed.rfind(', ') + 2:]
                raise Exception('Field \'%s\' is restricted to %s, is \'%s\' of type \'%s\'' % (f, allowed, str(value), str(type(value).__name__)))
    
    
    def check_is_list(self, field, with_none, *with_classes):
        '''
        Checks that the value of a field is a list and that its elements is of a specific class
        
        @param  field:str|itr<str>  The name of the field
        @param  with_none:bool      Whether the elements may be `None`
        @param  with_classes:*type  The classes of the elements
        '''
        with_classes = set(with_classes)
        for f in [field] if isinstance(field, str) else field:
            value = self.globals[f]
            if value is None:
                raise Exception('Field \'%s\' must be a list' % f)
            if not isinstance(value, list):
                raise Exception('Field \'%s\' must be a list' % f)
            for elem in value:
                if not with_none:
                    if elem is None:
                        raise Exception('Field \'%s\' may not contain `None`' % f)
                isclass = type(elem)
                if isclass not in with_classes:
                    allowed = ', '.join([c.__name__ for c in with_classes])
                    if ', ' in allowed:
                        allowed = allowed[:allowed.rfind(', ')] + ' and ' + allowed[allowed.rfind(', ') + 2:]
                    raise Exception('Field \'%s\' is restricted to %s elements' % (f, allowed))
    
    
    def check_elements(self, field, values):
        '''
        Checks that the value of a field is a list and that its elements is of a specific class
        
        @param  field:str|itr<str>  The name of the field
        @param  values:itr<¿E?>     The allowed elements
        '''
        values = set(values)
        for f in [field] if isinstance(field, str) else field:
            value = self.globals[f]
            for elem in value:
                if elem not in values:
                    raise Exception('Field \'%s\' may not contain the value \'%s\'' % (f, str(elem)))
    
    
    def check_format(self, field, checker):
        '''
        Checks that a non-`None` value satisfies a format
        
        @param  field:str|itr<str>  The name of the field
        @param  checker:(¿E?)→bool  Value checker
        '''
        for f in [field] if isinstance(field, str) else field:
            value = self.globals[f]
            if value is not None:
                if not checker(value):
                    raise Exception('Field \'%s\' is of bady formated value \'%s\'' % (f, value))
    
    
    def check_element_format(self, field, checker):
        '''
        Checks that non-`None` elements in a list satisfies a format
        
        @param  field:str|itr<str>  The name of the field
        @param  checker:(¿E?)→bool  List element checker
        '''
        for f in [field] if isinstance(field, str) else field:
            value = self.globals[f]
            for elem in value:
                if elem is not None:
                    if not checker(elem):
                        raise Exception('Field \'%s\' contains badly formated value \'%s\'' % (f, elem))
    
    
    def check_type_format(self, field, with_none, with_class, checker):
        '''
        Checks that the value of a field is of a specific class and that a non-`None` value satisfies a format
        
        @param  field:str|itr<str>  The name of the field
        @param  with_none:bool      Whether the value may be `None`
        @param  with_class:type     The class of the value
        @param  checker:(¿E?)→bool  Value checker
        '''
        for f in [field] if isinstance(field, str) else field:
            self.check_type(f, with_none, with_class)
            self.check_format(f, checker)
    
    
    def check_is_list_format(self, field, with_none, with_class, checker):
        '''
        Checks that the value of a field is a list and that its elements is of a specific class and that non-`None` elements in a list satisfies a format
        
        @param  field:str|itr<str>  The name of the field
        @param  with_none:bool      Whether the elements may be `None`
        @param  with_class:type     The class of the elements
        @param  checker:(¿E?)→bool  List element checker
        '''
        for f in [field] if isinstance(field, str) else field:
            self.check_is_list(f, with_none, with_class)
            self.check_element_format(f, checker)
    
    
    def check_is_list_elements(self, field, with_none, with_class, values):
        '''
        Checks that the value of a field is a list and that its elements is confined to a specific set of values
        
        @param  field:str|itr<str>    The name of the field
        @param  with_none:bool        Whether the elements may be `None`
        @param  with_class:type<¿E?>  The class of the elements
        @param  values:itr<¿E??>      The allowed elements
        '''
        values = (list(values) + [None]) if with_none else values
        for f in [field] if isinstance(field, str) else field:
            self.check_is_list(f, with_none, with_class)
            self.check_elements(f, values)
    
    
    def addon_proofread(self, scroll, scroll_file):
        '''
        Onion this function with addition proofreading if you are an extension.
        The scroll is already loaded. Raise an exception if you find an error.
        
        @param  scroll:str       The specified scroll
        @param  scroll_file:str  The file found for the scroll
        '''
        pass
    
    
    @staticmethod
    def field_display_convert(field, value):
        '''
        If required, converts the field value to a pony friendly format, otherwise, it performs a identity mapping
        
        @param   field:str        The name of the field
        @param   value:¿I?        The raw value of the field
        @return  {value:}|{:¿O?}  Pony friendly display value of the field
        '''
        # TODO add `metalicense`
        if isinstance(value, int):
            if field == 'freedom':
                if 0 <= value < (1 << 8):
                    rc = []
                    if (value & SOFTWARE) == SOFTWARE:
                        rc.append('Free software')
                    else:
                        if (value & SOFTWARE_SHAREABLE) != 0:
                            rc.append('Shareable software')
                        if (value & SOFTWARE_COMMERCIAL) != 0:
                            rc.append('Resellable software')
                        if (value & SOFTWARE_DERIVATIVE) != 0:
                            rc.append('Modifiable software')
                    if (value & MEDIA) != MEDIA:
                        rc.append('Free media')
                    else:
                        if (value & MEDIA_SHAREABLE) != 0:
                            rc.append('Shareable media')
                        if (value & MEDIA_COMMERCIAL) != 0:
                            rc.append('Resellable media')
                        if (value & MEDIA_DERIVATIVE) != 0:
                            rc.append('Modifiable media')
                    if (value & TRADEMARKED) != 0:
                        rc.append('Trademark protected')
                    if (value & PATENTED) != 0:
                        rc.append('Patent protected')
                    return rc
            elif field == 'private':
                if 0 <= value < 3:
                    return ('Unsupported', 'Supported', 'Manditory')[value]
        return value

