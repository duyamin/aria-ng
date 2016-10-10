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

from .shared_elements import Element, Parameter, Interface, Operation, Artifact, GroupPolicy
from .utils import validate_dict_values, validate_list_values, coerce_dict_values, coerce_list_values, dump_list_values, dump_dict_values, dump_properties, dump_interfaces
from ..validation import Issue
from ..utils import StrictList, StrictDict, ReadOnlyList, puts, indent, as_raw 
from collections import OrderedDict

class ServiceInstance(Element):
    """
    A service instance is an instance of a :class:`ServiceModel`.
    
    You will usually not create it programmatically, but instead instantiate
    it from the model.
    
    Properties:
    
    * :code:`description`: Human-readable description
    * :code:`metadata`: :class:`Metadata`
    * :code:`nodes`: Dict of :class:`Node`
    * :code:`groups`: Dict of :class:`Group`
    * :code:`policies`: Dict of :class:`Policy`
    * :code:`substitution`: :class:`Substituion`
    * :code:`inputs`: Dict of :class:`Parameter`
    * :code:`outputs`: Dict of :class:`Parameter`
    * :code:`operations`: Dict of :class:`Operation`
    """
    
    def __init__(self):
        self.description = None
        self.metadata = None
        self.nodes = StrictDict(key_class=basestring, value_class=Node) 
        self.groups = StrictDict(key_class=basestring, value_class=Group) 
        self.policies = StrictDict(key_class=basestring, value_class=Policy)
        self.substitution = None
        self.inputs = StrictDict(key_class=basestring, value_class=Parameter)
        self.outputs = StrictDict(key_class=basestring, value_class=Parameter)
        self.operations = StrictDict(key_class=basestring, value_class=Operation)

    def satisfy_requirements(self, context):
        satisfied = True
        for node in self.nodes.itervalues():
            if not node.satisfy_requirements(context):
                satisfied = False
        return satisfied
    
    def validate_capabilities(self, context):
        satisfied = True
        for node in self.nodes.itervalues():
            if not node.validate_capabilities(context):
                satisfied = False
        return satisfied
    
    def find_nodes(self, node_template_name):
        nodes = []
        for node in self.nodes.itervalues():
            if node.template_name == node_template_name:
                nodes.append(node)
        return ReadOnlyList(nodes)

    def get_node_ids(self, node_template_name):
        return ReadOnlyList((node.id for node in self.find_nodes(node_template_name)))
    
    def find_groups(self, group_template_name):
        groups = []
        for group in self.groups.itervalues():
            if group.template_name == group_template_name:
                groups.append(group)
        return ReadOnlyList(groups)

    def get_group_ids(self, group_template_name):
        return ReadOnlyList((group.id for group in self.find_groups(group_template_name)))
    
    def is_node_a_target(self, context, target_node):
        for node in self.nodes.itervalues():
            if self._is_node_a_target(context, node, target_node):
                return True
        return False

    def _is_node_a_target(self, context, source_node, target_node):
        if source_node.relationships:
            for relationship in source_node.relationships:
                if relationship.target_node_id == target_node.id:
                    return True
                else:
                    node = context.modeling.instance.nodes.get(relationship.target_node_id)
                    if node is not None:
                        if self._is_node_a_target(context, node, target_node):
                            return True
        return False

    @property
    def as_raw(self):
        return OrderedDict((
            ('description', self.description),
            ('metadata', as_raw(self.metadata) if self.metadata is not None else None),
            ('nodes', [as_raw(v) for v in self.nodes.itervalues()]),
            ('groups', [as_raw(v) for v in self.groups.itervalues()]),
            ('policies', [as_raw(v) for v in self.policies.itervalues()]),
            ('substitution', as_raw(self.substitution) if self.substitution is not None else None),
            ('inputs', {k: as_raw(v) for k, v in self.inputs.iteritems()}),
            ('outputs', {k: as_raw(v) for k, v in self.outputs.iteritems()}),
            ('operations', [as_raw(v) for v in self.operations.itervalues()])))
    
    def validate(self, context):
        if self.metadata is not None:
            self.metadata.validate(context)
        validate_dict_values(context, self.nodes)
        validate_dict_values(context, self.groups)
        validate_dict_values(context, self.policies)
        if self.substitution is not None:
            self.substitution.validate(context)
        validate_dict_values(context, self.inputs)
        validate_dict_values(context, self.outputs)
        validate_dict_values(context, self.operations)

    def coerce_values(self, context, container, report_issues):
        if self.metadata is not None:
            self.metadata.coerce_values(context, container, report_issues)
        coerce_dict_values(context, container, self.nodes, report_issues)
        coerce_dict_values(context, container, self.groups, report_issues)
        coerce_dict_values(context, container, self.policies, report_issues)
        if self.substitution is not None:
            self.substitution.coerce_values(context, container, report_issues)
        coerce_dict_values(context, container, self.inputs, report_issues)
        coerce_dict_values(context, container, self.outputs, report_issues)
        coerce_dict_values(context, container, self.operations, report_issues)

    def dump(self, context):
        if self.description is not None:
            puts('Description: %s' % context.style.meta(self.description))
        if self.metadata is not None:
            self.metadata.dump(context)
        for node in self.nodes.itervalues():
            node.dump(context)
        for group in self.groups.itervalues():
            group.dump(context)
        for policy in self.policies.itervalues():
            policy.dump(context)
        if self.substitution is not None:
            self.substitution.dump(context)
        dump_properties(context, self.inputs, 'Inputs')
        dump_properties(context, self.outputs, 'Outputs')
        dump_dict_values(context, self.operations, 'Operations')

    def dump_graph(self, context):
        for node in self.nodes.itervalues():
            if not self.is_node_a_target(context, node):
                self._dump_graph_node(context, node)
        
    def _dump_graph_node(self, context, node):
        puts(context.style.node(node.id))
        if node.relationships:
            with context.style.indent:
                for relationship in node.relationships:
                    relationship_name = context.style.node(relationship.template_name) if relationship.template_name is not None else context.style.type(relationship.type_name)
                    capability_name = context.style.node(relationship.target_capability_name) if relationship.target_capability_name is not None else None
                    if capability_name is not None:
                        puts('-> %s %s' % (relationship_name, capability_name))
                    else:
                        puts('-> %s' % relationship_name)
                    target_node = self.nodes.get(relationship.target_node_id)
                    with indent(3):
                        self._dump_graph_node(context, target_node)

