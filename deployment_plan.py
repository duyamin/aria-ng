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

from aria.deployment import DeploymentPlan

class CloudifyDeploymentPlan(DeploymentPlan):
    def __init__(self, presentation):
        super(CloudifyDeploymentPlan, self).__init__(presentation)
        
        self.plugins = [self.create_plugin(name, p) for name, p in self.presentation.service_template.plugins.iteritems()] if self.presentation.service_template.plugins else []
        
        self.nodes = [self.create_node(name, n) for name, n in self.presentation.service_template.node_templates.iteritems()] if self.presentation.service_template.node_templates else []

        self.node_instances = []
        if self.presentation.service_template.node_templates:
            for name, node_template in self.presentation.service_template.node_templates.iteritems():
                count = node_template.instances.deploy if (node_template.instances and node_template.instances.deploy is not None) else 1
                for _ in range(count):
                    node_instance = self.create_node_instance(name, node_template)
                    self.node_instances.append(node_instance)

        self.relate_node_instances()
        
        self.workflows = {name: self.create_workflow(name, o) for name, o in self.presentation.service_template.workflows.iteritems()} if self.presentation.service_template.workflows else {}

    def get_node_type(self, node_type_name):
        return self.presentation.service_template.node_types[node_type_name]

    def get_node_template(self, node_name):
        return self.presentation.service_template.node_templates[node_name]

    def get_relationship(self, name):
        return self.presentation.service_template.relationships[name]
    
    def is_contained_relationship(self, the_type):
        if the_type == 'cloudify.relationships.contained_in':
            return True
        relationship = self.get_relationship(the_type)
        if relationship.derived_from:
            return self.is_contained_relationship(relationship.derived_from)
        return False

    def create_node(self, name, node_template):
        node = super(CloudifyDeploymentPlan, self).create_node(name)
        self.append_from_node_type(node, node_template.type)
        self.append_property_values(node['properties'], node_template.properties)
        if node_template.relationships:
            for relationship in node_template.relationships:
                r = self.create_node_relationship(relationship.target)
                self.append_from_relationship_type(r, relationship.type)
                #self.append_property_values(r['properties'], relationship.properties)
                node['relationships'].append(r)
        node['type'] = node_template.type
        return node

    def create_node_instance(self, name, node_template):
        node_instance = super(CloudifyDeploymentPlan, self).create_node_instance(name)
        return node_instance

    def create_workflow(self, name, workflow):
        plugin_name, operation_name = workflow.mapping.split('.', 1) if workflow.mapping else (None, None)
        o = super(CloudifyDeploymentPlan, self).create_operation(plugin_name, operation_name)
        self.append_properties(o['parameters'], workflow.parameters)
        return o

    def create_operation(self, name, operation):
        plugin_name, operation_name = operation.implementation.split('.', 1) if operation.implementation else (None, None)
        o = super(CloudifyDeploymentPlan, self).create_operation(plugin_name, operation_name)
        if operation.executor is not None:
            o['executor'] = operation.executor
        #elif plugin:
        #    o['executor'] = self.presentation.service_template.plugins[plugin].executor
        self.append_properties(o['inputs'], operation.inputs)
        if operation.max_retries is not None:
            o['max_retries'] = operation.max_retries
        if operation.retry_interval is not None:
            o['retry_interval'] = operation.retry_interval
        return o

    def create_plugin(self, name, plugin):
        r = {}
        r['name'] = name
        return r

    def append_properties(self, r, properties):
        if properties:
            for name, p in properties.iteritems():
                r[name] = {}
                r[name]['default'] = p.default
    
    def append_property_values(self, r, properties):
        if properties:
            for name, p in properties.iteritems():
                r[name] = p.value

    def append_operations_from_interfaces(self, r, interfaces):
        if interfaces:
            for interface_name, i in interfaces.iteritems():
                for operation_name, o in i.operations.iteritems():
                    # Seems we need to support both long and short lookup styles?
                    operation = self.create_operation(operation_name, o)
                    r['%s.%s' % (interface_name, operation_name)] = operation
                    r[operation_name] = operation

    def append_from_node_type(self, r, node_type_name):
        r['type_hierarchy'].insert(0, node_type_name)
        node_type = self.get_node_type(node_type_name)
        if node_type.derived_from:
            self.append_from_node_type(r, node_type.derived_from)
        if node_type.properties:
            for property_name, p in node_type.properties.iteritems():
                if p.default is not None:
                    r['properties'][property_name] = p.default
        self.append_operations_from_interfaces(r['operations'], node_type.interfaces)
    
    def append_interfaces(self, r, interfaces):
        # Is this actually used by dsl_parser consumers?
        if interfaces:
            for interface_name, i in interfaces.iteritems():
                r[interface_name] = {}
                for operation_name, o in i.operations.iteritems():
                    r[interface_name][operation_name] = {}
                    r[interface_name][operation_name]['implementation'] = o.implementation
                    r[interface_name][operation_name]['inputs'] = {} # TODO: o.inputs
                    r[interface_name][operation_name]['max_retries'] = o.max_retries
                    r[interface_name][operation_name]['retry_interval'] = o.retry_interval
                    r[interface_name][operation_name]['executor'] = o.executor

    def append_from_relationship_type(self, r, the_type):
        r['type_hierarchy'].insert(0, the_type)
        relationship_type = self.get_relationship(the_type)
        if relationship_type.properties:
            for property_name, p in relationship_type.properties.iteritems():
                if p.default is not None:
                    r['properties'][property_name] = p.default
        if relationship_type.derived_from:
            self.append_from_relationship_type(r, relationship_type.derived_from)
        self.append_operations_from_interfaces(r['source_operations'], relationship_type.source_interfaces)
        self.append_operations_from_interfaces(r['target_operations'], relationship_type.target_interfaces)
        self.append_interfaces(r['source_interfaces'], relationship_type.source_interfaces)
        self.append_interfaces(r['target_interfaces'], relationship_type.target_interfaces)
    
    def relate_node_instances(self):
        for node_instance in self.node_instances:
            node_template = self.get_node_template(node_instance['name'])
            if node_template.relationships:
                relationships = []
                for relationship in node_template.relationships:
                    targets = self.get_node_instances(relationship.target)
                    for target in targets:
                        if self.is_contained_relationship(relationship.type):
                            node_instance['host_id'] = target['id']
                        r = self.create_node_instance_relationship(relationship.type, relationship.target, target['id'])
                        relationships.append(r)
                node_instance['relationships'] = relationships
