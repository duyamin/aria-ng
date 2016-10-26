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

from .writer import Writer
from collections import OrderedDict

class CodeMethod(object):
    def __init__(self, generator, name, interface, description, implementation, executor):
        self.generator = generator
        self.name = name
        self.interface = interface
        self.description = description
        self.implementation = implementation
        self.executor = executor
        self.arguments = OrderedDict()
    
    def __str__(self):
        with Writer() as w:
            if self.interface:
                w.write('@interfacemethod(%s)' % repr(self.interface))
            w.put('def %s(self' % self.name)
            if self.arguments:
                for a in self.arguments.itervalues():
                    w.put(', %s' % a.signature)
            w.put('):\n')
            w.i()
            if self.description or self.arguments:
                w.write('"""')
                if self.description:
                    self.write(self.description.strip())
                if self.arguments:
                    if self.description:
                        self.write()
                    for n, a in self.arguments.iteritems():
                        w.write(a.docstring)
                w.write('"""')
            w.put_indent()
            if self.implementation:
                if self.executor:
                    w.put('self.context.executor(%s).' % repr(self.executor))
                else:
                    w.put('self.context.executor().')
                if '/' in self.implementation:
                    w.put('selc.context.executor().execute(self, %s' % repr(self.implementation))
                else:
                    w.put('%s(self' % self.implementation)
                if self.arguments:
                    for n in self.arguments:
                        w.put(', %s' % n)
                w.put(')')
            else:
                w.put('pass')
            return str(w)
