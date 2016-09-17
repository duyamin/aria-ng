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

from .exceptions import PresenterError, PresenterNotFoundError
from .context import PresentationContext
from .presenter import Presenter
from .presentation import Value, PresentationBase, Presentation, AsIsPresentation
from .source import PRESENTER_CLASSES, PresenterSource, DefaultPresenterSource
from .null import NULL
from .fields import Field, has_fields, short_form_field, allow_unknown_fields, primitive_field, primitive_list_field, primitive_dict_field, primitive_dict_unknown_fields, object_field, object_list_field, object_dict_field, object_sequenced_list_field, object_dict_unknown_fields, field_getter, field_setter, field_validator
from .field_validators import type_validator, list_type_validator, list_length_validator, derived_from_validator
from .utils import validate_no_short_form, validate_no_unknown_fields, validate_known_fields, report_issue_for_unknown_type, report_issue_for_parent_is_self, report_issue_for_circular_type_hierarchy

__all__ = (
    'PresenterError',
    'PresenterNotFoundError',
    'PresentationContext',
    'Presenter',
    'Value',
    'PresentationBase',
    'Presentation',
    'AsIsPresentation',
    'PresenterSource',
    'PRESENTER_CLASSES',
    'DefaultPresenterSource',
    'NULL',
    'Field',
    'has_fields',
    'short_form_field',
    'allow_unknown_fields',
    'primitive_field',
    'primitive_list_field',
    'primitive_dict_field',
    'primitive_dict_unknown_fields',
    'object_field',
    'object_list_field',
    'object_dict_field',
    'object_sequenced_list_field',
    'object_dict_unknown_fields',
    'field_getter',
    'field_setter',
    'field_validator',
    'type_validator',
    'list_type_validator',
    'list_length_validator',
    'derived_from_validator',
    'validate_no_short_form',
    'validate_no_unknown_fields',
    'validate_known_fields',
    'report_issue_for_unknown_type',
    'report_issue_for_parent_is_self',
    'report_issue_for_circular_type_hierarchy')
