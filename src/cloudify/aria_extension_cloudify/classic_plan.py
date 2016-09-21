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
from aria.consumption import Consumer
from aria.deployment import Parameter, Function
from aria.utils import as_raw, as_agnostic, merge, prune, json_dumps
from collections import OrderedDict
import os
from aria.utils.collections import deepcopy_with_locators

COMPUTE_NODE_NAME = 'cloudify.nodes.Compute'
CONTAINED_IN_RELATIONSHIP_NAME = 'cloudify.relationships.contained_in'
SCALING_POLICY_NAME = 'cloudify.policies.scaling'
SCRIPT_RUNNER_RUN_OPERATION = 'script_runner.tasks.run'
SCRIPT_RUNNER_EXECUTE_WORKFLOW_OPERATION = 'script_runner.tasks.execute_workflow'
CENTRAL_DEPLOYMENT_AGENT = 'central_deployment_agent'
HOST_AGENT = 'host_agent'

class ClassicPlan(Consumer):
    """
    Generates the classic deployment plan based on the standard deployment plan.
    """

    def consume(self):
        if self.context.deployment.plan is None:
            self.context.validation.report('ClassicPlan consumer: missing deployment plan')
            return

        plugins = self.context.presentation.presenter.service_template.plugins
        plugins = [convert_plugin(self.context, v) for v in plugins.itervalues()] if plugins is not None else []
        setattr(self.context.deployment, 'plugins', plugins)

        classic_plan = convert_plan(self.context)
        setattr(self.context.deployment, 'classic_plan_ordered', classic_plan) # ordered version
        setattr(self.context.deployment, 'classic_plan', as_agnostic(classic_plan)) # agnostic version (does not maintain dict order)
    
    def dump(self):
        indent = self.context.get_arg_value_int('indent', 2)
        self.context.write(json_dumps(self.context.deployment.classic_plan, indent=indent))

#
# Conversions
#

def convert_plan(context):
    r = OrderedDict((
        # General
        ('version', convert_version(context)),
        ('description', context.deployment.plan.description),
        ('inputs', convert_properties(context, context.deployment.plan.inputs)),
        ('outputs', convert_properties(context, context.deployment.plan.outputs)),
        ('workflows', OrderedDict(
            (k, convert_workflow(context, v)) for k, v in context.deployment.plan.operations.iteritems())),
        ('deployment_plugins_to_install', []),
        ('workflow_plugins_to_install', plugins_to_install_for_operations(context, context.deployment.plan.operations, CENTRAL_DEPLOYMENT_AGENT)),

        # Instances
        ('node_instances', [convert_node(context, v) for v in context.deployment.plan.nodes.itervalues()]),

        # Templates
        ('nodes', [convert_node_template(context, v) for v in context.deployment.template.node_templates.itervalues()]),
        ('groups', OrderedDict(
            (k, convert_group_template(context, v)) for k, v in context.deployment.template.group_templates.iteritems())),
        ('scaling_groups', OrderedDict(
            (k, convert_group_template(context, v, policy_template)) for k, v, policy_template in iter_scaling_groups(context))),
        ('policies', OrderedDict(
            (k, convert_policy_template(context, v)) for k, v in context.deployment.template.policy_templates.iteritems())),

        # Types
        ('policy_types', OrderedDict(
            (v.name, convert_policy_type(context, v)) for v in context.deployment.policy_types.iter_descendants())),
        ('policy_triggers', OrderedDict(
            (v.name, convert_policy_trigger_type(context, v)) for v in context.deployment.policy_trigger_types.iter_descendants())),
        ('relationships', OrderedDict(
            (v.name, convert_relationship_type(context, v)) for v in context.deployment.relationship_types.iter_descendants()))))

    # Aggregate deployment_plugins_to_install from nodes
    for node in r['nodes']:
        node_deployment_plugins_to_install = node.get('deployment_plugins_to_install')
        if node_deployment_plugins_to_install:
            for plugin in node_deployment_plugins_to_install:
                exists = False
                for p in r['deployment_plugins_to_install']:
                    if p['name'] == plugin['name']:
                        exists = True
                        break
                if not exists:
                    r['deployment_plugins_to_install'].append(plugin)
    
    # Some code needs to access these as Python attributes
    setattr(r, 'version', r['version'])
    setattr(r['version'], 'definitions_name', r['version']['definitions_name'])
    setattr(r['version'], 'definitions_version', r['version']['definitions_version'])
    setattr(r['version']['definitions_version'], 'number', r['version']['definitions_version']['number'])
    setattr(r, 'inputs', r['inputs'])
    setattr(r, 'outputs', r['outputs'])
    setattr(r, 'node_templates', r['nodes'])
    
    return r

