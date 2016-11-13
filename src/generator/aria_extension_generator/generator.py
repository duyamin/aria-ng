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


import sys
from inspect import getargspec

from aria.consumption import Consumer

from .prop import CodeProperty
from .method import CodeMethod
from .assignment import CodeAssignment
from .execution import ExecutionContext
from .code_generator import CodeGenerator
from .relationship import CodeRelationship
from .node_template import CodeNodeTemplate
from .exceptions import BadImplementationError


class Generator(Consumer):
    """
    ARIA generator.

    Creates Python classes for the presentation.
    """

    def consume(self):
        self.implement()
        self.service.context.dump()

    @property
    def service(self):
        """
        Gets the implemented service instance.

        For this to work, the service source code must have been generated. The Python
        runtime will then load this code by compiling it.
        """
        sys.path.append(self.context.implementation.root)
        try:
            from service import Service # @UnresolvedImport
            args = len(getargspec(Service.__init__).args) - 2
        except Exception as e:
            raise BadImplementationError('service code could not be compiled', cause=e)
        try:
            context = ExecutionContext(self.context.style)
            service = Service(context, *([None] * args))
            return service
        except Exception as e:
            raise BadImplementationError('Service class could not be instantiated', cause=e)

    def implement(self):
        generator = CodeGenerator()

        generator.description = self.context.presentation.service_template.description

        if self.context.presentation.inputs:
            self._handle_inputs(generator)

        if self.context.presentation.outputs:
            self._handle_outputs(generator)

        if self.context.presentation.node_types:
            self._handle_node_types(generator)

        if self.context.presentation.data_types:
            self._handle_data_types(generator)

        if self.context.presentation.relationship_types:
            self._handle_relationship_types(generator)

        if self.context.presentation.node_templates:
            self._handle_node_templates(generator)

        if self.context.presentation.workflows:
            self._handle_workflows(generator)

        generator.write(self.context.implementation.root)

        return generator

    def _handle_inputs(self, generator):
        for name, i in self.context.presentation.inputs.iteritems():
            description = getattr(i, 'description', None)  # cloudify_dsl
            the_default = getattr(i, 'default', None)  # cloudify_dsl
            generator.inputs[name] = CodeProperty(generator, name, description, i.type,
                                                  the_default)

    def _handle_outputs(self, generator):
        for name, output in self.context.presentation.outputs.iteritems():
            generator.outputs[name] = CodeAssignment(generator, name, output.description,
                                                     output.value)

    def _handle_node_types(self, generator):
        for name, node_type in self.context.presentation.node_types.iteritems():
            cls = generator.get_class(name)
            if node_type.derived_from:
                cls.base = node_type.derived_from
            if node_type.description:
                cls.description = node_type.description
            if node_type.properties:
                for pname, property in node_type.properties.iteritems():
                    cls.properties[pname] = CodeProperty(generator, pname, property.description,
                                                         property.type, property.default)
            if node_type.interfaces:
                for name, i in node_type.interfaces.iteritems():
                    for oname, operation in i.operations.iteritems():
                        method = CodeMethod(generator,
                                            oname,
                                            name,
                                            getattr(operation, 'description', None),
                                            operation.implementation,
                                            operation.executor)
                        cls.methods[oname] = method
                        if operation.inputs:
                            for pname, property in operation.inputs.iteritems():
                                method.arguments[pname] = CodeProperty(
                                    generator,
                                    pname,
                                    property.description,
                                    property.type,
                                    property.default)

    def _handle_data_types(self, generator):
        for name, data_type in self.context.presentation.data_types.iteritems():
            cls = generator.get_class(name)
            if data_type.derived_from:
                cls.base = data_type.derived_from
            if data_type.description:
                cls.description = data_type.description
            if data_type.properties:
                for pname, property in data_type.properties.iteritems():
                    cls.properties[pname] = CodeProperty(generator, pname, property.description,
                                                         property.type, property.default)

    def _handle_node_templates(self, generator):
        for name, node_template in self.context.presentation.node_templates.iteritems():
            node = CodeNodeTemplate(generator, name, node_template.type,
                                    node_template.description)
            generator.nodes[name] = node
            if node_template.properties:
                for name, property in node_template.properties.iteritems():
                    node.assignments[name] = property.value
            # cloudify_dsl
            if hasattr(node_template, 'relationships') and node_template.relationships:
                for relationship in node_template.relationships:
                    node.relationships.append(
                        CodeRelationship(generator, relationship.type, relationship.target))

    def _handle_relationship_types(self, generator):
        for name, rel_type in self.context.presentation.relationship_types.iteritems():
            cls = generator.get_class(name)
            if rel_type.derived_from:
                cls.base = rel_type.derived_from
            if rel_type.description:
                cls.description = rel_type.description
            if rel_type.properties:
                for name, property in rel_type.properties.iteritems():
                    cls.properties[name] = CodeProperty(generator, name, property.description,
                                                        property.type, property.default)

    def _handle_workflows(self, generator):
        for name, operation in self.context.presentation.workflows.iteritems():
            method = CodeMethod(
                generator,
                name,
                None,
                getattr(operation, 'description', None),
                operation.mapping,
                operation.executor if hasattr(operation, 'executor') else None)
            generator.workflows[name] = method
            if operation.parameters:
                for pname, property in operation.parameters.iteritems():
                    method.arguments[name] = CodeProperty(
                        generator, pname, property.description, property.type,
                        property.default)
