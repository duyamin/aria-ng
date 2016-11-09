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


from collections import OrderedDict

from .writer import Writer


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
        with Writer() as writer:
            if self.interface:
                writer.write('@interfacemethod(%s)' % repr(self.interface))
            writer.put('def %s(self' % self.name)
            if self.arguments:
                for arg in self.arguments.itervalues():
                    writer.put(', %s' % arg.signature)
            writer.put('):\n')
            writer.add_indent()
            if self.description or self.arguments:
                writer.write('"""')
                if self.description:
                    writer.write(self.description.strip())
                if self.arguments:
                    if self.description:
                        writer.write()
                    for _, arg in self.arguments.iteritems():
                        writer.write(arg.docstring)
                writer.write('"""')
            writer.put_indent()
            if self.implementation:
                self._implementation_str(writer)
            else:
                writer.put('pass')
            return str(writer)

    def _implementation_str(self, writer):
        if self.executor:
            writer.put('self.context.executor(%s).' % repr(self.executor))
        else:
            writer.put('self.context.executor().')
        if '/' in self.implementation:
            writer.put('selc.context.executor().execute(self, %s' % repr(self.implementation))
        else:
            writer.put('%s(self' % self.implementation)
        if self.arguments:
            for arg in self.arguments:
                writer.put(', %s' % arg)
        writer.put(')')