#
# General
#

def convert_version(context):
    number = context.presentation.presenter.service_template.tosca_definitions_version
    number = number[len('cloudify_dsl_'):]
    number = number.split('_')
    number = tuple(int(v) for v in number)

    return OrderedDict((
        ('definitions_name', 'cloudify_dsl'),
        ('definitions_version', OrderedDict((
            ('number', number),)))))

def convert_plugin(context, plugin):
    return OrderedDict((
        ('name', plugin._name),
        ('distribution', getattr(plugin, 'distribution', None)),
        ('distribution_release', getattr(plugin, 'distribution_release', None)),
        ('distribution_version', getattr(plugin, 'distribution_version', None)),
        ('executor', plugin.executor),
        ('install', plugin.install),
        ('install_arguments', getattr(plugin, 'install_arguments', None)),
        ('package_name', getattr(plugin, 'package_name', None)),
        ('package_version', getattr(plugin, 'package_version', None)),
        ('source', plugin.source),
        ('supported_platform', getattr(plugin, 'supported_platform', None))))

def convert_workflow(context, operation):
    plugin_name, _, operation_name, inputs = parse_implementation(context, operation.implementation, True)

    r = OrderedDict((
        ('plugin', plugin_name),
        ('operation', operation_name),
        ('parameters', merge(convert_parameters(context, operation.inputs), inputs)),
        ('has_intrinsic_functions', has_intrinsic_functions(context, operation.inputs)),
        ('executor', operation.executor),
        ('max_retries', operation.max_retries),
        ('retry_interval', operation.retry_interval)))

    return r

#
# Instances
#

def convert_node(context, node):
    host_node = find_host_node(context, node)
    groups = find_groups(context, node)

    return OrderedDict((
        ('id', node.id),
        ('name', node.template_name),
        ('host_id', host_node.id if host_node is not None else None),
        ('relationships', [convert_relationship(context, v) for v in node.relationships]),
        ('scaling_groups', [OrderedDict((('name', group.template_name),)) for group in groups])))

def convert_relationship(context, relationship):
    target_node = context.deployment.plan.nodes.get(relationship.target_node_id)
    
    return OrderedDict((
        ('type', relationship.type_name), # template_name?
        ('target_id', relationship.target_node_id),
        ('target_name', target_node.template_name)))

#
# Templates
#

