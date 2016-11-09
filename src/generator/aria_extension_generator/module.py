# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
from collections import OrderedDict

from aria.utils import safe_repr

from .cls import CodeClass
from .writer import Writer, create_header


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
            module = self.get_module(name)
            return module.get_module(remainder)

        for module_name, module in self.children.iteritems():
            if module_name == name:
                return module

        if create:
            module = CodeModule(self.generator, name, self)
            self.children[name] = module
            return module

        return None

    def get_class(self, name, create=True):
        if name in self.classes:
            return self.classes[name]
        if create:
            class_ = CodeClass(self.generator, name, module=self)
            self.classes[name] = class_
            return class_
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
            def __cmp__(self, other):
                if self.cls.module == other.cls.module:
                    if self.cls.base == other.cls:
                        return 1
                    elif other.cls.base == self.cls:
                        return -1
                return 0

        def key((_, class_)):
            return Wrapper(class_)

        items = self.classes.items()
        items.sort(key=key)
        self.classes = OrderedDict(items)

    @property
    def all_modules(self):
        yield self
        for module in self.children.itervalues():
            for module in module.all_modules:
                yield module

    @property
    def all_classes(self):
        for class_ in self.classes.itervalues():
            yield class_
        for module in self.children.itervalues():
            for class_ in module.all_classes:
                yield class_

    @property
    def fullname(self):
        name = self.parent.fullname if self.parent else ''
        return '%s.%s' % (name, self.name) if name else self.name

    @property
    def path(self):
        path = self.parent.path if self.parent else ''
        return os.path.join(path, self.name) if path else self.name

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
        with Writer() as writer:
            writer.write(create_header())
            imports = set()
            for class_ in self.classes.itervalues():
                if (class_.base != 'object') and (class_.base.module != self):
                    imports.add(class_.base.module.fullname)
                for property in class_.properties.itervalues():
                    if property.type:
                        cls = self.generator.get_class(property.type, False)
                        if cls:
                            if cls.module != self:
                                imports.add(cls.module.fullname)
            for i in imports:
                writer.write('import %s' % i)
            writer.write()
            for class_ in self.classes.itervalues():
                writer.write(str(class_))
            if self.children:
                all_value = [m.name for m in self.children.itervalues()]
                all_value += [class_.name for class_ in self.classes.itervalues()]
                writer.write('__all__ = %s' % safe_repr(all_value))
            return str(writer)
