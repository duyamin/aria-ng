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


from aria.utils import safe_repr

from .writer import Writer, one_line


class CodeProperty(object):
    def __init__(self, generator, name, description=None, type_name=None, default=None):
        self.generator = generator
        self.name = name
        self.description = description
        self.type = type_name
        self.default = default

    @property
    def docstring(self):
        with Writer() as writer:
            writer.put(':param')
            if self.type:
                writer.put(' %s' % self.type)
            writer.put(' %s: %s' % (self.name, one_line(self.description or self.name)))
            return str(writer)

    @property
    def signature(self):
        with Writer() as writer:
            writer.put('%s=%s' % (self.name, safe_repr(self.default)))
            #if self.default is not None:
            #    writer.put('=%s' % safe_repr(self.default))
            return str(writer)
