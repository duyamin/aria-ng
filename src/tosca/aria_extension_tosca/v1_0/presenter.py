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
from .functions import Concat, Token, GetInput, GetProperty, GetAttribute, GetOperationOutput, GetNodesOfType, GetArtifact
from .deployment import get_deployment_template
from aria.presentation import Presenter
from aria.utils import ReadOnlyList, cachedmethod

class ToscaSimplePresenter1_0(Presenter):
    """
    ARIA presenter for the `TOSCA Simple Profile v1.0 <http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/csprd02/TOSCA-Simple-Profile-YAML-v1.0-csprd02.html>`__.
    """

    DSL_VERSION = 'tosca_simple_yaml_1_0'
    ALLOWED_IMPORTED_DSL_VERSIONS = ('tosca_simple_yaml_1_0',)
    
    @property
    @cachedmethod
    def service_template(self):
        return ServiceTemplate(raw=self._raw)

    @property
    @cachedmethod
    def functions(self):
        return {
            'concat': Concat,
            'token': Token,
            'get_input': GetInput,
            'get_property': GetProperty,
            'get_attribute': GetAttribute,
            'get_operation_output': GetOperationOutput,
            'get_nodes_of_type': GetNodesOfType,
            'get_artifact': GetArtifact} 
    
    # Presentation

    def _dump(self, context):
        self.service_template._dump(context)

    def _validate(self, context):
        self.service_template._validate(context)

    # Presenter

    @cachedmethod
    def _get_import_locations(self):
        return ReadOnlyList([i.file for i in self.service_template.imports] if (self.service_template and self.service_template.imports) else [])

    @cachedmethod
    def _get_deployment_template(self, context):
        return get_deployment_template(context)
