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

from .exceptions import BadImplementationError
from .code_generator import CodeGenerator
from .prop import CodeProperty
from .assignment import CodeAssignment
from .method import CodeMethod
from .node_template import CodeNodeTemplate
from .relationship import CodeRelationship
from .execution import ExecutionContext
from aria.consumption import Consumer
from inspect import getargspec
import sys

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
            for name, i in self.context.presentation.inputs.iteritems():
                description = getattr(i, 'description', None) # cloudify_dsl
                the_default = getattr(i, 'default', None) # cloudify_dsl
                generator.inputs[name] = CodeProperty(generator, name, description, i.type, the_default)

        if self.context.presentation.outputs:
            for name, output in self.context.presentation.outputs.iteritems():
                generator.outputs[name] = CodeAssignment(generator, name, output.description, output.value)
        
        if self.context.presentation.node_types:
            for name, node_type in self.context.presentation.node_types.iteritems():
                cls = generator.get_class(name)
                if node_type.derived_from:
                    cls.base = node_type.derived_from
                if node_type.description:
                    cls.description = node_type.description
                if node_type.properties:
                    for pname, prop in node_type.properties.iteritems():
                        cls.properties[pname] = CodeProperty(generator, pname, prop.description, prop.type, prop.default)
                if node_type.interfaces:
                    for name, i in node_type.interfaces.iteritems():
                        for oname, operation in i.operations.iteritems():
                            m = CodeMethod(generator, oname, name, getattr(operation, 'description', None), operation.implementation, operation.executor)
                            cls.methods[oname] = m
                            if operation.inputs:
                                for pname, prop in operation.inputs.iteritems():
                                    m.arguments[pname] = CodeProperty(generator, pname, prop.description, prop.type, prop.default)

        if self.context.presentation.data_types:
            for name, data_type in self.context.presentation.data_types.iteritems():
                cls = generator.get_class(name)
                if data_type.derived_from:
                    cls.base = data_type.derived_from
                if data_type.description:
                    cls.description = data_type.description
                if data_type.properties:
                    for pname, prop in data_type.properties.iteritems():
                        cls.properties[pname] = CodeProperty(generator, pname, prop.description, prop.type, prop.default)

        if self.context.presentation.relationship_types:
            for name, relationship_type in self.context.presentation.relationship_types.iteritems():
                cls = generator.get_class(name)
                if relationship_type.derived_from:
                    cls.base = relationship_type.derived_from
                if relationship_type.description:
                    cls.description = relationship_type.description
                if relationship_type.properties:
                    for name, p in relationship_type.properties.iteritems():
                        cls.properties[name] = CodeProperty(generator, name, p.description, p.type, p.default)

        if self.context.presentation.node_templates:
            for name, node_template in self.context.presentation.node_templates.iteritems():
                n = CodeNodeTemplate(generator, name, node_template.type, node_template.description)
                generator.nodes[name] = n
                if node_template.properties:
                    for name, prop in node_template.properties.iteritems():
                        n.assignments[name] = prop.value
                if hasattr(node_template, 'relationships') and node_template.relationships: # cloudify_dsl
                    for relationship in node_template.relationships:
                        n.relationships.append(CodeRelationship(generator, relationship.type, relationship.target))

        if self.context.presentation.workflows:
            for name, operation in self.context.presentation.workflows.iteritems():
                m = CodeMethod(generator, name, None, getattr(operation, 'description', None), operation.mapping, operation.executor if hasattr(operation, 'executor') else None)
                generator.workflows[name] = m
                if operation.parameters:
                    for pname, prop in operation.parameters.iteritems():
                        m.arguments[name] = CodeProperty(generator, pname, prop.description, prop.type, prop.default)
        
        generator.write(self.context.implementation.root)
        
        return generator
        