class Node(Element):
    """
    An instance of a :class:`NodeTemplate`.
    
    Nodes may have zero or more :class:`Relationship` instances to other nodes.
    
    Properties:
    
    * :code:`id`: Unique ID (prefixed with the template name)
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`template_name`: Must be represented in the :class:`ServiceModel`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`interfaces`: Dict of :class:`Interface`
    * :code:`artifacts`: Dict of :class:`Artifact`
    * :code:`capabilities`: Dict of :class:`CapabilityTemplate`
    * :code:`relationship`: List of :class:`Relationship`
    """
    
    def __init__(self, context, type_name, template_name):
        if not isinstance(type_name, basestring):
            raise ValueError('must set type_name (string)')
        if not isinstance(template_name, basestring):
            raise ValueError('must set template_name (string)')

        self.id = '%s_%s' % (template_name, context.modeling.generate_id())
        self.type_name = type_name
        self.template_name = template_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.interfaces = StrictDict(key_class=basestring, value_class=Interface)
        self.artifacts = StrictDict(key_class=basestring, value_class=Artifact)
        self.capabilities = StrictDict(key_class=basestring, value_class=Capability)
        self.relationships = StrictList(value_class=Relationship)
    
    def satisfy_requirements(self, context):
        node_template = context.modeling.model.node_templates.get(self.template_name)
        satisfied = True
        for requirement in node_template.requirements:
            # Find target template
            target_node_template, target_node_capability = requirement.find_target(context, node_template)
            if target_node_template is not None:
                # Find target nodes
                target_nodes = context.modeling.instance.find_nodes(target_node_template.name)
                if target_nodes:
                    target_node = None
                    target_capability = None
                    
                    if target_node_capability is not None:
                        # Relate to the first target node that has capacity
                        for node in target_nodes:
                            target_capability = node.capabilities.get(target_node_capability.name)
                            if target_capability.relate():
                                target_node = node
                                break
                    else:
                        # Use first target node
                        target_node = target_nodes[0]
                        
                    if target_node is not None:
                        if requirement.relationship_template is not None:
                            relationship = requirement.relationship_template.instantiate(context, self)
                            relationship.target_node_id = target_node.id
                            if target_capability is not None:
                                relationship.target_capability_name = target_capability.name
                            self.relationships.append(relationship)
                    else:
                        context.validation.report('requirement "%s" of node "%s" targets node template "%s" but its instantiated nodes do not have enough capacity' % (requirement.name, self.id, target_node_template.name), level=Issue.BETWEEN_INSTANCES)
                        satisfied = False
                else:
                    context.validation.report('requirement "%s" of node "%s" targets node template "%s" but it has no instantiated nodes' % (requirement.name, self.id, target_node_template.name), level=Issue.BETWEEN_INSTANCES)
                    satisfied = False
            else:
                context.validation.report('requirement "%s" of node "%s" has no target node template' % (requirement.name, self.id), level=Issue.BETWEEN_INSTANCES)
                satisfied = False
        return satisfied

    def validate_capabilities(self, context):
        satisfied = False
        for capability in self.capabilities.itervalues():
            if not capability.has_enough_relationships:
                context.validation.report('capability "%s" of node "%s" requires at least %d relationships but has %d' % (capability.name, self.id, capability.min_occurrences, capability.occurrences), level=Issue.BETWEEN_INSTANCES)
                satisfied = False
        return satisfied

    @property
    def as_raw(self):
        return OrderedDict((
            ('id', self.id),
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('properties', {k: as_raw(v) for k, v in self.properties.iteritems()}),
            ('interfaces', [as_raw(v) for v in self.interfaces.itervalues()]),
            ('artifacts', [as_raw(v) for v in self.artifacts.itervalues()]),
            ('capabilities', [as_raw(v) for v in self.capabilities.itervalues()]),
            ('relationships', [as_raw(v) for v in self.relationships])))
            
    def validate(self, context):
        if len(self.id) > context.modeling.id_max_length:
            context.validation.report('"%s" has an ID longer than the limit of %d characters: %d' % (self.id, context.modeling.id_max_length, len(self.id)), level=Issue.BETWEEN_INSTANCES)
        
        # TODO: validate that node template is of type?
        
        validate_dict_values(context, self.properties)
        validate_dict_values(context, self.interfaces)
        validate_dict_values(context, self.artifacts)
        validate_dict_values(context, self.capabilities)
        validate_list_values(context, self.relationships)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, self, self.properties, report_issues)
        coerce_dict_values(context, self, self.interfaces, report_issues)
        coerce_dict_values(context, self, self.artifacts, report_issues)
        coerce_dict_values(context, self, self.capabilities, report_issues)
        coerce_list_values(context, self, self.relationships, report_issues)

    def dump(self, context):
        puts('Node: %s' % context.style.node(self.id))
        with context.style.indent:
            puts('Template: %s' % context.style.node(self.template_name))
            puts('Type: %s' % context.style.type(self.type_name))
            dump_properties(context, self.properties)
            dump_interfaces(context, self.interfaces)
            dump_dict_values(context, self.artifacts, 'Artifacts')
            dump_dict_values(context, self.capabilities, 'Capabilities')
            dump_list_values(context, self.relationships, 'Relationships')

