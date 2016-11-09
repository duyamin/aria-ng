# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from aria.utils import full_type_name, puts

from .exceptions import ExecutorNotFoundError
from .cloudify import HostAgentExecutor, CentralDeploymentAgentExecutor


class Relationship(object):
    def __init__(self, source, relationship, target):
        self.source = source
        self.relationship = relationship
        self.target = target


class ExecutionContext(object):
    """
    Service execution context.
    """
    def __init__(self, style):
        self.service = None
        self.relationships = []
        self.style = style
        self.executors = {}
        self.executors['host_agent'] = HostAgentExecutor()
        self.executors['central_deployment_agent'] = CentralDeploymentAgentExecutor()

    def relate(self, source, relationship, target):
        """
        Creates the graph.
        """
        self.relationships.append(Relationship(source, relationship, target))

    def executor(self, name):
        if name not in self.executors:
            raise ExecutorNotFoundError(name)
        return self.executors[name]

    def get_relationship_from(self, source):
        relationships = []
        for relationship in self.relationships:
            if relationship.source == source:
                relationships.append(relationship)
        return relationships

    def get_node_name(self, node):
        for name in self.nodes:
            the_node = getattr(self.service, name)
            if node == the_node:
                return name
        return None

    @property
    def inputs(self):
        return getattr(self.service.__class__, 'INPUTS', [])

    @property
    def outputs(self):
        return getattr(self.service.__class__, 'OUTPUTS', [])

    @property
    def nodes(self):
        return getattr(self.service.__class__, 'NODES', [])

    @property
    def workflows(self):
        return getattr(self.service.__class__, 'WORKFLOWS', [])

    def dump(self):
        if self.inputs:
            puts(self.style.section('Inputs:'))
            with self.style.indent:
                for name in self.inputs:
                    puts('%s' % self.style.property(name))
        if self.outputs:
            puts(self.style.section('Outputs:'))
            with self.style.indent:
                for name in self.outputs:
                    prop = getattr(self.service.__class__, name)
                    puts('%s: %s' % (self.style.property(name), prop.__doc__.strip()))
        if self.nodes:
            puts(self.style.section('Topology:'))
            with self.style.indent:
                for name in self.nodes:
                    node = getattr(self.service, name)
                    puts('%s: %s' % (self.style.node(name), self.style.type(full_type_name(node))))
                    relationships = self.get_relationship_from(node)
                    if relationships:
                        with self.style.indent:
                            for relationship in relationships:
                                puts('-> %s %s' %
                                     (self.style.type(full_type_name(relationship.relationship)),
                                      self.style.node(self.get_node_name(relationship.target))))
