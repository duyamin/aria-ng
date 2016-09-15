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

from .locator import LocatableString, LocatableInt, LocatableFloat
from .reader import Reader
from .exceptions import ReaderSyntaxError
from .locator import Locator
from collections import OrderedDict
from ruamel import yaml # @UnresolvedImport

# Add our types to ruamel.yaml (for round trips)
yaml.representer.RoundTripRepresenter.add_representer(LocatableString, yaml.representer.RoundTripRepresenter.represent_unicode)
yaml.representer.RoundTripRepresenter.add_representer(LocatableInt, yaml.representer.RoundTripRepresenter.represent_int)
yaml.representer.RoundTripRepresenter.add_representer(LocatableFloat, yaml.representer.RoundTripRepresenter.represent_float)

class YamlLocator(Locator):
    """
    Map for agnostic raw data read from YAML.
    """
    
    def parse(self, yaml_loader, node, location):
        def child(n, key=None):
            locator = YamlLocator(location, n.start_mark.line + 1, n.start_mark.column + 1)
            if key is not None:
                self.children[key] = locator
            else:
                self.children.append(locator)
            locator.parse(yaml_loader, n, location)
        
        if isinstance(node, yaml.SequenceNode):
            self.children = []
            for n in node.value:
                child(n)
        elif isinstance(node, yaml.MappingNode):
            self.children = {}
            for k, n in node.value:
                if k.tag == u'tag:yaml.org,2002:merge':
                    for merge_k, merge_n in n.value:
                        child(merge_n, merge_k.value)
                else:
                    child(n, k.value)

class YamlReader(Reader):
    """
    ARIA YAML reader.
    """
    
    def read(self):
        data = self.load()
        try:
            data = unicode(data)
            yaml_loader = yaml.RoundTripLoader(data)
            try:
                node = yaml_loader.get_single_node()
                locator = YamlLocator(self.loader.location, 0, 0)
                if node is not None:
                    locator.parse(yaml_loader, node, self.loader.location)
                    raw = yaml_loader.construct_document(node)
                else:
                    raw = OrderedDict()
                #locator.dump()
                setattr(raw, '_locator', locator)
                return raw
            finally:
                yaml_loader.dispose()
        except Exception as e:
            if isinstance(e, yaml.parser.MarkedYAMLError):
                context = e.context or 'while parsing'
                problem = e.problem
                line = e.problem_mark.line
                column = e.problem_mark.column
                snippet = e.problem_mark.get_snippet()
                raise ReaderSyntaxError('YAML %s: %s %s' % (e.__class__.__name__, problem, context), location=self.loader.location, line=line, column=column, snippet=snippet, cause=e)
            else:
                raise ReaderSyntaxError('YAML: %s' % e, cause=e)
