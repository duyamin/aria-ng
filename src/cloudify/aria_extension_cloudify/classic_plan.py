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

from aria.consumption import Consumer
from aria.deployment import Parameter, Function
from aria.utils import JsonAsRawEncoder, as_raw, as_agnostic, prune
from collections import OrderedDict
import json

COMPUTE_NODE_NAME = 'cloudify.nodes.Compute'
CONTAINED_IN_RELATIONSHIP_NAME = 'cloudify.relationships.contained_in'
SCALING_POLICY_NAME = 'cloudify.policies.scaling'

class ClassicPlan(Consumer):
    """
    Generates the classic deployment plan based on the standard deployment plan.
    """

    def consume(self):
        if self.context.deployment.plan is None:
            self.context.validation.report('ClassicPlan consumer: missing deployment plan')
            return

        classic_plan = convert_plan(self.context)
        setattr(self.context.deployment, 'classic_plan_ordered', classic_plan)
        setattr(self.context.deployment, 'classic_plan', as_agnostic(classic_plan))
    
    def dump(self):
        self.context.write(json.dumps(self.context.deployment.classic_plan, indent=2, cls=JsonAsRawEncoder))

#
# Conversions
#

def convert_plan(context):
    plugins = context.presentation.presenter.service_template.plugins
    plugins = [convert_plugin(context, v) for v in plugins.itervalues()] if plugins is not None else []

    r = OrderedDict((
        ('version', convert_version(context)),
        ('description', context.deployment.plan.description),
        ('inputs', convert_properties(context, context.deployment.plan.inputs)),
        ('outputs', convert_properties(context, context.deployment.plan.outputs)),
        ('nodes', [convert_node_template(context, v, plugins) for v in context.deployment.template.node_templates.itervalues()]),
        ('node_instances', [convert_node(context, v) for v in context.deployment.plan.nodes.itervalues()]),
        ('groups', OrderedDict(
            (k, convert_group_template(context, v)) for k, v in context.deployment.template.group_templates.iteritems())),
        ('scaling_groups', OrderedDict(
            (k, convert_group_template(context, v)) for k, v in iter_scaling_groups(context))),
        ('policies', OrderedDict()), # TODO
        ('policy_triggers', OrderedDict()), # TODO
        ('policy_types', OrderedDict(
            (v.name, convert_policy_type(context, v)) for v in context.deployment.policy_types.iter_descendants())),
        ('workflows', OrderedDict(
            (k, convert_workflow(context, v)) for k, v in context.deployment.plan.operations.iteritems())),
        ('workflow_plugins_to_install', plugins_to_install_for_operations(context, context.deployment.plan.operations, plugins, 'central_deployment_agent')),
        ('relationships', OrderedDict(
            (v.name, convert_relationship_type(context, v)) for v in context.deployment.relationship_types.iter_descendants()))))
        
    setattr(r, 'version', r['version'])
    setattr(r['version'], 'definitions_name', r['version']['definitions_name'])
    setattr(r['version'], 'definitions_version', r['version']['definitions_version'])
    setattr(r['version']['definitions_version'], 'number', r['version']['definitions_version']['number'])
    setattr(r, 'inputs', r['inputs'])
    setattr(r, 'outputs', r['outputs'])
    setattr(r, 'node_templates', r['nodes'])
    
    return r

def convert_version(context):
    number = context.presentation.presenter.service_template.tosca_definitions_version
    number = number[len('cloudify_dsl_'):]
    number = number.split('_')
    number = tuple(int(v) for v in number)

    return OrderedDict((
        ('definitions_name', 'cloudify_dsl'),
        ('definitions_version', OrderedDict((
            ('number', number),)))))

def convert_node_template(context, node_template, plugins):
    node_type = context.deployment.node_types.get_descendant(node_template.type_name)
    host_node_template = find_host_node_template(context, node_template)
    
    current_instances = 0
    for node in context.deployment.plan.nodes.itervalues():
        if node.template_name == node_template.name:
            current_instances += 1
    
    relationships = []
    for requirement in node_template.requirements:
        if requirement.relationship_template is not None:
            relationships.append(convert_relationship_template(context, requirement))

    r = OrderedDict((
        ('name', node_template.name),
        ('id', node_template.name),
        ('type', node_type.name),
        ('type_hierarchy', convert_type_hierarchy(context, node_type, context.deployment.node_types)),
        ('host_id', host_node_template.name if host_node_template is not None else None),
        ('properties', convert_properties(context, node_template.properties)),
        ('operations', convert_operations(context, node_template.interfaces)),
        ('relationships', relationships),
        ('plugins', plugins),
        ('plugins_to_install', plugins_to_install_for_interface(context, node_template.interfaces, plugins, 'host_agent')),
        ('deployment_plugins_to_install', plugins_to_install_for_interface(context, node_template.interfaces, plugins, 'central_deployment_agent')),
        ('capabilities', OrderedDict((
            ('scalable', OrderedDict((
                ('properties', OrderedDict((
                    ('current_instances', current_instances),
                    ('default_instances', node_template.default_instances),
                    ('min_instances', node_template.min_instances),
                    ('max_instances', node_template.max_instances if node_template.max_instances is not None else -1)))),))),)))))
    
    if r['host_id'] is None:
        del r['host_id']
        
    return r