def convert_node_template(context, node_template):
    node_type = context.deployment.node_types.get_descendant(node_template.type_name)
    host_node_template = find_host_node_template(context, node_template)
    is_host = is_host_node_template(context, node_template)
    
    current_instances = 0
    for node in context.deployment.plan.nodes.itervalues():
        if node.template_name == node_template.name:
            current_instances += 1

    plugins_to_install = [] if is_host else None
    deployment_plugins_to_install = []
    add_plugins_to_install_for_interface(context, plugins_to_install, node_template.interfaces, HOST_AGENT)
    add_plugins_to_install_for_interface(context, deployment_plugins_to_install, node_template.interfaces, CENTRAL_DEPLOYMENT_AGENT)
    
    relationships = []
    for requirement in node_template.requirements:
        if requirement.relationship_template is not None:
            relationships.append(convert_relationship_template(context, requirement, plugins_to_install, deployment_plugins_to_install))

    r = OrderedDict((
        ('name', node_template.name),
        ('id', node_template.name),
        ('type', node_type.name),
        ('type_hierarchy', convert_type_hierarchy(context, node_type, context.deployment.node_types)),
        ('host_id', host_node_template.name if host_node_template is not None else None),
        ('properties', convert_properties(context, node_template.properties)),
        ('operations', convert_operations(context, node_template.interfaces)),
        ('relationships', relationships),
        ('plugins', context.deployment.plugins),
        ('plugins_to_install', plugins_to_install),
        ('deployment_plugins_to_install', deployment_plugins_to_install),
        ('capabilities', OrderedDict((
            ('scalable', OrderedDict((
                ('properties', OrderedDict((
                    ('current_instances', current_instances),
                    ('default_instances', node_template.default_instances),
                    ('min_instances', node_template.min_instances),
                    ('max_instances', node_template.max_instances if node_template.max_instances is not None else -1)))),))),)))))
    
    if r['host_id'] is None:
        del r['host_id']
    
    if not is_host:
        del r['plugins_to_install']
        
    return r

def convert_relationship_template(context, requirement, plugins_to_install, deployment_plugins_to_install):
    relationship_template = requirement.relationship_template
    relationship_type = context.deployment.relationship_types.get_descendant(relationship_template.type_name)

    add_plugins_to_install_for_interface(context, plugins_to_install, relationship_template.source_interfaces, HOST_AGENT)
    add_plugins_to_install_for_interface(context, plugins_to_install, relationship_template.target_interfaces, HOST_AGENT)
    add_plugins_to_install_for_interface(context, deployment_plugins_to_install, relationship_template.source_interfaces, CENTRAL_DEPLOYMENT_AGENT)
    add_plugins_to_install_for_interface(context, deployment_plugins_to_install, relationship_template.target_interfaces, CENTRAL_DEPLOYMENT_AGENT)
    
    return OrderedDict((
        ('type', relationship_type.name),
        ('type_hierarchy', convert_type_hierarchy(context, relationship_type, context.deployment.relationship_types)),
        ('target_id', requirement.target_node_template_name),
        ('properties', convert_properties(context, relationship_template.properties)),
        ('source_interfaces', convert_interfaces(context, relationship_template.source_interfaces)),
        ('target_interfaces', convert_interfaces(context, relationship_template.target_interfaces)),
        ('source_operations', convert_operations(context, relationship_template.source_interfaces)), 
        ('target_operations', convert_operations(context, relationship_template.target_interfaces))))

def convert_group_template(context, group_template, policy_template=None):
    r = OrderedDict((
        ('members', group_template.member_node_template_names),
        ('policies', OrderedDict(
            (k, convert_group_policy(context, v)) for k, v in group_template.policies.iteritems()))))

    if policy_template is not None:
        r['properties'] = convert_properties(context, policy_template.properties)

    return r

def convert_group_policy(context, group_policy):
    return OrderedDict((
        ('type', group_policy.type_name),
        ('properties', convert_properties(context, group_policy.properties))))

def convert_policy_template(context, policy_template):
    return OrderedDict((
        ('properties', convert_properties(context, policy_template.properties)),))

#
# Types
#

def convert_policy_type(context, policy_type):
    return OrderedDict((
        ('source', policy_type.implementation),
        ('properties', convert_parameters(context, policy_type.properties))))

def convert_policy_trigger_type(context, policy_trigger_type):
    return OrderedDict((
        ('source', policy_trigger_type.implementation),
        ('parameters', convert_parameters(context, policy_trigger_type.properties))))

