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

from ..utils import StrictList, StrictDict, puts

class Type(object):
    def __init__(self, name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        
        self.name = name
        self.children = StrictList(value_class=Type)
        
    def get_parent(self, name):
        for child in self.children:
            if child.name == name:
                return self
            parent = child.get_parent(name)
            if parent is not None:
                return parent
        return None
    
    def get_descendant(self, name):
        if self.name == name:
            return self
        for child in self.children:
            found = child.get_descendant(name)
            if found is not None:
                return found
        return None
    
    def is_descendant(self, base_name, name):
        base = self.get_descendant(base_name)
        if base is not None:
            if base.get_descendant(name) is not None:
                return True
        return False

    def iter_descendants(self):
        for child in self.children:
            yield child
            for d in child.iter_descendants():
                yield d

    def dump(self, context):
        if self.name:
            puts(context.style.type(self.name))
        with context.style.indent:
            for child in self.children:
                child.dump(context)

class RelationshipType(Type):
    def __init__(self, name):
        super(RelationshipType, self).__init__(name)
        
        self.properties = StrictDict(key_class=basestring)
        self.source_interfaces = StrictDict(key_class=basestring)
        self.target_interfaces = StrictDict(key_class=basestring)

class PolicyType(Type):
    def __init__(self, name):
        super(PolicyType, self).__init__(name)

        self.implementation = None     
        self.properties = StrictDict(key_class=basestring)

class TypeHierarchy(Type):
    def __init__(self):
        self.name = None
        self.children = StrictList(value_class=Type)