def convert_group_template(context, group_template):
    return OrderedDict((
        ('members', group_template.member_node_template_names),
        ('policies', OrderedDict(
            (k, convert_group_policy(context, v)) for k, v in group_template.policies.iteritems()))))

def convert_group_policy(context, group_policy):
    return OrderedDict((
        ('type', group_policy.type_name),
        ('properties', convert_properties(context, group_policy.properties))))

def convert_relationship_template(context, requirement):
    relationship_template = requirement.relationship_template
    relationship_type = context.deployment.relationship_types.get_descendant(relationship_template.type_name)
    
    return OrderedDict((
        ('type', relationship_type.name),
        ('type_hierarchy', convert_type_hierarchy(context, relationship_type, context.deployment.relationship_types)),
        ('target_id', requirement.target_node_template_name),
        ('properties', convert_properties(context, relationship_template.properties)),
        ('source_interfaces', convert_interfaces(context, relationship_template.source_interfaces)),
        ('target_interfaces', convert_interfaces(context, relationship_template.target_interfaces)),
        ('source_operations', convert_operations(context, relationship_template.source_interfaces)), 
        ('target_operations', convert_operations(context, relationship_template.target_interfaces))))

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

def convert_interfaces(context, interfaces):
    r = OrderedDict()

    for interface_name, interface in interfaces.iteritems():
        rr = OrderedDict()
        for operation_name, operation in interface.operations.iteritems():
            rr[operation_name] = convert_interface_operation(context, operation)
        r[interface_name] = rr
    
    return r

def convert_interface_operation(context, operation):
    _, plugin_executor, _ = parse_implementation(context, operation.implementation)

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
    plugin_name, plugin_executor, operation_name = parse_implementation(context, operation.implementation)

    return OrderedDict((
        ('plugin', plugin_name),
        ('operation', operation_name),
        ('inputs', convert_inputs(context, operation.inputs)),
        ('has_intrinsic_functions', has_intrinsic_functions(context, operation.inputs)),
        ('executor', operation.executor or plugin_executor),
        ('max_retries', operation.max_retries),
        ('retry_interval', operation.retry_interval)))

def convert_workflow(context, operation):
    plugin_name, _, operation_name = parse_implementation(context, operation.implementation)

    r = OrderedDict((
        ('plugin', plugin_name),
        ('operation', operation_name),
        ('parameters', convert_parameters(context, operation.inputs)),
        ('has_intrinsic_functions', has_intrinsic_functions(context, operation.inputs)),
        ('executor', operation.executor),
        ('max_retries', operation.max_retries),
        ('retry_interval', operation.retry_interval)))

    return r
        
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

def convert_policy_type(context, policy_type):
    return OrderedDict((
        ('source', policy_type.implementation),
        ('properties', convert_parameters(context, policy_type.properties))))

def convert_properties(context, properties):
    return OrderedDict((
        (k, as_raw(v.value)) for k, v in properties.iteritems()))

def convert_inputs(context, inputs):
    return OrderedDict((
        (k, as_raw(v.value)) for k, v in inputs.iteritems()))

def convert_parameters(context, parameters):
    return OrderedDict((
        (k, convert_parameter(context, v)) for k, v in parameters.iteritems()))

def convert_parameter(context, parameter):
    # prune removes any None (but not NULL), and then as_raw converts any NULL to None
    return as_raw(prune(OrderedDict((
        ('type', parameter.type_name),
        ('default', parameter.value),
        ('description', parameter.description)))))

def convert_type_hierarchy(context, the_type, hierarchy):
    type_hierarchy = []
    while (the_type is not None) and (the_type.name is not None):
        type_hierarchy.insert(0, the_type.name)
        the_type = hierarchy.get_parent(the_type.name)
    return type_hierarchy

#
# Utils
#

def parse_implementation(context, implementation):
    if (not implementation) or ('/' in implementation):
        # Explicit script
        return None, None, implementation
    else:
        # plugin.operation
        plugin_name, operation_name = implementation.split('.', 1)
        plugin = context.presentation.presenter.service_template.plugins.get(plugin_name) if context.presentation.presenter.service_template.plugins is not None else None
        plugin_executor = plugin.executor if plugin is not None else None
        return plugin_name, plugin_executor, operation_name

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

def plugins_to_install_for_interface(context, interfaces, plugins, agent):
    install = []
    for interface in interfaces.itervalues():
        for operation in interface.operations.itervalues():
            plugin_name, plugin_executor, _ = parse_implementation(context, operation.implementation)
            executor = operation.executor or plugin_executor
            if executor == agent:
                if plugin_name not in install: 
                    install.append(plugin_name)
    return [OrderedDict((('name', v),)) for v in install]

def plugins_to_install_for_operations(context, operations, plugins, agent):
    install = []
    for operation in operations.itervalues():
        plugin_name, plugin_executor, _ = parse_implementation(context, operation.implementation)
        executor = operation.executor or plugin_executor
        if executor == agent:
            if plugin_name not in install: 
                install.append(plugin_name)
    return [OrderedDict((('name', v),)) for v in install]

def get_type_parent_name(the_type, hierarchy):
    the_type = hierarchy.get_parent(the_type.name)
    return the_type.name if the_type is not None else None

def find_host_node_template(context, node_template):
    if context.deployment.node_types.is_descendant(COMPUTE_NODE_NAME, node_template.type_name):
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
                yield group_template_name, group_template
