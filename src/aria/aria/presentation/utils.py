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

from ..validation import Issue
from ..utils import safe_repr

def get_locator(*values):
    """
    Gets the first available locator.
        
    :rtype: :class:`aria.reading.Locator`
    """
    
    for v in values:
        if hasattr(v, '_locator'):
            locator = v._locator
            if locator is not None:
                return locator
    return None

def validate_no_short_form(presentation, context):
    """
    Makes sure that we can use short form definitions only if we allowed it.
    """
    
    if (not hasattr(presentation, 'SHORT_FORM_FIELD')) and (not isinstance(presentation._raw, dict)):
        context.validation.report('short form not allowed for field "%s"' % presentation._fullname, locator=presentation._locator, level=Issue.BETWEEN_FIELDS)

def validate_no_unknown_fields(presentation, context):
    """
    Make sure that we can use unknown fields only if we allowed it.
    """
    
    if (not getattr(presentation, 'ALLOW_UNKNOWN_FIELDS', False)) and (not context.validation.allow_unknown_fields) and isinstance(presentation._raw, dict) and hasattr(presentation, 'FIELDS'):
        for k in presentation._raw:
            if k not in presentation.FIELDS:
                context.validation.report('field "%s" is not supported in "%s"' % (k, presentation._fullname), locator=presentation._get_child_locator(k), level=Issue.BETWEEN_FIELDS)

def validate_known_fields(presentation, context):
    """
    Validates all known fields.
    """
    
    if hasattr(presentation, '_iter_fields'):
        for _, field in presentation._iter_fields():
            field.validate(presentation, context)

def report_issue_for_unknown_type(context, presentation, type_name, field_name, value=None):
    if value is None:
        value = getattr(presentation, field_name)
    context.validation.report('"%s" refers to an unknown %s in "%s": %s' % (field_name, type_name, presentation._fullname, safe_repr(value)), locator=presentation._get_child_locator(field_name), level=Issue.BETWEEN_TYPES)

def report_issue_for_parent_is_self(context, presentation, field_name):
    context.validation.report('parent type of "%s" is self' % presentation._fullname, locator=presentation._get_child_locator(field_name), level=Issue.BETWEEN_TYPES)

def report_issue_for_unknown_parent_type(context, presentation, field_name):
    context.validation.report('unknown parent type "%s" in "%s"' % (getattr(presentation, field_name), presentation._fullname), locator=presentation._get_child_locator(field_name), level=Issue.BETWEEN_TYPES)

def report_issue_for_circular_type_hierarchy(context, presentation, field_name):
    context.validation.report('"%s" of "%s" creates a circular type hierarchy' % (getattr(presentation, field_name), presentation._fullname), locator=presentation._get_child_locator(field_name), level=Issue.BETWEEN_TYPES)