def convert_relationship_type(context, relationship_type):
    r = OrderedDict((
        ('name', relationship_type.name),
        ('derived_from', get_type_parent_name(relationship_type, context.deployment.relationship_types)),
        ('type_hierarchy', convert_type_hierarchy(context, relationship_type, context.deployment.relationship_types)),
        ('properties', convert_parameters(context, relationship_type.properties)),
        ('source_interfaces', convert_interfaces(context, relationship_type.source_interfaces)),
        ('target_interfaces', convert_interfaces(context, relationship_type.target_interfaces))))
    
    if r['derived_from'] is None:
        del r['derived_from']
    
    return r

#
# Misc
#

def convert_properties(context, properties):
    return OrderedDict((
        (k, as_raw(v.value)) for k, v in properties.iteritems()))

def convert_parameters(context, parameters):
    return OrderedDict((
        (k, convert_parameter(context, v)) for k, v in parameters.iteritems()))

def convert_parameter(context, parameter):
    # prune removes any None (but not NULL), and then as_raw converts any NULL to None
    return as_raw(prune(OrderedDict((
        ('type', parameter.type_name),
        ('default', parameter.value),
        ('description', parameter.description)))))

def convert_interfaces(context, interfaces):
    r = OrderedDict()

    for interface_name, interface in interfaces.iteritems():
        rr = OrderedDict()
        for operation_name, operation in interface.operations.iteritems():
            rr[operation_name] = convert_interface_operation(context, operation)
        r[interface_name] = rr
    
    return r

def convert_interface_operation(context, operation):
    _, plugin_executor, _, _ = parse_implementation(context, operation.implementation)

    return OrderedDict((
        ('implementation', operation.implementation or ''),
        ('inputs', convert_inputs(context, operation.inputs)),
        ('executor', operation.executor or plugin_executor),
        ('max_retries', operation.max_retries),
        ('retry_interval', operation.retry_interval)))

def convert_operations(context, interfaces):
    r = OrderedDict()
    
    duplicate_operation_names = set()
    for interface_name, interface in interfaces.iteritems():
        for operation_name, operation in interface.operations.iteritems():
            operation = convert_operation(context, operation)
            r['%s.%s' % (interface_name, operation_name)] = operation
            if operation_name not in r:
                r[operation_name] = operation
            else:
                duplicate_operation_names.add(operation_name)

    # If the short form is not unique, then we should not have it at all 
    for operation_name in duplicate_operation_names:
        del r[operation_name]
            
    return r

def convert_operation(context, operation):
    plugin_name, plugin_executor, operation_name, inputs = parse_implementation(context, operation.implementation)

    return OrderedDict((
        ('plugin', plugin_name),
        ('operation', operation_name),
        ('inputs', merge(convert_inputs(context, operation.inputs), inputs)),
        ('has_intrinsic_functions', has_intrinsic_functions(context, operation.inputs)),
        ('executor', operation.executor or plugin_executor),
        ('max_retries', operation.max_retries),
        ('retry_interval', operation.retry_interval)))

def convert_inputs(context, inputs):
    return OrderedDict((
        (k, as_raw(v.value)) for k, v in inputs.iteritems()))

def convert_type_hierarchy(context, the_type, hierarchy):
    type_hierarchy = []
    while (the_type is not None) and (the_type.name is not None):
        type_hierarchy.insert(0, the_type.name)
        the_type = hierarchy.get_parent(the_type.name)
    return type_hierarchy

#
# Utils
#

def parse_implementation(context, implementation, is_workflow=False):
    parsed = False

    if not implementation:
        plugin_name = None
        plugin_executor = None
        operation_name = None
        inputs = OrderedDict()
        parsed = True
    
    if not parsed:
        for search_path in context.loading.search_paths:
            path = os.path.join(search_path, implementation)
            if os.path.isfile(path):
                # Explicit script
                plugin = find_plugin(context)
                plugin_name = plugin['name'] 
                plugin_executor = plugin['executor']
                if is_workflow:
                    operation_name = SCRIPT_RUNNER_EXECUTE_WORKFLOW_OPERATION
                    inputs = OrderedDict((
                        ('script_path', OrderedDict((('default', implementation),))),)) 
                else:
                    operation_name = SCRIPT_RUNNER_RUN_OPERATION
                    inputs = OrderedDict((('script_path', implementation),))
                parsed = True
                break

    if not parsed:
        # plugin.operation
        plugin_name, operation_name = implementation.split('.', 1)
        plugin = find_plugin(context, plugin_name)
        plugin_executor = plugin['executor']
        inputs = OrderedDict()

    return plugin_name, plugin_executor, operation_name, inputs

