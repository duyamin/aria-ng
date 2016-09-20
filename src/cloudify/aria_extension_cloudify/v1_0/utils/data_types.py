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

from ..functions import get_function
from aria.validation import Issue
from aria.utils import import_fullname, deepcopy_with_locators, full_type_name

#
# PropertyDefinition
#

def get_data_type(context, presentation):
    """
    Returns the type, whether it's a complex data type (a DataType instance) or a primitive (a Python primitive type class).
    """
    
    the_type = presentation.type
    
    if the_type is None:
        return None
    
    # Try complex data type
    data_type = context.presentation.presenter.data_types.get(the_type) if context.presentation.presenter.data_types is not None else None
    if data_type is not None:
        return data_type
    
    # Try primitive data type
    return get_primitive_data_type(the_type)

#
# Utils
#

PRIMITIVE_DATA_TYPES = {
    'string': str,
    'integer': int,
    'float': float,
    'boolean': bool}

def get_primitive_data_type(type_name):
    return PRIMITIVE_DATA_TYPES.get(type_name)

def get_data_type_name(the_type):
    """
    Returns the name of the type, whether it's a DataType, a primitive type, or another class.
    """
    
    if hasattr(the_type, '_name'):
        return the_type._name
    return full_type_name(the_type)

def find_functions(context, presentation, value):
    if isinstance(value, dict):
        for k, v in value.iteritems():
            is_function, fn = get_function(context, presentation, v)
            if is_function:
                value[k] = fn
            else:
                find_functions(context, presentation, v)
    elif isinstance(value, list):
        for index in range(len(value)):
            v = value[index]
            is_function, fn = get_function(context, presentation, v)
            if is_function:
                value[index] = fn
            else:
                find_functions(context, presentation, v)

def coerce_value(context, presentation, the_type, value, aspect=None):
    """
    Returns the value after it's coerced to its type, reporting validation errors if it cannot be coerced.
    
    Supports both complex data types and primitives.
    
    Data types can use the :code:`coerce_value` extension to hook their own specialized function. If the extension
    is present, we will delegate to that hook.
    """

    is_function, fn = get_function(context, presentation, value)
    if is_function:
        return fn
    
    if the_type is None:
        if isinstance(value, dict):
            value = deepcopy_with_locators(value)
            find_functions(context, presentation, value)
        return value

    # Delegate to 'coerce_value' extension
    if hasattr(the_type, '_get_extension'):
        coerce_value_fn_name = the_type._get_extension('coerce_value')
        if coerce_value_fn_name is not None:
            coerce_value_fn = import_fullname(coerce_value_fn_name)
            return coerce_value_fn(context, presentation, the_type, value, aspect)

    if hasattr(the_type, '_coerce_value'):
        # Delegate to _coerce_value (likely a DataType instance)
        return the_type._coerce_value(context, presentation, value, aspect)

    # Coerce to primitive type
    return coerce_to_primitive(context, presentation, the_type, value, aspect)

def coerce_to_primitive(context, presentation, primitive_type, value, aspect=None):
    """
    Returns the value after it's coerced to a primitive type, translating exceptions to validation errors if it cannot be coerced.
    """
    
    if value is None:
        return None

    try:
        # Coerce
        value = primitive_type(value)
    except ValueError as e:
        report_issue_for_bad_format(context, presentation, primitive_type, value, aspect, e)
        value = None
    except TypeError as e:
        report_issue_for_bad_format(context, presentation, primitive_type, value, aspect, e)
        value = None
    
    return value

def report_issue_for_bad_format(context, presentation, the_type, value, aspect, e):
    aspect = None
    if aspect == 'default':
        aspect = '"default" value'
    elif aspect is not None:
        aspect = '"%s" aspect'  
    
    if aspect is not None:
        context.validation.report('%s for field "%s" is not a valid "%s": %s' % (aspect, presentation._name or presentation._container._name, get_data_type_name(the_type), repr(value)), locator=presentation._locator, level=Issue.BETWEEN_FIELDS, exception=e)
    else:
        context.validation.report('field "%s" is not a valid "%s": %s' % (presentation._name or presentation._container._name, get_data_type_name(the_type), repr(value)), locator=presentation._locator, level=Issue.BETWEEN_FIELDS, exception=e)
