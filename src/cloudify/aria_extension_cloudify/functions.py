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

from aria import InvalidValueError
from aria.utils import deepcopy_with_locators, safe_repr

class FunctionContext(object):
    def __init__(self, context, get_node_instances_method, get_node_instance_method, get_node_method):
        self.self_node_id = context.get('self')
        self.source_node_id = context.get('source')
        self.target_node_id = context.get('target')
        self.get_nodes = get_node_instances_method
        self.get_node = get_node_instance_method
        self.get_node_template = get_node_method

class GetInput(object):
    def __init__(self, value):
        self.input_property_name = value
    
    def evaluate(self, context):
        inputs = self.context.modeling.classic_deployment_plan['inputs']
        if self.input_property_name not in inputs:
            raise InvalidValueError('input does not exist for function "get_input": %s' % safe_repr(self.input_property_name), locator=self.locator)
        return deepcopy_with_locators(inputs[self.input_property_name])

class GetProperty(object):
    def __init__(self, value):
        self.modelable_entity_name = value[0]
        self.nested_property_name_or_index = value[1:]

    def evaluate(self, context):
        _, node_template = get_node(context, self.modelable_entity_name, 'get_property')
        return get_property(node_template['properties'], self.nested_property_name_or_index, 'get_property')

class GetAttribute(object):
    def __init__(self, value):
        self.modelable_entity_name = value[0]
        self.nested_property_name_or_index = value[1:]

    def evaluate(self, context):
        node, node_template = get_node(context, self.modelable_entity_name, 'get_attribute')

        try:
            return get_property(node['runtime_properties'], self.nested_property_name_or_index, 'get_attribute')
        except InvalidValueError:
            return get_property(node_template['properties'], self.nested_property_name_or_index, 'get_attribute')

class Concat(object):
    def __init__(self, value):
        pass

    def evaluate(self, context):
        return '123'

FUNCTIONS = {
    'get_input': GetInput,
    'get_property': GetProperty,
    'get_attribute': GetAttribute,
    'concat': Concat}

def get_function(value):
    if isinstance(value, dict) and (len(value) == 1):
        key = value.keys()[0]
        if key in FUNCTIONS:
            return FUNCTIONS[key](value[key])
    return None

#
# Utils
#

def get_node(function_context, modelable_entity_name, function_name):
    node = None
    
    def get_node(node_id):
        try:
            return function_context.get_node(node_id)
        except Exception as e:
            raise InvalidValueError('function "%s" refers to an unknown node: %s' % (function_name, safe_repr(node_id)), cause=e)

    if modelable_entity_name == 'SELF':
        node = get_node(function_context.self_node_id)
    elif modelable_entity_name == 'SOURCE':
        node = get_node(function_context.source_node_id)
    elif modelable_entity_name == 'TARGET':
        node = get_node(function_context.target_node_id)
    else:
        try:
            nodes = function_context.get_nodes(modelable_entity_name)
            node = nodes[0]
        except Exception as e:
            raise InvalidValueError('function "%s" refers to an unknown modelable entity: %s' % (function_name, safe_repr(modelable_entity_name)), cause=e)
    
    node_template = function_context.get_node_template(node['node_id'])
    
    return node, node_template

def get_property(value, nested_property_name_or_index, function_name):
    for name_or_index in nested_property_name_or_index:
        try:
            value = value[name_or_index]
        except KeyError as e:
            raise InvalidValueError('function "%s" refers to an unknown nested property name: %s' % (function_name, safe_repr(name_or_index)), cause=e)
        except IndexError as e:
            raise InvalidValueError('function "%s" refers to an unknown nested index: %s' % (function_name, safe_repr(name_or_index)), cause=e)
    return value
