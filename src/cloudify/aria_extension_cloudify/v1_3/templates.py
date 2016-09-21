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

from .assignments import CapabilityAssignment
from .field_validators import policy_type_validator
from .utils.node_templates import get_node_template_scalable
from ..v1_0 import NodeTemplate as NodeTemplate1_0, PropertyAssignment
from ..v1_2 import ServiceTemplate as ServiceTemplate1_2
from aria import dsl_specification
from aria.presentation import Presentation, has_fields, primitive_field, primitive_list_field, object_dict_field, field_validator, list_type_validator
from aria.utils import ReadOnlyList, cachedmethod

@has_fields
@dsl_specification('node-templates-1', 'cloudify-1.3')
class NodeTemplate(NodeTemplate1_0):
    @object_dict_field(CapabilityAssignment)
    def capabilities(self):
        """
        Used for specifying the node template capabilities (Supported since: :code:`cloudify_dsl_1_3`. At the moment only scalable capability is supported)
        
        :rtype: dict of str, :class:`CapabilityAssignment`
        """

    @cachedmethod
    def _get_scalable(self, context):
        return get_node_template_scalable(context, self)

@has_fields
@dsl_specification('policies', 'cloudify-1.3')
class PolicyDefinition(Presentation):
    """
    Policies provide a way of configuring reusable behavior by referencing groups for which a policy applies.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-policies/>`__.    
    """
    
    @field_validator(policy_type_validator)
    @primitive_field(str, required=True)
    def type(self):
        """
        The policy type.
        
        :rtype: str
        """

    @object_dict_field(PropertyAssignment)
    def properties(self):
        """
        The specific policy properties. The properties schema is defined by the policy type.
        
        :rtype: dict of str, :class:`PropertyAssignment`
        """

    @field_validator(list_type_validator('group', 'groups'))
    @primitive_list_field(str, required=True)
    def targets(self):
        """
        A list of group names. The policy will be applied on the groups specified in this list. 
        
        :rtype: list of str
        """
    
    @cachedmethod
    def _get_type(self, context):
        return context.presentation.presenter.policy_types.get(self.type) if context.presentation.presenter.policy_types is not None else None

    @cachedmethod
    def _get_targets(self, context):
        r = []
        targets = self.targets
        if targets:
            for target in targets:
                target = context.presentation.presenter.groups.get(target)
                if target is not None:
                    r.append(target)
        return ReadOnlyList(r)

    def _validate(self, context):
        super(PolicyDefinition, self)._validate(context)
        self._get_targets(context)

@has_fields
class ServiceTemplate(ServiceTemplate1_2):
    @object_dict_field(NodeTemplate)
    def node_templates(self):
        """
        :rtype: dict of str, :class:`NodeTemplate`
        """

    @object_dict_field(PolicyDefinition)
    def policies(self):
        """
        :rtype: dict of str, :class:`PolicyDefinition`
        """

    def _dump(self, context):
        self._dump_content(context, (
            'description',
            'tosca_definitions_version',
            'imports',
            'plugins',
            'data_types',
            'node_types',
            'policy_types',
            'inputs',
            'node_templates',
            'relationships',
            'groups',
            'policies',
            'policy_triggers',
            'outputs',
            'workflows',
            'upload_resources'))

