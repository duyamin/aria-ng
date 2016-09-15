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

from ..utils import puts, colored, indent

# We are inheriting the primitive types in order to add the ability to set an attribute (_locator) on them.

class LocatableString(unicode):
    pass

class LocatableInt(int):
    pass

class LocatableFloat(float):
    pass

def wrap(value):
    if isinstance(value, basestring):
        return True, LocatableString(value)
    elif isinstance(value, int) and not isinstance(value, bool): # Note: bool counts as int in Python! 
        return True, LocatableInt(value)
    elif isinstance(value, float):
        return True, LocatableFloat(value)
    return False, value

class Locator(object):
    """
    Stores location information (line and column numbers) for agnostic raw data.
    """
    def __init__(self, location, line, column):
        self.location = location
        self.line = line
        self.column = column
        self.children = None
    
    def get_child(self, name):
        if isinstance(self.children, dict):
            return self.children.get(name, self)
        return self

    def get_grandchild(self, name1, name2):
        if isinstance(self.children, dict):
            locator1 = self.children.get(name1)
            if (locator1 is not None) and (locator1.children is not None):
                return locator1.children.get(name2, locator1)
        return self
    
    def link(self, raw):
        try:
            setattr(raw, '_locator', self)
        except AttributeError:
            pass
        
        if isinstance(raw, list):
            for i in range(len(raw)):
                r = raw[i]
                wrapped, r = wrap(r)
                if wrapped:
                    raw[i] = r
                try:
                    self.children[i].link(r)
                except KeyError:
                    raise ValueError('location map does not match agnostic raw data: %d' % i)
        elif isinstance(raw, dict):
            for k, r in raw.iteritems():
                wrapped, r = wrap(r)
                if wrapped:
                    raw[k] = r
                try:
                    self.children[k].link(r)
                except KeyError:
                    raise ValueError('location map does not match agnostic raw data: %s' % k)
    
    def merge(self, locator):
        if isinstance(self.children, dict) and isinstance(locator.children, dict):
            for k, m in locator.children.iteritems():
                if k in self.children:
                    self.children[k].merge(m)
                else:
                    self.children[k] = m

    def dump(self, key=None):
        if key:
            puts('%s "%s":%d:%d' % (colored.red(key), colored.blue(self.location), self.line, self.column))
        else:
            puts('"%s":%d:%d' % (colored.blue(self.location), self.line, self.column))
        if isinstance(self.children, list):
            with indent(2):
                for m in self.children:
                    m.dump()
        elif isinstance(self.children, dict):
            with indent(2):
                for k, m in self.children.iteritems():
                    m.dump(k)

    def __str__(self):
        # Should be in same format as Issue.locator_as_str
        return '"%s":%d:%d' % (self.location, self.line, self.column)
