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

from .templates import ServiceTemplate
from .functions import GetInput, GetProperty, GetAttribute
from .utils.deployment import get_deployment_template
from aria.validation import Issue
from aria.presentation import Presenter
from aria.utils import EMPTY_READ_ONLY_LIST, cachedmethod

class CloudifyPresenter1_0(Presenter):
    """
    ARIA presenter for the `Cloudify DSL v1.0 specification <http://getcloudify.org/guide/3.1/dsl-spec-general.html>`__.
    """

    @property
    @cachedmethod
    def service_template(self):
        return ServiceTemplate(raw=self._raw)
    
    @property
    @cachedmethod
    def functions(self):
        return {
            'get_input': GetInput,
            'get_property': GetProperty,
            'get_attribute': GetAttribute}

    # Presentation

    def _dump(self, context):
        self.service_template._dump(context)

    def _validate(self, context):
        self.service_template._validate(context)

    # Presenter

    @staticmethod
    def can_present(raw):
        dsl = raw.get('tosca_definitions_version')
        return dsl == 'cloudify_dsl_1_0'

    def _get_import_locations(self):
        return self.service_template.imports if (self.service_template and self.service_template.imports) else EMPTY_READ_ONLY_LIST
    
    def _validate_import(self, context, presentation):
        r = True
        if (presentation.service_template.tosca_definitions_version is not None) and (presentation.service_template.tosca_definitions_version != self.service_template.tosca_definitions_version):
            context.validation.report('import "tosca_definitions_version" is not "%s": %s' % (self.service_template.tosca_definitions_version, presentation.service_template.tosca_definitions_version), locator=presentation._get_child_locator('inputs'), level=Issue.BETWEEN_TYPES)
            r = False
        if presentation.inputs is not None:
            context.validation.report('import has forbidden "inputs" section', locator=presentation._get_child_locator('inputs'), level=Issue.BETWEEN_TYPES)
            r = False
        if presentation.outputs is not None:
            context.validation.report('import has forbidden "outputs" section', locator=presentation._get_child_locator('outputs'), level=Issue.BETWEEN_TYPES)
            r = False
        if presentation.node_templates is not None:
            context.validation.report('import has forbidden "node_templates" section', locator=presentation._get_child_locator('node_templates'), level=Issue.BETWEEN_TYPES)
            r = False
        if presentation.groups is not None:
            context.validation.report('import has forbidden "groups" section', locator=presentation._get_child_locator('groups'), level=Issue.BETWEEN_TYPES)
            r = False
        return r

    @cachedmethod
    def _get_deployment_template(self, context):
        return get_deployment_template(context, self)

    @property
    @cachedmethod
    def repositories(self):
        return None

    @property
    @cachedmethod
    def inputs(self):
        return self.service_template.inputs
            
    @property
    @cachedmethod
    def outputs(self):
        return self.service_template.outputs

    @property
    @cachedmethod
    def data_types(self):
        return None
    
    @property
    @cachedmethod
    def node_types(self):
        return self.service_template.node_types
    
    @property
    @cachedmethod
    def relationship_types(self):
        return self.service_template.relationships
    
    @property
    @cachedmethod
    def group_types(self):
        return None

    @property
    @cachedmethod
    def capability_types(self):
        return None

    @property
    @cachedmethod
    def interface_types(self):
        return None

    @property
    @cachedmethod
    def artifact_types(self):
        return None

    @property
    @cachedmethod
    def policy_types(self):
        return self.service_template.policy_types
    
    @property
    @cachedmethod
    def node_templates(self):
        return self.service_template.node_templates

    @property
    @cachedmethod
    def relationship_templates(self):
        return None

    @property
    @cachedmethod
    def groups(self):
        return self.service_template.groups

    @property
    @cachedmethod
    def policies(self):
        return None

    @property
    @cachedmethod
    def policy_triggers(self):
        return self.service_template.policy_triggers

    @property
    @cachedmethod
    def workflows(self):
        return self.service_template.workflows
