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

from .consumer import Consumer, ConsumerChain
from ..utils import json_dumps, yaml_dumps

class Derive(Consumer):
    """
    Derives the deployment template.
    """
    
    def consume(self):
        if self.context.presentation.presenter is None:
            self.context.validation.report('Derive consumer: missing presenter')
            return
        
        if not hasattr(self.context.presentation.presenter, '_get_deployment_template'):
            self.context.validation.report('Derive consumer: presenter does not support "_get_deployment_template"')
            return

        self.context.deployment.template = self.context.presentation.presenter._get_deployment_template(self.context)

class ValidateTemplate(Consumer):
    """
    Validates the deployment template.
    """

    def consume(self):
        self.context.deployment.template.validate(self.context)

class Template(ConsumerChain):
    """
    Generates the deployment template by deriving it from the presentation.
    """

    def __init__(self, context):
        super(Template, self).__init__(context, (Derive, ValidateTemplate))

    def dump(self):
        if self.context.has_arg_switch('types'):
            self.context.deployment.dump_types(self.context)
        elif self.context.has_arg_switch('yaml'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.deployment.template_as_raw
            self.context.write(yaml_dumps(raw, indent=indent))
        elif self.context.has_arg_switch('json'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.deployment.template_as_raw
            self.context.write(json_dumps(raw, indent=indent))
        else:
            self.context.deployment.template.dump(self.context)

class Instantiate(Consumer):
    """
    Instantiates the deployment plan.
    """
    
    def consume(self):
        if self.context.deployment.template is None:
            self.context.validation.report('Instantiate consumer: missing deployment template')
            return

        self.context.deployment.template.instantiate(self.context, None)

class CoerceValues(Consumer):
    """
    Coerces values in the deployment plan.
    """

    def consume(self):
        self.context.deployment.plan.coerce_values(self.context, None, True)

class ValidatePlan(Consumer):
    """
    Validates the deployment plan.
    """

    def consume(self):
        self.context.deployment.plan.validate(self.context)

class SatisfyRequirements(Consumer):
    """
    Satisfies node requirements in the deployment plan.
    """

    def consume(self):
        self.context.deployment.plan.satisfy_requirements(self.context)
        
class ValidateCapabilities(Consumer):
    """
    Validates capabilities in the deployment plan.
    """

    def consume(self):
        self.context.deployment.plan.validate_capabilities(self.context)

class Plan(ConsumerChain):
    """
    Generates the deployment plan by instantiating the deployment template.
    """
    
    def __init__(self, context):
        super(Plan, self).__init__(context, (Instantiate, CoerceValues, ValidatePlan, CoerceValues, SatisfyRequirements, CoerceValues, ValidateCapabilities, CoerceValues))

    def dump(self):
        if self.context.has_arg_switch('graph'):
            self.context.deployment.plan.dump_graph(self.context)
        elif self.context.has_arg_switch('yaml'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.deployment.plan_as_raw
            self.context.write(yaml_dumps(raw, indent=indent))
        elif self.context.has_arg_switch('json'):
            indent = self.context.get_arg_value_int('indent', 2)
            raw = self.context.deployment.plan_as_raw
            self.context.write(json_dumps(raw, indent=indent))
        else:
            self.context.deployment.plan.dump(self.context)