class Capability(Element):
    """
    A capability of a :class:`Node`.
    
    An instance of a :class:`CapabilityTemplate`.

    Properties:
    
    * :code:`name`: Name
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`min_occurrences`: Minimum number of requirement matches required
    * :code:`max_occurrences`: Maximum number of requirement matches allowed
    * :code:`properties`: Dict of :class:`Parameter`
    """
    
    def __init__(self, name, type_name):
        if not isinstance(name, basestring):
            raise ValueError('name must be string')
        if not isinstance(type_name, basestring):
            raise ValueError('type_name must be string')
        
        self.name = name
        self.type_name = type_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        
        self.min_occurrences = None # optional
        self.max_occurrences = None # optional
        self.occurrences = 0
    
    @property
    def has_enough_relationships(self):
        if self.min_occurrences is not None:
            return self.occurrences >= self.min_occurrences
        return True

    def relate(self):
        if self.max_occurrences is not None:
            if self.occurrences == self.max_occurrences:
                return False
        self.occurrences += 1
        return True 

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('properties', {k: as_raw(v) for k, v in self.properties.iteritems()})))

    def validate(self, context):
        if context.modeling.capability_types.get_descendant(self.type_name) is None:
            context.validation.report('capability "%s" has an unknown type: %s' % (self.name, safe_repr(self.type_name)), level=Issue.BETWEEN_TYPES)
        
        validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)
            
    def dump(self, context):
        puts(context.style.node(self.name))
        with context.style.indent:
            puts('Type: %s' % context.style.type(self.type_name))
            puts('Occurrences: %s (%s%s)' % (self.occurrences, self.min_occurrences or 0, (' to %d' % self.max_occurrences) if self.max_occurrences is not None else ' or more'))
            dump_properties(context, self.properties)

