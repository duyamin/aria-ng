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

from .reader import Reader
from .exceptions import ReaderSyntaxError
from .locator import Locator
from collections import OrderedDict
from ruamel import yaml # @UnresolvedImport

class YamlLocator(Locator):
    """
    Map for agnostic raw data read from YAML.
    """
    
    def parse(self, yaml_loader, node, location):
        if isinstance(node, yaml.SequenceNode):
            self.children = []
            for n in node.value:
                locator = YamlLocator(location, n.start_mark.line + 1, n.start_mark.column + 1)
                self.children.append(locator)
                locator.parse(yaml_loader, n, location)
        elif isinstance(node, yaml.MappingNode):
            yaml_loader.flatten_mapping(node)
            self.children = {}
            for key, n in node.value:
                locator = YamlLocator(location, key.start_mark.line + 1, key.start_mark.column + 1)
                self.children[key.value] = locator
                locator.parse(yaml_loader, n, location)

def construct_yaml_map(self, node):
    data = OrderedDict()
    yield data
    value = self.construct_mapping(node)
    data.update(value)

yaml.constructor.SafeConstructor.add_constructor(u'tag:yaml.org,2002:map', construct_yaml_map)

class YamlReader(Reader):
    """
    ARIA YAML reader.
    """
    
    def read(self):
        data = self.load()
        try:
            data = unicode(data)
            #yaml_loader = yaml.RoundTripLoader(data) # Bug: https://bitbucket.org/ruamel/yaml/issues/60/roundtriploader-does-not-handle-anchors
            yaml_loader = yaml.SafeLoader(data)
            try:
                node = yaml_loader.get_single_node()
                locator = YamlLocator(self.loader.location, 0, 0)
                if node is None:
                    raw = OrderedDict()
                else:
                    locator.parse(yaml_loader, node, self.loader.location)
                    raw = yaml_loader.construct_document(node)
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
