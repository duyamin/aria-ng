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

from aria.modeling import Type, RelationshipType, PolicyType, PolicyTriggerType, ServiceModel, NodeTemplate, RelationshipTemplate, GroupTemplate, PolicyTemplate, GroupPolicy, GroupPolicyTrigger, Interface, Operation, Requirement, Parameter
from aria.validation import Issue

POLICY_SCALING = 'cloudify.policies.scaling'

def get_service_model(context):
    r = ServiceModel()
    
    r.description = context.presentation.get('service_template', 'description', 'value')

    normalize_types(context, context.modeling.node_types, context.presentation.get('service_template', 'node_types'))
    normalize_types(context, context.modeling.relationship_types, context.presentation.get('service_template', 'relationships'), normalize_relationship_type)
    normalize_types(context, context.modeling.policy_types, context.presentation.get('service_template', 'policy_types'), normalize_policy_type)
    normalize_types(context, context.modeling.policy_trigger_types, context.presentation.get('service_template', 'policy_triggers'), normalize_policy_trigger_type)
    
    # Built-in types
    scaling = PolicyType(POLICY_SCALING)
    set_scaling_policy_properties(context, scaling)
    context.modeling.policy_types.children.append(scaling)
    
    service_template = context.presentation.get('service_template')
    if service_template is not None:
        normalize_property_values(r.inputs, service_template._get_input_values(context))
        normalize_property_values(r.outputs, service_template._get_output_values(context))
    
    node_templates = context.presentation.get('service_template', 'node_templates')
    if node_templates:
        for node_template_name, node_template in node_templates.iteritems():
            r.node_templates[node_template_name] = normalize_node_template(context, node_template)

    groups = context.presentation.get('service_template', 'groups')
    if groups:
        for group_name, group in groups.iteritems():
            r.group_templates[group_name] = normalize_group(context, group)

    policies = context.presentation.get('service_template', 'policies')
    if policies:
        for policy_name, policy in policies.iteritems():
            r.policy_templates[policy_name] = normalize_policy(context, policy)
            
    workflows = context.presentation.get('service_template', 'workflows')
    if workflows:
        for workflow_name, workflow in workflows.iteritems():
            r.operations[workflow_name] = normalize_workflow(context, workflow)

    return r

def normalize_node_template(context, node_template):
    r = NodeTemplate(name=node_template._name, type_name=node_template.type)
    
    normalize_property_values(r.properties, node_template._get_property_values(context))
    normalize_interfaces(context, r.interfaces, node_template._get_interfaces(context))
    
    relationships = node_template.relationships
    if relationships:
        for relationship in relationships:
            r.requirements.append(normalize_requirement(context, relationship))

    if hasattr(node_template, '_get_scalable'):
        scalable = node_template._get_scalable(context)
        if scalable is not None:
            r.default_instances = scalable.default_instances
            r.min_instances = scalable.min_instances
            if scalable.max_instances != -1:
                r.max_instances = scalable.max_instances

    return r

def normalize_interface(context, interface, is_definition=False):
    r = Interface(name=interface._name, type_name=None)

    operations = interface.operations
    if operations:
        for operation_name, operation in operations.iteritems():
            r.operations[operation_name] = normalize_operation(context, operation, is_definition)
    
    return r if r.operations else None

def normalize_operation(context, operation, is_definition=False):
    r = Operation(name=operation._name)

    implementation = operation.implementation
    if implementation is not None:
        r.implementation = implementation
    executor = operation.executor
    if executor is not None:
        r.executor = executor
    max_retries = operation.max_retries
    if max_retries is not None:
        r.max_retries = max_retries
    retry_interval = operation.retry_interval
    if retry_interval is not None:
        r.retry_interval = retry_interval

    inputs = operation.inputs
    if inputs:
        for input_name, the_input in inputs.iteritems():
            if is_definition:
                r.inputs[input_name] = Parameter(the_input.type, the_input.default, the_input.description.value if the_input.description is not None else None)
            else:
                r.inputs[input_name] = Parameter(the_input.value.type, the_input.value.value, None) # TODO: description
    
    return r

