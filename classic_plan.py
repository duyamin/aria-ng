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

class ClassicDeploymentPlan(object):
    """
    
    """
    
    def __init__(self, presentation):
        self.presentation = presentation
        self.nodes = [] # see: create_node
        self.node_instances = [] # see: create_node_instance
        self.workflows = {} # see: create_operation
        self.plugins = [] # strings

    def get_node_instances(self, node_name):
        node_instances = []
        for node_instance in self.node_instances:
            if node_instance['name'] == node_name:
                node_instances.append(node_instance)
        return node_instances
    
    @property
    def as_dict(self):
        return {
            'nodes': self.nodes,
            'node_instances': self.node_instances,
            'workflows': self.workflows}

    def create_node(self, node_name):
        return {
            'id': node_name,
            'properties': {},
            'operations': {}, # see: create_operation
            'type_hierarchy': [], # strings
            'relationships': [], # see: create_node_relationship
            'plugins': self.plugins, # strings
            'type': None, # string
            'capabilities': {
                'scalable': {
                    'properties': {
                        'current_instances': 1,
                        'default_instances': None,
                        'min_instances': None,
                        'max_instances': None}}}}
        # See: cloudify_rest_client/nodes.py
        #'deployment_id'] =
        #'blueprint_id'] =
        #'number_of_instances': 1
        #'planned_number_of_instances': 1
        #'deploy_number_of_instances': 1
        #'host_id': None} 

    def create_node_relationship(self, target_node_name):
        return {
            'target_id': target_node_name,
            'source_operations': {}, # see: create_operation 
            'target_operations': {}, # see: create_operation
            'source_interfaces': {},
            'target_interfaces': {},
            'type_hierarchy': [], # strings
            'properties': {}}

    def create_node_instance(self, node_name):
        id = generate_id()
        return {
            'name': node_name, # string
            'id': '%s_%s' % (node_name, id), # unique string
            'relationships': []} # create_node_instance_relationship
        # See: cloudify_rest_client/node_instances.py
        #'node_id': id
        #'host_id'] =
        #'deployment_id'] =
        #'runtime_properties': {}
        #'state'] =
        #'version'] =

    def create_node_instance_relationship(self, relationship_type, target_node_name, target_node_instance_id):
        return {
            'type': relationship_type,
            'target_name': target_node_name,
            'target_id': target_node_instance_id}

    def create_operation(self, plugin_name, operation_name):
        return {
            'plugin': plugin_name,
            'operation': operation_name,
            'parameters': {},
            'has_intrinsic_functions': False,
            'executor': None,
            'inputs': {},
            'max_retries': 1,
            'retry_interval': 1}
        # Note: the default 1 is required for TestExecuteOperationWorkflow.test_execute_operation_with_dependency_order
