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

from .utils.properties import get_assigned_and_defined_property_values
from aria.presentation import Presentation, AsIsPresentation, has_fields, allow_unknown_fields, short_form_field, primitive_field, object_dict_field, object_dict_unknown_fields, field_validator, type_validator
from aria.utils import ReadOnlyDict, cachedmethod
from aria import dsl_specification

class PropertyAssignment(AsIsPresentation):
    pass

@has_fields
class TriggerAssignment(Presentation):
    @field_validator(type_validator('policy trigger', 'policy_triggers'))
    @primitive_field(str, required=True)
    def type(self):
        """
        Trigger type.
        
        :rtype: str
        """

    @object_dict_field(PropertyAssignment)
    def parameters(self):
        """
        Optional parameters that will be passed to the trigger.
        
        :rtype: dict of str, :class:`PropertyAssignment`
        """

    @cachedmethod
    def _get_type(self, context):
        return context.presentation.presenter.policy_triggers.get(self.type) if context.presentation.presenter.policy_triggers is not None else None

    @cachedmethod
    def _get_property_values(self, context):
        return ReadOnlyDict(get_assigned_and_defined_property_values(context, self, 'parameters'))

    def _validate(self, context):
        super(TriggerAssignment, self)._validate(context)
        self._get_property_values(context)

@has_fields
class PolicyAssignment(Presentation):
    @field_validator(type_validator('policy type', 'policy_types'))
    @primitive_field(str, required=True)
    def type(self):
        """
        Policy type.
        
        :rtype: str
        """

    @object_dict_field(PropertyAssignment)
    def properties(self):
        """
        Optional properties for configuring the policy.
        
        :rtype: dict of str, :class:`PropertyAssignment`
        """

    @object_dict_field(TriggerAssignment)
    def triggers(self):
        """
        A dict of triggers.
        
        :rtype: dict of str, :class:`TriggerAssignment`
        """

    @cachedmethod
    def _get_type(self, context):
        return context.presentation.presenter.policy_types.get(self.type) if context.presentation.presenter.policy_types is not None else None

    @cachedmethod
    def _get_property_values(self, context):
        return ReadOnlyDict(get_assigned_and_defined_property_values(context, self))

    def _validate(self, context):
        super(PolicyAssignment, self)._validate(context)
        self._get_property_values(context)

@short_form_field('implementation')
@has_fields
class OperationAssignment(Presentation):
    @primitive_field(str)
    def implementation(self):
        """
        The script or plugin task name to execute.
        
        ARIA NOTE: The spec seems to mistakingly mark this as a required field.
        
        :rtype: str
        """

    @object_dict_field(PropertyAssignment)
    def inputs(self):
        """
        Schema of inputs that will be passed to the implementation as kwargs.
        
        :rtype: dict of str, :class:`PropertyAssignment`
        """

    @primitive_field(str, allowed=('central_deployment_agent', 'host_agent'))
    def executor(self):
        """
        Valid values: :code:`central_deployment_agent`, :code:`host_agent`.
        
        :rtype: str
        """

    @primitive_field(int)
    def max_retries(self):
        """
        Maximum number of retries for a task. -1 means infinite retries (Default: :code:`task_retries` in manager blueprint Cloudify Manager Type for remote workflows and :code:`task_retries` workflow configuration for local workflows).
        
        :rtype: int
        """

    @primitive_field(int)
    def retry_interval(self):
        """
        Minimum wait time (in seconds) in between task retries (Default: :code:`task_retry_interval` in manager blueprint Cloudify Manager Type for remote workflows and :code:`task_retry_interval` workflow configuration for local workflows).
        
        :rtype: int
        """

@allow_unknown_fields
@has_fields
@dsl_specification('interfaces-2', 'cloudify-1.0')
@dsl_specification('interfaces-2', 'cloudify-1.1')
@dsl_specification('interfaces-2', 'cloudify-1.2')
@dsl_specification('interfaces-2', 'cloudify-1.3')
class InterfaceAssignment(Presentation):
    """
    Interfaces provide a way to map logical tasks to executable operations.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-interfaces/>`__.
    """

    @object_dict_unknown_fields(OperationAssignment)
    def operations(self):
        """
        :rtype: dict of str, :class:`OperationAssignment`
        """
