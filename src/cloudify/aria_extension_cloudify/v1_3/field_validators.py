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

from aria.presentation import type_validator

#
# PolicyDefinition
#

_policy_type_validator = type_validator('policy type', 'policy_types')

def policy_type_validator(field, presentation, context):
    """
    Makes sure that the field refers to an existing type defined in the root presenter.
    
    Used with the :func:`field_validator` decorator for the "type" field in :class:`PolicyDefinition`.
    """
    
    field._validate(presentation, context)
    
    value = getattr(presentation, field.name)
    if value is not None:
        # Check for built-in types
        if value == 'cloudify.policies.scaling':
            return
        
        _policy_type_validator(field, presentation, context)
