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

from .module import CodeModule
from .writer import Writer, create_header, repr_assignment


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
            cls_name = self.translate_classes[name]
            return cls_name if isinstance(cls_name, str) else cls_name.fullname
        return name

    def link_classes(self):
        for class_ in self.module.all_classes:
            if isinstance(class_.base, str):
                base_class = self.get_class(class_.base, False)
                if base_class:
                    class_.base = base_class
        for class_ in self.module.all_classes:
            if not class_.module.name:
                del class_.module.classes[class_.name]
                root = self.module.get_module(self.common_module_name)
                class_.module = root
                root.classes[class_.name] = class_
                self.translate_classes[class_.name] = class_

    @staticmethod
    def write_file(the_file, content):
        try:
            os.makedirs(os.path.dirname(the_file))
        except OSError as e:
            if e.errno != 17:
                raise e
        with open(the_file, 'w') as f:
            f.write(str(content))

    def write(self, root):
        self.link_classes()
        for module in self.module.all_modules:
            if module.name:
                the_file = os.path.join(root, module.file)
                self.write_file(the_file, module)
        the_file = os.path.join(root, 'service.py')
        self.write_file(the_file, self.service)

    @property
    def service(self):
        with Writer() as writer:
            writer.write(create_header())
            for module in self.module.all_modules:
                if module.fullname:
                    writer.write('import %s' % module.fullname)
            writer.write()
            writer.write('class Service(object):')
            writer.add_indent()
            if self.description or self.inputs:
                self._handle_description_and_inputs(writer)
            if self.inputs or self.outputs or self.nodes or self.workflows:
                self._handle_metadata(writer)
            writer.put_indent()
            writer.put('def __init__(self, context')
            if self.inputs:
                for i in self.inputs.itervalues():
                    writer.put(', %s' % i.signature)
            writer.put('):\n')
            writer.add_indent()
            writer.write('self.context = context')
            writer.write('self.context.service = self')
            if self.inputs:
                writer.write()
                writer.write('# Inputs')
                for i in self.inputs:
                    writer.write('self.%s = %s' % (i, i))
            if self.nodes:
                self._handle_nodes(writer)
            writer.remove_indent()
            if self.outputs:
                self._handle_outputs(writer)
            if self.workflows:
                self._handle_workflows(writer)
            return str(writer)

    def _handle_description_and_inputs(self, writer):
        writer.write('"""')
        if self.description:
            writer.write(self.description.strip())
        if self.inputs:
            if self.description:
                writer.write()
            for i in self.inputs.itervalues():
                writer.write(i.docstring)
        writer.write('"""')

    def _handle_metadata(self, writer):
        writer.write()
        writer.write('# Metadata')
        if self.inputs:
            writer.write('INPUTS = %s' % safe_repr(tuple(self.inputs.keys())))
        if self.outputs:
            writer.write('OUTPUTS = %s' % safe_repr(tuple(self.outputs.keys())))
        if self.nodes:
            writer.write('NODES = %s' % safe_repr(tuple(self.nodes.keys())))
        if self.workflows:
            writer.write('WORKFLOWS = %s' % safe_repr(tuple(self.workflows.keys())))
        writer.write()

    def _handle_nodes(self, writer):
        writer.write()
        for node in self.nodes.itervalues():
            writer.write(node.description or 'Node: %s' % node.name, prefix='# ')
            writer.write(node)
        has_relationships = False
        for node in self.nodes.itervalues():
            if node.relationships:
                has_relationships = True
                break
        if has_relationships:
            writer.write('# Relationships')
            for node in self.nodes.itervalues():
                node.relate(writer)

    def _handle_outputs(self, writer):
        writer.write()
        writer.write('# Outputs')
        for output in self.outputs.itervalues():
            writer.write()
            writer.write('@property')
            writer.write('def %s(self):' % output.name)
            writer.add_indent()
            if output.description:
                writer.write_docstring(output.description)
            writer.write('return %s' % repr_assignment(output.value))
            writer.remove_indent()

    def _handle_workflows(self, writer):
        writer.write()
        writer.write('# Workflows')
        for workflow in self.workflows.itervalues():
            writer.write()
            writer.write(str(workflow))
