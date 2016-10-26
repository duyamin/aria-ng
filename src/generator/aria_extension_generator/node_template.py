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

from .writer import Writer, repr_assignment
from collections import OrderedDict

class CodeNodeTemplate(object):
    def __init__(self, generator, name, type_name, description):
        self.generator = generator
        self.name = name
        self.type = type_name
        self.description = description
        self.assignments = OrderedDict()
        self.relationships = []
        
    def relate(self, w):
        if self.relationships:
            for r in self.relationships:
                w.write('context.relate(self.%s, %s(context), self.%s)' % (self.name, self.generator.get_classname(r.type), r.target))
    
    def __str__(self):
        with Writer() as w:
            if self.description:
                w.write('%s' % self.description.strip(), prefix='# ')
            w.write('self.%s = %s(context)' % (self.name, self.generator.get_classname(self.type)))
            if self.assignments:
                for k, v in self.assignments.iteritems():
                    w.write('self.%s.%s = %s' % (self.name, k, repr_assignment(v)))
            return str(w)