class Relationship(Element):
    """
    Connects :class:`Node` to another node.

    An instance of a :class:`RelationshipTemplate`.

    Properties:

    * :code:`target_node_id`: Must be represented in the :class:`ServiceInstance`
    * :code:`target_capability_name`: The matches capability at the target node
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`template_name`: Must be represented in the :class:`ServiceModel`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`source_interfaces`: Dict of :class:`Interface`
    * :code:`target_interfaces`: Dict of :class:`Interface`
    """
    
    def __init__(self, type_name=None, template_name=None):
        if type_name and not isinstance(type_name, basestring):
            raise ValueError('type_name must be string')
        if template_name and not isinstance(template_name, basestring):
            raise ValueError('template_name must be string')
        if (type_name and template_name) or ((not type_name) and (not template_name)):
            raise ValueError('must set either type_name or template_name')
        
        self.target_node_id = None
        self.target_capability_name = None
        self.type_name = type_name
        self.template_name = template_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.source_interfaces = StrictDict(key_class=basestring, value_class=Interface)
        self.target_interfaces = StrictDict(key_class=basestring, value_class=Interface)

    @property
    def as_raw(self):
        return OrderedDict((
            ('target_node_id', self.target_node_id),
            ('target_capability_name', self.target_capability_name),
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('properties', {k: as_raw(v) for k, v in self.properties.iteritems()}),
            ('source_interfaces', [as_raw(v) for v in self.source_interfaces.itervalues()]),            
            ('target_interfaces', [as_raw(v) for v in self.target_interfaces.itervalues()])))            

    def validate(self, context):
        if self.type_name:
            if context.modeling.relationship_types.get_descendant(self.type_name) is None:
                context.validation.report('relationship "%s" has an unknown type: %s' % (self.name, safe_repr(self.type_name)), level=Issue.BETWEEN_TYPES)        

        validate_dict_values(context, self.properties)
        validate_dict_values(context, self.source_interfaces)
        validate_dict_values(context, self.target_interfaces)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)
        coerce_dict_values(context, container, self.source_interfaces, report_issues)
        coerce_dict_values(context, container, self.target_interfaces, report_issues)

    def dump(self, context):
        puts('Target node: %s' % context.style.node(self.target_node_id))
        with context.style.indent:
            if self.target_capability_name is not None:
                puts('Target capability: %s' % context.style.node(self.target_capability_name))
            if self.type_name is not None:
                puts('Relationship type: %s' % context.style.type(self.type_name))
            else:
                puts('Relationship template: %s' % context.style.node(self.template_name))
            dump_properties(context, self.properties)
            dump_interfaces(context, self.source_interfaces, 'Source interfaces')
            dump_interfaces(context, self.target_interfaces, 'Target interfaces')

class Group(Element):
    """
    An instance of a :class:`GroupTemplate`.

    Properties:
    
    * :code:`id`: Unique ID (prefixed with the template name)
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`template_name`: Must be represented in the :class:`ServiceModel`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`interfaces`: Dict of :class:`Interface`
    * :code:`policies`: Dict of :class:`GroupPolicy`
    * :code:`member_node_ids`: Must be represented in the :class:`ServiceInstance`
    * :code:`member_group_ids`: Must be represented in the :class:`ServiceInstance`
    """    
    
    def __init__(self, context, type_name, template_name):
        if not isinstance(template_name, basestring):
            raise ValueError('must set template_name (string)')

        self.id = '%s_%s' % (template_name, context.modeling.generate_id())
        self.type_name = type_name
        self.template_name = template_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.interfaces = StrictDict(key_class=basestring, value_class=Interface)
        self.policies = StrictDict(key_class=basestring, value_class=GroupPolicy)
        self.member_node_ids = StrictList(value_class=basestring)
        self.member_group_ids = StrictList(value_class=basestring)

    @property
    def as_raw(self):
        return OrderedDict((
            ('id', self.id),
            ('type_name', self.type_name),
            ('template_name', self.template_name),
            ('properties', {k: as_raw(v) for k, v in self.properties.iteritems()}),
            ('interfaces', [as_raw(v) for v in self.interfaces.itervalues()]),
            ('policies', [as_raw(v) for v in self.policies.itervalues()]),
            ('member_node_ids', self.member_node_ids),
            ('member_group_ids', self.member_group_ids)))

    def validate(self, context):
        if context.modeling.group_types.get_descendant(self.type_name) is None:
            context.validation.report('group "%s" has an unknown type: %s' % (self.name, safe_repr(self.type_name)), level=Issue.BETWEEN_TYPES)        

        validate_dict_values(context, self.properties)
        validate_dict_values(context, self.interfaces)
        validate_dict_values(context, self.policies)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)
        coerce_dict_values(context, container, self.interfaces, report_issues)
        coerce_dict_values(context, container, self.policies, report_issues)

    def dump(self, context):
        puts('Group: %s' % context.style.node(self.id))
        with context.style.indent:
            puts('Type: %s' % context.style.type(self.type_name))
            puts('Template: %s' % context.style.type(self.template_name))
            dump_properties(context, self.properties)
            dump_interfaces(context, self.interfaces)
            dump_dict_values(context, self.policies, 'Policies')
            if self.member_node_ids:
                puts('Member nodes:')
                with context.style.indent:
                    for node_id in self.member_node_ids:
                        puts(context.style.node(node_id))

