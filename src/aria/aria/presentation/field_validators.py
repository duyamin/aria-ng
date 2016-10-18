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

from .utils import report_issue_for_unknown_type, report_issue_for_parent_is_self, report_issue_for_unknown_parent_type, report_issue_for_circular_type_hierarchy
from ..validation import Issue
from types import FunctionType

def type_validator(type_name, *types_dict_names):
    """
    Makes sure that the field refers to an existing type defined in the root presenter.
    
    The arguments from the second onwards are used to locate a nested field under
    :code:`service_template` under the root presenter. The first of these can optionally
    be a function, in which case it will be called to convert type names. This can be used
    to support shorthand type names, aliases, etc.    
    
    Can be used with the :func:`field_validator` decorator.
    """

    types_dict_names, convert = _parse_types_dict_names(types_dict_names)
    
    def validator_fn(field, presentation, context):
        field.default_validate(presentation, context)

        # Make sure type exists
        value = getattr(presentation, field.name)
        if value is not None:
            types_dict = context.presentation.get('service_template', *types_dict_names) or {}

            if convert:
                value = convert(context, value, types_dict)

            if value not in types_dict:
                report_issue_for_unknown_type(context, presentation, type_name, field.name)
        
    return validator_fn

def list_type_validator(type_name, *types_dict_names):
    """
    Makes sure that the field's elements refer to existing types defined in the root presenter.
    
    Assumes that the field is a list.
    
    The arguments from the second onwards are used to locate a nested field under
    :code:`service_template` under the root presenter. The first of these can optionally
    be a function, in which case it will be called to convert type names. This can be used
    to support shorthand type names, aliases, etc.    
    
    Can be used with the :func:`field_validator` decorator.
    """

    types_dict_names, convert = _parse_types_dict_names(types_dict_names)

    def validator_fn(field, presentation, context):
        field.default_validate(presentation, context)
        
        # Make sure types exist
        values = getattr(presentation, field.name)
        if values is not None:
            types_dict = context.presentation.get('service_template', *types_dict_names) or {}

            for value in values:
                if convert:
                    value = convert(context, value, types_dict)
    
                if value not in types_dict:
                    report_issue_for_unknown_type(context, presentation, type_name, field.name)
        
    return validator_fn

def list_length_validator(length):
    """
    Makes sure the field has exactly a specific number of elements.
    
    Assumes that the field is a list.
    
    Can be used with the :func:`field_validator` decorator.
    """

    def validator_fn(field, presentation, context):
        field.default_validate(presentation, context)
        
        # Make sure list has exactly the length
        values = getattr(presentation, field.name)
        if isinstance(values, list):
            if len(values) != length:
                context.validation.report('field "%s" does not have exactly %d elements in "%s"' % (field.name, length, presentation._fullname), locator=presentation._get_child_locator(field.name), level=Issue.FIELD)
        
    return validator_fn

def derived_from_validator(*types_dict_names):
    """
    Makes sure that the field refers to a valid parent type defined in the root presenter.
    
    The arguments are used to locate a nested field under
    :code:`service_template` under the root presenter. The first of these can optionally
    be a function, in which case it will be called to convert type names. This can be used
    to support shorthand type names, aliases, etc.    
    
    Can be used with the :func:`field_validator` decorator.
    """

    types_dict_names, convert = _parse_types_dict_names(types_dict_names)

    def validator_fn(field, presentation, context):
        field.default_validate(presentation, context)

        value = getattr(presentation, field.name)
        if value is not None:
            types_dict = context.presentation.get('service_template', *types_dict_names) or {}
            
            if convert:
                value = convert(context, value, types_dict)
            
            # Make sure not derived from self
            if value == presentation._name:
                report_issue_for_parent_is_self(context, presentation, field.name)
            # Make sure derived from type exists
            elif value not in types_dict:
                report_issue_for_unknown_parent_type(context, presentation, field.name)
            else:
                # Make sure derivation hierarchy is not circular
                hierarchy = [presentation._name]
                p = presentation
                while p.derived_from is not None:
                    derived_from = p.derived_from
                    if convert:
                        derived_from = convert(context, derived_from, types_dict)

                    if derived_from == p._name:
                        # This should cause a validation issue at that type
                        break
                    elif derived_from not in types_dict:
                        # This should cause a validation issue at that type
                        break
                    p = types_dict[derived_from]
                    if p._name in hierarchy:
                        report_issue_for_circular_type_hierarchy(context, presentation, field.name)
                        break
                    hierarchy.append(p._name)

    return validator_fn

#
# Utils
#

def _parse_types_dict_names(types_dict_names):
    """
    If the first element in the array is a function, extracts it out.
    """
    
    convert = None
    if isinstance(types_dict_names[0], FunctionType):
        convert = types_dict_names[0]
        types_dict_names = types_dict_names[1:]
    return types_dict_names, convert
