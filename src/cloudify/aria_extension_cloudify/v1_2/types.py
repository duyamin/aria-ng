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

from .modeling.data_types import coerce_data_type_value, validate_data_type_name
from ..v1_0 import PropertyDefinition
from ..v1_0.modeling.properties import get_inherited_property_definitions
from aria import dsl_specification
from aria.presentation import Presentation, has_fields, primitive_field, object_dict_field, field_validator, derived_from_validator
from aria.utils import ReadOnlyDict, cachedmethod

@has_fields
@dsl_specification('data-types', 'cloudify-1.2')
@dsl_specification('data-types', 'cloudify-1.3')
class DataType(Presentation):
    """
    :code:`data_types` are useful for grouping together and re-using a common set of properties, along with their types and default values.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-data-types/>`__.
    """

    @primitive_field(str)
    def description(self):
        """
        Description for the data type.
        
        :rtype: str
        """

    @object_dict_field(PropertyDefinition)
    def properties(self):
        """
        Dictionary of the data type properties.
        
        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @field_validator(derived_from_validator('data_types'))
    @primitive_field(str)
    def derived_from(self):
        """
        Parent data type.
        
        :rtype: str
        """

    @cachedmethod
    def _get_parent(self, context):
        return context.presentation.get_from_dict('service_template', 'data_types', self.derived_from)

    @cachedmethod
    def _get_properties(self, context):
        return ReadOnlyDict(get_inherited_property_definitions(context, self, 'properties'))

    def _validate(self, context):
        super(DataType, self)._validate(context)
        validate_data_type_name(context, self)
        self._get_properties(context)

    def _coerce_value(self, context, presentation, value, aspect):
        return coerce_data_type_value(context, presentation, self, value, aspect)
