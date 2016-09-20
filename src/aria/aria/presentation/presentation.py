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

from .null import none_to_null
from .utils import get_locator, validate_no_short_form, validate_no_unknown_fields, validate_known_fields
from ..utils import HasCachedMethods, full_type_name, deepcopy_with_locators, puts

class Value(object):
    def __init__(self, the_type, value):
        self.type = deepcopy_with_locators(the_type)
        self.value = deepcopy_with_locators(value)

class PresentationBase(HasCachedMethods):
    """
    Base class for ARIA presentation classes.
    """
    
    def __init__(self, name=None, raw=None, container=None):
        self._name = name
        self._raw = raw
        self._container = container

    def _validate(self, context):
        """
        Validates the presentation while reporting errors in the validation context but
        *not* raising exceptions.
        
        The base class does not thing, but subclasses may override this for specialized
        validation.
        """

    @property
    def _fullname(self):
        """
        Always returns a usable full name of the presentation, whether it itself is named,
        or recursing to its container, and finally defaulting to the class name. 
        """
        
        if self._name is not None:
            return self._name
        elif self._container is not None:
            return self._container._fullname
        return full_type_name(self)

    @property
    def _locator(self):
        """
        Attempts to return the most relevant locator, whether we have one, or recursing
        to our container.
        
        :rtype: :class:`aria.reading.Locator`
        """
        
        return get_locator(self._raw, self._container)

    def _get_child_locator(self, *names):
        """
        Attempts to return the locator of one our children. Will default to our locator
        if not found.
        
        :rtype: :class:`aria.reading.Locator`
        """
        
        if hasattr(self._raw, '_locator'):
            locator = self._raw._locator
            if locator is not None:
                return locator.get_child(*names)
        return self._locator

    def _dump(self, context):
        """
        Emits a colorized representation.
        
        The base class will emit a sensible default representation of the fields,
        (by calling :code:`_dump_content`), but subclasses may override this for specialized
        dumping. 
        """
        
        if self._name:
            puts(context.style.node(self._name))
            with context.style.indent:
                self._dump_content(context)
        else:
            self._dump_content(context)
                            
    def _dump_content(self, context, field_names=None):
        """
        Emits a colorized representation of the contents.
        
        The base class will call :code:`_dump_field` on all the fields, but subclasses may
        override this for specialized dumping. 
        """

        if field_names:
            for field_name in field_names:
                self._dump_field(context, field_name)
        elif hasattr(self, '_iter_field_names'):
            for field_name in self._iter_field_names():
                self._dump_field(context, field_name)
        else:
            puts(context.style.literal(self._raw))

    def _dump_field(self, context, field_name):
        """
        Emits a colorized representation of the field.
        
        According to the field type, this may trigger nested recursion. The nested
        types will delegate to their :code:`_dump` methods.
        """
        
        field = self.FIELDS[field_name]
        field.dump(self, context) 

    def _clone(self, container=None):
        """
        Creates a clone of this presentation, optionally allowing for a new container.
        """
        
        raw = deepcopy_with_locators(self._raw)
        if container is None:
            container = self._container
        return self.__class__(name=self._name, raw=raw, container=container)

class Presentation(PresentationBase):
    """
    Base class for ARIA presentations. A presentation is a Pythonic wrapper around
    agnostic raw data, adding the ability to read and modify the data with proper
    validation. 
    
    ARIA presentation classes will often be decorated with @has_fields, as that
    mechanism automates a lot of field-specific validation. However, that is not a
    requirement.
    
    Make sure that your utility property and method names begin with a "_", because
    those names without a "_" prefix are normally reserved for fields. 
    """
    
    def _validate(self, context):
        validate_no_short_form(self, context)
        validate_no_unknown_fields(self, context)
        validate_known_fields(self, context)

class AsIsPresentation(PresentationBase):
    """
    Base class for trivial ARIA presentations that provide the raw value as is.
    """
    
    # TODO: support type coersion
    
    @property
    def value(self):
        return none_to_null(self._raw)
    
    @value.setter
    def value(self, value):
        self._raw = value

    def _dump(self, context):
        if hasattr(self._raw, '_dump'):
            self._raw._dump(context)
        else:
            super(AsIsPresentation, self)._dump(context)