class Policy(Element):
    """
    An instance of a :class:`PolicyTemplate`.
    
    Properties:
    
    * :code:`name`: Name
    * :code:`type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`target_node_ids`: Must be represented in the :class:`ServiceInstance`
    * :code:`target_group_ids`: Must be represented in the :class:`ServiceInstance`
    """
    
    def __init__(self, name, type_name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        if not isinstance(type_name, basestring):
            raise ValueError('must set type_name (string)')
        
        self.name = name
        self.type_name = type_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.target_node_ids = StrictList(value_class=basestring)
        self.target_group_ids = StrictList(value_class=basestring)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('properties', {k: as_raw(v) for k, v in self.properties.iteritems()}),
            ('target_node_ids', self.target_node_ids),
            ('target_group_ids', self.target_group_ids)))

    def validate(self, context):
        if context.modeling.policy_types.get_descendant(self.type_name) is None:
            context.validation.report('policy "%s" has an unknown type: %s' % (self.name, safe_repr(self.type_name)), level=Issue.BETWEEN_TYPES)        

        validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        puts('Policy: %s' % context.style.node(self.name))
        with context.style.indent:
            puts('Type: %s' % context.style.type(self.type_name))
            dump_properties(context, self.properties)
            if self.target_node_ids:
                puts('Target nodes:')
                with context.style.indent:
                    for node_id in self.target_node_ids:
                        puts(context.style.node(node_id))
            if self.target_group_ids:
                puts('Target groups:')
                with context.style.indent:
                    for group_id in self.target_group_ids:
                        puts(context.style.node(group_id))

class Mapping(Element):
    """
    An instance of a :class:`MappingTemplate`.
    
    Properties:
    
    * :code:`mapped_name`: Exposed capability or requirement name
    * :code:`node_id`: Must be represented in the :class:`ServiceInstance`
    * :code:`name`: Name of capability or requirement at the node
    """
    
    def __init__(self, mapped_name, node_id, name):
        if not isinstance(mapped_name, basestring):
            raise ValueError('must set mapped_name (string)')
        if not isinstance(node_id, basestring):
            raise ValueError('must set node_id (string)')
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')

        self.mapped_name = mapped_name
        self.node_id = node_id
        self.name = name

    @property
    def as_raw(self):
        return OrderedDict((
            ('mapped_name', self.mapped_name),
            ('node_id', self.node_id),
            ('name', self.name)))

    def dump(self, context):
        puts('%s -> %s.%s' % (context.style.node(self.mapped_name), context.style.node(self.node_id), context.style.node(self.name)))

class Substitution(Element):
    """
    An instance of a :class:`SubstitutionTemplate`.
    
    Properties:
    
    * :code:`node_type_name`: Must be represented in the :class:`ModelingContext`
    * :code:`capabilities`: Dict of :class:`Mapping`
    * :code:`requirements`: Dict of :class:`Mapping`
    """
    
    def __init__(self, node_type_name):
        if not isinstance(node_type_name, basestring):
            raise ValueError('must set node_type_name (string)')
    
        self.node_type_name = node_type_name
        self.capabilities = StrictDict(key_class=basestring, value_class=Mapping)
        self.requirements = StrictDict(key_class=basestring, value_class=Mapping)

    @property
    def as_raw(self):
        return OrderedDict((
            ('node_type_name', self.node_type_name),
            ('capabilities', [as_raw(v) for v in self.capabilities.itervalues()]),
            ('requirements', [as_raw(v) for v in self.requirements.itervalues()])))

    def validate(self, context):
        if context.modeling.node_types.get_descendant(self.node_type_name) is None:
            context.validation.report('substitution "%s" has an unknown type: %s' % (self.name, safe_repr(self.node_type_name)), level=Issue.BETWEEN_TYPES)        

        validate_dict_values(context, self.capabilities)
        validate_dict_values(context, self.requirements)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.capabilities, report_issues)
        coerce_dict_values(context, container, self.requirements, report_issues)

    def dump(self, context):
        puts('Substitution:')
        with context.style.indent:
            puts('Node type: %s' % context.style.type(self.node_type_name))
            dump_dict_values(context, self.capabilities, 'Capability mappings')
            dump_dict_values(context, self.requirements, 'Requirement mappings')
