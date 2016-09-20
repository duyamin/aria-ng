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
    
    def get_child(self, *names):
        if (not names) or (not isinstance(self.children, dict)):
            return self
        name = names[0]
        if name not in self.children:
            return self
        child = self.children[name]
        return child.get_child(names[1:])

    def link(self, raw, path=None):
        if hasattr(raw, '_locator'):
            # This can happen when we use anchors
            return
        
        try:
            setattr(raw, '_locator', self)
        except AttributeError:
            return
        
        if isinstance(raw, list):
            for i in range(len(raw)):
                r = raw[i]
                wrapped, r = wrap(r)
                if wrapped:
                    raw[i] = r
                child_path = '%s.%d' % (path, i) if path else str(i)
                try:
                    self.children[i].link(r, child_path)
                except KeyError:
                    raise ValueError('location map does not match agnostic raw data: %s' % child_path)
        elif isinstance(raw, dict):
            for k, r in raw.iteritems():
                wrapped, r = wrap(r)
                if wrapped:
                    raw[k] = r
                child_path = '%s.%s' % (path, k) if path else k
                try:
                    self.children[k].link(r, child_path)
                except KeyError:
                    raise ValueError('location map does not match agnostic raw data: %s' % child_path)
    
    def merge(self, locator):
        if isinstance(self.children, dict) and isinstance(locator.children, dict):
            for k, l in locator.children.iteritems():
                if k in self.children:
                    self.children[k].merge(l)
                else:
                    self.children[k] = l

    def dump(self, key=None):
        if key:
            puts('%s "%s":%d:%d' % (colored.red(key), colored.blue(self.location), self.line, self.column))
        else:
            puts('"%s":%d:%d' % (colored.blue(self.location), self.line, self.column))
        if isinstance(self.children, list):
            with indent(2):
                for l in self.children:
                    l.dump()
        elif isinstance(self.children, dict):
            with indent(2):
                for k, l in self.children.iteritems():
                    l.dump(k)

    def __str__(self):
        # Should be in same format as Issue.locator_as_str
        return '"%s":%d:%d' % (self.location, self.line, self.column)
