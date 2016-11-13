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

from aria.utils import safe_repr

from .writer import Writer


class CodeClass(object):
    def __init__(self, generator, name, module=None, base=None, description=None):
        self.generator = generator
        self.name = name
        self.module = module
        self.base = 'object' if base is None else base
        self.description = description
        self.properties = OrderedDict()
        self.methods = OrderedDict()

    @property
    def fullname(self):
        return '%s.%s' % (self.module.fullname, self.name)

    def make_names_unique(self):
        names = []
        def unique_name(name):
            if name not in names:
                names.append(name)
                return name
            else:
                return unique_name(name + '_')

        for method in self.methods.itervalues():
            method.name = unique_name(method.name)

    def __str__(self):
        self.make_names_unique()

        with Writer() as writer:
            writer.write('@has_validated_properties')
            writer.write('@has_interfaces')
            base = self.base if isinstance(self.base, str) \
                else (self.base.name if self.base.module == self.module else self.base.fullname)
            writer.write('class %s(%s):' % (self.name, base))
            writer.add_indent()
            if self.description:
                writer.write_docstring(self.description)
            writer.write('def __init__(self, context):')
            writer.add_indent()
            writer.write('self.context = context')
            writer.remove_indent()
            for name, property in self.properties.iteritems():
                writer.write()
                if property.default is not None:
                    writer.write('@property_default(%s)' % safe_repr(property.default))
                if property.type:
                    writer.write('@property_type(%s)' % self.generator.get_classname(property.type))
                writer.write('@validated_property')
                writer.write('def %s():' % name)
                writer.add_indent()
                if property.description or property.type is not None:
                    writer.write('"""')
                    if property.description:
                        writer.write(property.description.strip())
                    if property.type is not None:
                        if property.description:
                            writer.write()
                        writer.write(':rtype: :class:`%s`' %
                                     self.generator.get_classname(property.type))
                    writer.write('"""')
                else:
                    writer.write('pass')
                writer.remove_indent()
            for name, method in self.methods.iteritems():
                writer.write()
                writer.write(method)
            return str(writer)
