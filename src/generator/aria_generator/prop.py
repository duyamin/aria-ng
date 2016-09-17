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

from .writer import Writer, one_line
from aria.utils import as_agnostic

class CodeProperty(object):
    def __init__(self, generator, name, description=None, type_name=None, default=None):
        self.generator = generator
        self.name = name
        self.description = description
        self.type = type_name
        self.default = default

    @property
    def docstring(self):
        with Writer() as w:
            w.put(':param')
            if self.type:
                w.put(' %s' % self.type)
            w.put(' %s: %s' % (self.name, one_line(self.description or self.name)))
            return str(w)
    
    @property
    def signature(self):
        with Writer() as w:
            w.put('%s=%s' % (self.name, repr(as_agnostic(self.default))))
            #if self.default is not None:
            #    w.put('=%s' % repr(as_agnostic(self.default)))
            return str(w)
