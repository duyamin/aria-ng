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

from .collections import deepcopy_with_locators, ReadOnlyList, ReadOnlyDict, StrictList, StrictDict
import json
from collections import OrderedDict
from ruamel import yaml # @UnresolvedImport
from types import MethodType

# Add our types to ruamel.yaml (for round trips)
yaml.representer.RoundTripRepresenter.add_representer(ReadOnlyList, yaml.representer.RoundTripRepresenter.represent_list)
yaml.representer.RoundTripRepresenter.add_representer(ReadOnlyDict, yaml.representer.RoundTripRepresenter.represent_dict)
yaml.representer.RoundTripRepresenter.add_representer(StrictList, yaml.representer.RoundTripRepresenter.represent_list)
yaml.representer.RoundTripRepresenter.add_representer(StrictDict, yaml.representer.RoundTripRepresenter.represent_dict)

# Without this, ruamel.yaml will output "!!omap" types, which is technically correct but unnecessarily verbose for our uses 
yaml.representer.RoundTripRepresenter.add_representer(OrderedDict, yaml.representer.RoundTripRepresenter.represent_dict)

class JsonAsRawEncoder(json.JSONEncoder):
    """
    A :class:`JSONEncoder` that will use the :code:`as_raw` property of objects
    if available.
    """
    
    def default(self, o):
        try:
            return iter(o)
        except TypeError:
            if hasattr(o, 'as_raw'):
                return as_raw(o)
            return str(o)
        return super(JsonAsRawEncoder, self).default(self, o)

class YamlAsRawDumper(yaml.dumper.RoundTripDumper):
    """
    A :class:`RoundTripDumper` that will use the :code:`as_raw` property of objects
    if available.
    """
    
    def represent_data(self, data):
        if hasattr(data, 'as_raw'):
            data = as_raw(data)
        return super(YamlAsRawDumper, self).represent_data(data)

def classname(o):
    """
    The full class name of an object.
    """
    
    return '%s.%s' % (o.__class__.__module__, o.__class__.__name__)

def safe_str(s):
    """
    Like :code:`str` coercion, but makes sure that Unicode strings are properly
    encoded, and will never return None.
    """
    
    try:
        return str(s)
    except UnicodeEncodeError:
        s = unicode(s)
        return s.encode('utf8')

def as_raw(value):
    """
    Converts values using their :code:`as_raw` property, if it exists, recursively.
    """
    
    if hasattr(value, 'as_raw'):
        value = value.as_raw
        if isinstance(value, MethodType):
            # Old-style Python classes don't support properties
            value = value()
    elif isinstance(value, list):
        value = deepcopy_with_locators(value)
        for i in range(len(value)):
            value[i] = as_raw(value[i])
    elif isinstance(value, dict):
        value = deepcopy_with_locators(value)
        for k, v in value.iteritems():
            value[k] = as_raw(v)
    return value

def as_agnostic(value):
    """
    Converts subclasses of list and dict to standard lists and dicts, recursively.
    
    Useful for creating human-readable output of structures.
    """

    if isinstance(value, list):
        value = list(value)
    elif isinstance(value, dict):
        value = dict(value)
        
    if isinstance(value, list):
        for i in range(len(value)):
            value[i] = as_agnostic(value[i])
    elif isinstance(value, dict):
        for k, v in value.iteritems():
            value[k] = as_agnostic(v)
            
    return value

def json_dumps(value, indent):
    """
    JSON dumps that supports Unicode and the :code:`as_raw` property of objects
    if available. 
    """
    
    return json.dumps(value, indent=indent, ensure_ascii=False, cls=JsonAsRawEncoder)

def yaml_dumps(value, indent):
    """
    YAML dumps that supports Unicode and the :code:`as_raw` property of objects
    if available. 
    """
    
    return yaml.dump(value, indent=indent, allow_unicode=True, Dumper=YamlAsRawDumper)