def has_intrinsic_functions(context, value):
    if isinstance(value, Parameter):
        value = value.value

    if isinstance(value, Function):
        return True
    elif isinstance(value, dict):
        for v in value.itervalues():
            if has_intrinsic_functions(context, v):
                return True
    elif isinstance(value, list):
        for v in value:
            if has_intrinsic_functions(context, v):
                return True
    return False

def add_plugins_to_install_for_interface(context, plugins_to_install, interfaces, agent):
    if plugins_to_install is None:
        return
    
    def has_plugin(name):
        for plugin in plugins_to_install:
            if plugin['name'] == name:
                return True
        return False
    
    for interface in interfaces.itervalues():
        for operation in interface.operations.itervalues():
            plugin_name, plugin_executor, _, _ = parse_implementation(context, operation.implementation)
            executor = operation.executor or plugin_executor
            if executor == agent:
                if not has_plugin(plugin_name): 
                    plugins_to_install.append(find_plugin(context, plugin_name))

def plugins_to_install_for_operations(context, operations, agent):
    install = []
    for operation in operations.itervalues():
        plugin_name, plugin_executor, _, _ = parse_implementation(context, operation.implementation)
        executor = operation.executor or plugin_executor
        if executor == agent:
            if plugin_name not in install: 
                install.append(plugin_name)
    return [find_plugin(context, v) for v in install]

def get_type_parent_name(the_type, hierarchy):
    the_type = hierarchy.get_parent(the_type.name)
    return the_type.name if the_type is not None else None

def find_plugin(context, name=None):
    for plugin in context.deployment.plugins:
        if name is None:
            return plugin
        elif plugin['name'] == name:
            return plugin
    raise InvalidValueError('unknown plugin: %s' % name)

def is_host_node_template(context, node_template):
    return context.deployment.node_types.is_descendant(COMPUTE_NODE_NAME, node_template.type_name)

def find_host_node_template(context, node_template):
    if is_host_node_template(context, node_template):
        return node_template
    
    for requirement in node_template.requirements:
        relationship_template = requirement.relationship_template
        if relationship_template is not None:
            if context.deployment.relationship_types.is_descendant(CONTAINED_IN_RELATIONSHIP_NAME, relationship_template.type_name):
                return find_host_node_template(context, context.deployment.template.node_templates.get(requirement.target_node_template_name))

    return None

def find_host_node(context, node):
    node_template = context.deployment.template.node_templates.get(node.template_name)
    if context.deployment.node_types.is_descendant(COMPUTE_NODE_NAME, node_template.type_name):
        return node
    
    for relationship in node.relationships:
        if context.deployment.relationship_types.is_descendant(CONTAINED_IN_RELATIONSHIP_NAME, relationship.type_name):
            return find_host_node(context, context.deployment.plan.nodes.get(relationship.target_node_id))

    return None

def find_groups(context, node):
    groups = []
    for group in context.deployment.plan.groups.itervalues():
        if node.id in group.member_node_ids:
            groups.append(group)
    return groups

def iter_scaling_groups(context):
    for policy_template in context.deployment.template.policy_templates.itervalues():
        if policy_template.type_name == SCALING_POLICY_NAME:
            for group_template_name in policy_template.target_group_template_names:
                group_template = context.deployment.template.group_templates[group_template_name]
                yield group_template_name, group_template, policy_template
