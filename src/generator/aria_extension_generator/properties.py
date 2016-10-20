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

from aria.exceptions import InvalidValueError
from aria.utils import safe_repr
from functools import wraps
from types import MethodType
from collections import OrderedDict

class Prop(object):
    def __init__(self, fn=None, cls=None, default=None, required=False, status='supported'):
        self.name = None
        self.fn = fn
        self.cls = cls
        self.default = default
        self.required = required
        self.status = status
    
    def validate(self, value):
        if value is None:
            if self.required:
                raise InvalidValueError('required property must have a value: %s' % self.name)
            else:
                return None

        if self.cls and not isinstance(value, self.cls):
            try:
                return self.cls(value)
            except ValueError:
                raise InvalidValueError('property must be coercible to %s: %s=%s' % (self.cls.__name__, self.name, safe_repr(value)))

        return value

def has_validated_properties_iter_validated_property_names(self):
    for name in self.__class__.PROPERTIES:
        yield name

def has_validated_properties_iter_validated_properties(self):
    for name in self.__class__.PROPERTIES:
        yield name, self.__dict__[name]

def has_validated_properties(cls):
    """
    Class decorator for validated property support.
    
    1. Adds a `PROPERTIES` class property that is a dict of all the fields.
       Will inherit and merge `PROPERTIES` properties from base classes if
       they have them.
    
    2. Generates automatic `@property` implementations for the fields
       with the help of a set of special function decorators. The unvalidated
       value can be accessed via the "_" prefix.

    The class will also gain two utility methods,
    `_iter_validated_property_names` and `_iter_validated_properties`.
    """

    # Make sure we have PROPERTIES
    if 'PROPERTIES' not in cls.__dict__:
        setattr(cls, 'PROPERTIES', OrderedDict())
    
    # Inherit PROPERTIES from base classes 
    for base in cls.__bases__:
        if hasattr(base, 'PROPERTIES'):
            cls.PROPERTIES.update(base.PROPERTIES)
    
    for name, prop in cls.__dict__.iteritems():
        if isinstance(prop, Prop):
            # Accumulate
            cls.PROPERTIES[name] = prop
            
            prop.name = name

            # Convert to Python property
            def closure(prop):
                # By convention, we will have the getter wrap the original function.
                # (It is, for example, where the Python help() function will look for
                # docstrings.)

                @wraps(prop.fn)
                def getter(self):
                    value = getattr(self, '_' + prop.name)
                    if value is None:
                        value = prop.default
                        setattr(self, '_' + prop.name, value)
                    return prop.validate(value)
                    
                def setter(self, value):
                    value = prop.validate(value)
                    setattr(self, '_' + prop.name, value)
                    
                return property(fget=getter, fset=setter)
                
            setattr(cls, name, closure(prop))

    # Bind methods
    setattr(cls, '_iter_validated_property_names', MethodType(has_validated_properties_iter_validated_property_names, None, cls))
    setattr(cls, '_iter_validated_properties', MethodType(has_validated_properties_iter_validated_properties, None, cls))
                
    return cls

def validated_property(cls, default=None, required=False, status='supported'):
    """
    Function decorator for primitive fields.
    
    The function must be a method in a class decorated with :func:`has_validated_properties`.
    """
    def decorator(fn):
        return Prop(fn=fn, cls=cls, default=default, required=required, status=status)
    return decorator
