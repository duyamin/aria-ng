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

from .module import CodeModule
from .writer import Writer, create_header, repr_assignment
from aria.utils import safe_repr
from collections import OrderedDict
import os

class CodeGenerator(object):
    def __init__(self):
        self.description = None
        self.module = CodeModule(self)
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.nodes = OrderedDict()
        self.workflows = OrderedDict()
        self.translate_classes = {
            'string': 'str',
            'integer': 'int',
            'boolean': 'bool'}
        self.common_module_name = 'common'
    
    def get_class(self, name, create=True):
        return self.module.find_class(name, create)

    def get_classname(self, name):
        if name in self.translate_classes:
            r = self.translate_classes[name]
            return r if isinstance(r, str) else r.fullname
        return name

    def link_classes(self):
        for c in self.module.all_classes:
            if isinstance(c.base, str):
                b = self.get_class(c.base, False)
                if b:
                    c.base = b
        for c in self.module.all_classes:
            if not c.module.name:
                del c.module.classes[c.name]
                root = self.module.get_module(self.common_module_name)
                c.module = root
                root.classes[c.name] = c
                self.translate_classes[c.name] = c
    
    def write_file(self, the_file, content):
        try:
            os.makedirs(os.path.dirname(the_file))
        except OSError as e:
            if e.errno != 17:
                raise e
        with open(the_file, 'w') as f:
            f.write(str(content))
    
    def write(self, root):
        self.link_classes()
        for m in self.module.all_modules:
            if m.name:
                the_file = os.path.join(root, m.file)
                self.write_file(the_file, m)
        the_file = os.path.join(root, 'service.py')
        self.write_file(the_file, self.service)

    @property
    def service(self):
        with Writer() as w:
            w.write(create_header())
            for m in self.module.all_modules:
                if m.fullname:
                    w.write('import %s' % m.fullname)
            w.write()
            w.write('class Service(object):')
            w.i()
            if self.description or self.inputs:
                w.write('"""')
                if self.description:
                    w.write(self.description.strip())
                if self.inputs:
                    if self.description:
                        w.write()
                    for i in self.inputs.itervalues():
                        w.write(i.docstring)
                w.write('"""')
            if self.inputs or self.outputs or self.nodes or self.workflows:
                w.write()
                w.write('# Metadata')
                if self.inputs:
                    w.write('INPUTS = %s' % safe_repr(tuple(self.inputs.keys())))
                if self.outputs:
                    w.write('OUTPUTS = %s' % safe_repr(tuple(self.outputs.keys())))
                if self.nodes:
                    w.write('NODES = %s' % safe_repr(tuple(self.nodes.keys())))
                if self.workflows:
                    w.write('WORKFLOWS = %s' % safe_repr(tuple(self.workflows.keys())))
                w.write()
            w.put_indent()
            w.put('def __init__(self, context')
            if self.inputs:
                for i in self.inputs.itervalues():
                    w.put(', %s' % i.signature)
            w.put('):\n')
            w.i()
            w.write('self.context = context')
            w.write('self.context.service = self')
            if self.inputs:
                w.write()
                w.write('# Inputs')
                for i in self.inputs:
                    w.write('self.%s = %s' % (i, i))
            if self.nodes:
                w.write()
                for n in self.nodes.itervalues():
                    w.write(n.description or 'Node: %s' % n.name, prefix='# ')
                    w.write(n)
                has_relationships = False
                for n in self.nodes.itervalues():
                    if n.relationships:
                        has_relationships = True
                        break
                if has_relationships:
                    w.write('# Relationships')
                    for n in self.nodes.itervalues():
                        n.relate(w)
            w.o()
            if self.outputs:
                w.write()
                w.write('# Outputs')
                for o in self.outputs.itervalues():
                    w.write()
                    w.write('@property')
                    w.write('def %s(self):' % o.name)
                    w.i()
                    if o.description:
                        w.write_docstring(o.description)
                    w.write('return %s' % repr_assignment(o.value))
                    w.o()
            if self.workflows:
                w.write()
                w.write('# Workflows')
                for workflow in self.workflows.itervalues():
                    w.write()
                    w.write(str(workflow))
            return str(w)
