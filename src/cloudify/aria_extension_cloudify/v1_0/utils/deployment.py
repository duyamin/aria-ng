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

from aria.deployment import Type, RelationshipType, DeploymentTemplate, NodeTemplate, RelationshipTemplate, GroupTemplate, PolicyTemplate, GroupPolicy, GroupPolicyTrigger, Interface, Operation, Requirement, Parameter

def get_deployment_template(context, presenter):
    r = DeploymentTemplate()
    
    r.description = presenter.service_template.description.value if presenter.service_template.description is not None else None

    normalize_types(context, context.deployment.node_types, presenter.node_types)
    normalize_types(context, context.deployment.group_types, presenter.group_types)
    normalize_types(context, context.deployment.relationship_types, presenter.relationship_types, normalize_relationship_type)
    normalize_types(context, context.deployment.policy_types, presenter.policy_types)
    
    # This policy type is built-in
    context.deployment.policy_types.children.append(Type('cloudify.policies.scaling'))

    normalize_property_values(r.inputs, presenter.service_template._get_input_values(context))
    normalize_property_values(r.outputs, presenter.service_template._get_output_values(context))

    node_templates = presenter.node_templates
    if node_templates:
        for node_template_name, node_template in node_templates.iteritems():
            r.node_templates[node_template_name] = normalize_node_template(context, node_template)

    groups = presenter.groups
    if groups:
        for group_name, group in groups.iteritems():
            r.group_templates[group_name] = normalize_group(context, group)

    policies = presenter.policies
    if policies:
        for policy_name, policy in policies.iteritems():
            r.policy_templates[policy_name] = normalize_policy(context, policy)
            
    workflows = presenter.workflows
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

def normalize_relationship(context, relationship):
    relationship_type = relationship._get_type(context)
    r = RelationshipTemplate(type_name=relationship_type._name)

    normalize_property_values(r.properties, relationship._get_property_values(context))
    normalize_interfaces(context, r.source_interfaces, relationship._get_source_interfaces(context))
    normalize_interfaces(context, r.target_interfaces, relationship._get_target_interfaces(context))
    
    return r

def normalize_group(context, group):
    r = GroupTemplate(name=group._name)
    
    members = group.members
    if members:
        for member in members:
            r.member_node_template_names.append(member)
            
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