def normalize_requirement(context, relationship):
    r = Requirement(name=relationship._name, target_node_template_name=relationship.target)
    
    r.relationship_template = normalize_relationship(context, relationship)
    
    return r

def normalize_relationship_type(context, relationship_type):
    r = RelationshipType(relationship_type._name)
    
    normalize_property_definitions(r.properties, relationship_type._get_properties(context))
    normalize_interfaces(context, r.source_interfaces, relationship_type._get_source_interfaces(context), True)
    normalize_interfaces(context, r.target_interfaces, relationship_type._get_target_interfaces(context), True)
    
    return r

def normalize_policy_type(context, policy_type):
    r = PolicyType(policy_type._name)
    
    r.implementation = policy_type.source
    normalize_property_definitions(r.properties, policy_type._get_properties(context))
    
    return r

def normalize_policy_trigger_type(context, policy_trigger_type):
    r = PolicyTriggerType(policy_trigger_type._name)
    
    r.implementation = policy_trigger_type.source
    normalize_property_definitions(r.properties, policy_trigger_type._get_properties(context))
    
    return r

def normalize_relationship(context, relationship):
    relationship_type = relationship._get_type(context)
    r = RelationshipTemplate(type_name=relationship_type._name)

    normalize_property_values(r.properties, relationship._get_property_values(context))
    normalize_interfaces(context, r.source_interfaces, relationship._get_source_interfaces(context))
    normalize_interfaces(context, r.target_interfaces, relationship._get_target_interfaces(context))
    
    return r

def normalize_group(context, group):
    r = GroupTemplate(name=group._name)

    node_templates = context.presentation.get('service_template', 'node_templates') or {}
    
    members = group.members
    if members:
        for member in members:
            if member in node_templates:
                r.member_node_template_names.append(member)
            else:
                # Note: groups inside groups are only supported since Cloudify DSL 1.3
                r.member_group_template_names.append(member)
            
    policies = group.policies
    if policies:
        for policy_name, policy in policies.iteritems():
            r.policies[policy_name] = normalize_group_policy(context, policy)
    
    return r

def normalize_group_policy(context, policy):
    r = GroupPolicy(name=policy._name, type_name=policy.type)
    normalize_property_values(r.properties, policy._get_property_values(context))
    
    triggers = policy.triggers
    if triggers:
        for trigger_name, trigger in triggers.iteritems():
            r.triggers[trigger_name] = normalize_group_policy_trigger(context, trigger)
    
    return r

def normalize_group_policy_trigger(context, trigger):
    trigger_type = trigger._get_type(context)
    r = GroupPolicyTrigger(name=trigger._name, implementation=trigger_type.source)
    normalize_property_values(r.properties, trigger._get_property_values(context))
    return r

def normalize_policy(context, policy):
    r = PolicyTemplate(name=policy._name, type_name=policy.type)
    
    normalize_property_assignments(r.properties, policy.properties)
    if policy.type == POLICY_SCALING:
        set_scaling_policy_properties(context, r, policy)
    
    groups = policy._get_targets(context)
    for group in groups:
        r.target_group_template_names.append(group._name)
    
    return r

def normalize_workflow(context, workflow):
    r = Operation(name=workflow._name)

    r.implementation = workflow.mapping

    parameters = workflow.parameters
    if parameters:
        for parameter_name, parameter in parameters.iteritems():
            r.inputs[parameter_name] = Parameter(parameter.type, parameter.default, parameter.description.value if parameter.description is not None else None)
    
    return r

#
# Utils
#

