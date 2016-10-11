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

from .presentation import Presentation
from ..validation import Issue 
from ..utils import merge, safe_repr

class Presenter(Presentation):
    """
    Base class for ARIA presenters.
    
    Presenters provide a robust API over agnostic raw data.
    """

    @classmethod
    def can_present(cls, raw):
        dsl = raw.get('tosca_definitions_version')
        return dsl in cls.DSL_VERSIONS

    def _validate_import(self, context, presentation):
        if (presentation.service_template.tosca_definitions_version is not None) and (presentation.service_template.tosca_definitions_version not in self.__class__.ALLOWED_IMPORTED_DSL_VERSIONS):
            context.validation.report('import "tosca_definitions_version" is not one of %s: %s' % (' or '.join([safe_repr(v) for v in self.__class__.ALLOWED_IMPORTED_DSL_VERSIONS]), presentation.service_template.tosca_definitions_version), locator=presentation._get_child_locator('inputs'), level=Issue.BETWEEN_TYPES)
            return False
        return True

    def _merge_import(self, presentation):
        merge(self._raw, presentation._raw)
        if hasattr(self._raw, '_locator') and hasattr(presentation._raw, '_locator'):
            self._raw._locator.merge(presentation._raw._locator)

    def _link_locators(self):
        if hasattr(self._raw, '_locator'):
            locator = self._raw._locator
            delattr(self._raw, '_locator')
            locator.link(self._raw)

    def _get_import_locations(self, context):
        return None
    
    def _get_deployment_template(self, context):
        return None
