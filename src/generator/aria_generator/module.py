#
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

from .cls import CodeClass
from .writer import Writer, create_header
from aria.utils import safe_repr
from collections import OrderedDict
import os

class CodeModule(object):
    def __init__(self, generator, name='', parent=None):
        self.generator = generator
        self.name = name
        self.parent = parent
        self.children = {}
        self.classes = OrderedDict()
    
    def get_module(self, name, create=True):
        if name is None:
            return self
            
        if '.' in name:
            name, remainder = name.split('.', 1)
            m = self.get_module(name)
            return m.get_module(remainder)
        
        for n, m in self.children.iteritems():
            if n == name:
                return m
        
        if create:
            m = CodeModule(self.generator, name, self)
            self.children[name] = m
            return m
        
        return None
    
    def get_class(self, name, create=True):
        if name in self.classes:
            return self.classes[name]
        if create:
            c = CodeClass(self.generator, name, module=self)
            self.classes[name] = c
            return c
        return None
    
    def find_class(self, name, create=True):
        module = None
        if '.' in name:
            module, name = name.rsplit('.', 1)
        module = self.get_module(module, create)
        return module.get_class(name, create) if module else None
    
    def sort_classes(self):
        class Wrapper(object):
            def __init__(self, cls):
                self.cls = cls
            def __cmp__(self, o):
                if (self.cls.module == o.cls.module):
                    if (self.cls.base == o.cls):
                        return 1
                    elif (o.cls.base == self.cls):
                        return -1
                return 0
                
        def key((_, c)):
            return Wrapper(c)
        
        items = self.classes.items()
        items.sort(key=key)
        self.classes = OrderedDict(items)

    @property
    def all_modules(self):
        yield self
        for m in self.children.itervalues():
            for m in m.all_modules:
                yield m

    @property
    def all_classes(self):
        for c in self.classes.itervalues():
            yield c
        for m in self.children.itervalues():
            for c in m.all_classes:
                yield c

    @property
    def fullname(self):
        n = self.parent.fullname if self.parent else ''
        return '%s.%s' % (n, self.name) if n else self.name
    
    @property
    def path(self):
        p = self.parent.path if self.parent else ''
        return os.path.join(p, self.name) if p else self.name
    
    @property
    def file(self):
        f = self.parent.path if self.parent else ''
        if self.children:
            if self.name:
                f = os.path.join(f, self.name)
            f = os.path.join(f, '__init__.py')
        else:
            f = os.path.join(f, self.name + '.py')
        return f
    
    def __str__(self):
        self.sort_classes()
        with Writer() as w:
            w.write(create_header())
            imports = set()
            for c in self.classes.itervalues():
                if (c.base != 'object') and (c.base.module != self):
                    imports.add(c.base.module.fullname)
                for p in c.properties.itervalues():
                    if p.type:
                        cc = self.generator.get_class(p.type, False)
                        if cc:
                            if cc.module != self:
                                imports.add(cc.module.fullname)
            for i in imports:
                w.write('import %s' % i)
            w.write()
            for c in self.classes.itervalues():
                w.write(str(c))
            if self.children:
                all_value = [m.name for m in self.children.itervalues()]
                all_value += [c.name for c in self.classes.itervalues()]
                w.write('__all__ = %s' % safe_repr(all_value))
            return str(w)
