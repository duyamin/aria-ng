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

from .utils import full_type_name
from collections import OrderedDict

DSL_SPECIFICATION = {}
DSL_SPECIFICATION_PACKAGES = []

URL = {
    'tosca-simple-profile-1.0': 'http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/csprd02/TOSCA-Simple-Profile-YAML-v1.0-csprd02.html',
    'tosca-simple-nfv-1.0': 'http://docs.oasis-open.org/tosca/tosca-nfv/v1.0/tosca-nfv-v1.0.html'}

def dsl_specification(section, spec):
    """
    Decorator for TOSCA specification.
    
    Used for documentation and standards compliance.
    """
    
    def decorator(o):
        sp = DSL_SPECIFICATION.get(spec)
        if sp is None:
            sp = {}
            DSL_SPECIFICATION[spec] = sp
        if section in sp:
            raise Exception('you cannot specify the same @dsl_specification twice, consider adding \'-1\', \'-2\', etc.: %s, %s' % (spec, section))

        url = URL.get(spec)
        if url:
            doc = o.__doc__
            if doc is not None:
                url_start = doc.find(url)
                if url_start != -1:
                    url_end = doc.find('>', url_start + len(url))
                    if url_end != -1:
                        url = doc[url_start:url_end]

        sp[section] = OrderedDict((
            ('code', full_type_name(o)),
            ('url', url)))
        try:
            setattr(o, DSL_SPECIFICATION, {section: section, spec: spec})
        except:
            pass
        return o
    return decorator

def iter_spec(spec):
    sections = DSL_SPECIFICATION[spec]
    keys = sections.keys()
    def key(value):
        try:
            parts = value.split('-', 1)
            first = (int(v) for v in parts[0].split('.'))
            second = parts[1] if len(parts) > 1 else None
            return (first, second)
        except ValueError:
            return value
    keys.sort(key=key)
    for key in keys:
        yield key, sections[key]