def normalize_types(context, root, types, normalize=None):
    if types is None:
        return
    
    def added_all():
        for name in types:
            if root.get_descendant(name) is None:
                return False
        return True

    while not added_all():    
        for name, the_type in types.iteritems():
            if root.get_descendant(name) is None:
                parent_type = the_type._get_parent(context)
                if normalize:
                    r = normalize(context, the_type)
                else:
                    r = Type(the_type._name)
                if parent_type is None:
                    root.children.append(r)
                else:
                    container = root.get_descendant(parent_type._name)
                    if container is not None:
                        container.children.append(r)

def normalize_property_values(properties, source_properties):
    if source_properties:
        for property_name, prop in source_properties.iteritems():
            properties[property_name] = Parameter(prop.type, prop.value, None) # TODO: description

def normalize_property_assignments(properties, source_properties):
    if source_properties:
        for property_name, prop in source_properties.iteritems():
            properties[property_name] = Parameter(None, prop.value, None) # TODO: description

def normalize_property_definitions(properties, source_properties):
    if source_properties:
        for property_name, prop in source_properties.iteritems():
            properties[property_name] = Parameter(prop.type, prop.default, prop.description.value if prop.description is not None else None)

def normalize_interfaces(context, interfaces, source_interfaces, is_definition=False):
    if source_interfaces:
        for interface_name, interface in source_interfaces.iteritems():
            interface = normalize_interface(context, interface, is_definition)
            if interface is not None:
                interfaces[interface_name] = interface

def set_scaling_policy_properties(context, o, presentation=None):
    def set_value(name, default, description, is_check_range=False):
        if name in o.properties:
            o.properties[name].type = 'int'
        else:
            o.properties[name] = Parameter('int', default, description)
        is_valid = coerce(name)
        if is_valid and is_check_range:
            is_valid = check_range(name)
        return is_valid
    
    def coerce(name):
        value = o.properties[name].value
        try:
            o.properties[name].value = int(value)
            if name == 'max_instances':
                if o.properties['max_instances'].value < -1:
                    context.validation.report('"max_instances" is not a positive integer, zero, or -1', locator=presentation._get_child_locator(name), level=Issue.FIELD)
                    return False
            elif o.properties[name].value < 0:
                context.validation.report('"%s" is not a positive integer or zero' % name, locator=presentation._get_child_locator(name), level=Issue.FIELD)
                return False
        except TypeError:
            context.validation.report('"%s" is not a valid integer' % name, locator=presentation._get_child_locator(name), level=Issue.FIELD)
            return False
        return True
    
    def check_range(name):
        value = o.properties[name].value
        if value < o.properties['min_instances'].value:
            context.validation.report('"%s" is lesser than "min_instances"' % name, locator=presentation._get_child_locator(name), level=Issue.BETWEEN_FIELDS)
            return False
        elif (o.properties['max_instances'].value != -1) and (value > o.properties['max_instances'].value):
            context.validation.report('"%s" is greater than "max_instances"' % name, locator=presentation._get_child_locator(name), level=Issue.BETWEEN_FIELDS)
            return False
        return True

    if ('max_instances' in o.properties) and (o.properties['max_instances'].value == 'UNBOUNDED'):
        o.properties['max_instances'].value = -1
    
    is_min_valid = set_value('min_instances', 0, 'The minimum number of allowed group instances.')
    is_max_valid = set_value('max_instances', -1, 'The maximum number of allowed group instances.')
    
    is_range_valid = is_min_valid and is_max_valid
    if is_range_valid and (o.properties['max_instances'].value != -1) and (o.properties['max_instances'].value < o.properties['min_instances'].value):
        context.validation.report('"max_instances" is lesser than "min_instances"', locator=presentation._get_child_locator('max_instances'), level=Issue.BETWEEN_FIELDS)
        is_range_valid = False
        
    is_default_valid = set_value('default_instances', 1, 'The number of instances the groups referenced by this policy will have.', is_range_valid)
    
    if is_default_valid:
        set_value('planned_instances', o.properties['default_instances'].value, None, is_range_valid)
        set_value('current_instances', o.properties['default_instances'].value, None, is_range_valid)
