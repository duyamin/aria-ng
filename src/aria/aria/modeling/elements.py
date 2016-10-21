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

from .utils import coerce_value
from .. import UnimplementedFunctionalityError
from ..utils import StrictDict, full_type_name, deepcopy_with_locators, puts
from collections import OrderedDict

class Function(object):
    """
    An intrinsic function.
    
    Serves as a placeholder for a value that should eventually be derived
    by calling the function.
    """
    
    @property
    def as_raw(self):
        raise UnimplementedFunctionalityError(full_type_name(self) + '.as_raw')

    def _evaluate(self, context, container):
        raise UnimplementedFunctionalityError(full_type_name(self) + '._evaluate')

    def __deepcopy__(self, memo):
        # Circumvent cloning in order to maintain our state
        return self

class Element(object):
    """
    Base class for :class:`ServiceInstance` elements.
    
    All elements support validation, diagnostic dumping, and representation as
    raw data (which can be translated into JSON or YAML) via :code:`as_raw`.
    """
    
    @property
    def as_raw(self):
        raise UnimplementedFunctionalityError(full_type_name(self) + '.as_raw')

    def validate(self, context):
        pass

    def coerce_values(self, context, container, report_issues):
        pass
    
    def dump(self, context):
        pass

class ModelElement(Element):
    """
    Base class for :class:`ServiceModel` elements.
    
    All model elements can be instantiated into :class:`ServiceInstance` elements. 
    """

    def instantiate(self, context, container):
        pass

class Parameter(ModelElement):
    """
    Represents a typed value.

    This class is used by both service model and service instance elements.
    """
    
    def __init__(self, type_name, value, description):
        self.type_name = type_name
        self.value = value
        self.description = description

    @property
    def as_raw(self):
        return OrderedDict((
            ('type_name', self.type_name),
            ('value', self.value),
            ('description', self.description)))

    def instantiate(self, context, container):
        return Parameter(self.type_name, self.value, self.description)

    def coerce_values(self, context, container, report_issues):
        if self.value is not None:
            self.value = coerce_value(context, container, self.value, report_issues)

class Metadata(ModelElement):
    """
    Custom values associated with the deployment template and its plans.

    This class is used by both service model and service instance elements.

    Properties:
    
    * :code:`values`: Dict of custom values
    """
    
    def __init__(self):
        self.values = StrictDict(key_class=basestring)

    @property
    def as_raw(self):
        return deepcopy_with_locators(self.values)

    def instantiate(self, context, container):
        r = Metadata()
        r.values.update(self.values)
        return r

    def dump(self, context):
        puts('Metadata:')
        with context.style.indent:
            for name, value in self.values.iteritems():
                puts('%s: %s' % (name, context.style.meta(value)))

