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
            self.context.validation.report('Template consumer: missing presenter')
            return
        
        if not hasattr(self.context.presentation.presenter, '_get_deployment_template'):
            self.context.validation.report('Template consumer: presenter does not support "_get_deployment_template"')
            return

        self.context.deployment.template = self.context.presentation.presenter._get_deployment_template(self.context)

class Validate(Consumer):
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
        super(Template, self).__init__(context, (Derive, Validate))

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
