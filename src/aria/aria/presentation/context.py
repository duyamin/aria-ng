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

from .source import DefaultPresenterSource

class PresentationContext(object):
    """
    Properties:
    
    * :code:`location`: From where we will generate the presenter
    * :code:`presenter`: The generated presenter instance
    * :code:`presenter_source`: For finding presenter classes
    * :code:`presenter_class`: Overrides :code:`presenter_source` with a specific class
    * :code:`threads`: Number of threads to use when reading data
    * :code:`timeout`: Timeout in seconds for loading data
    * :code:`print_exceptions`: Whether to print exceptions while reading data
    """
    
    def __init__(self):
        self.location = None
        self.presenter = None
        self.presenter_source = DefaultPresenterSource()
        self.presenter_class = None # overrides
        self.threads = 8
        self.timeout = 10 # in seconds
        self.print_exceptions = False

    def get(self, *names):
        o = self.presenter
        if (o is not None) and names:
            for name in names:
                o = getattr(o, name, None)
                if o is None:
                    break
        return o

    def get_from_dict(self, *names):
        if names:
            o = self.get(*names[:-1])
            if isinstance(o, dict):
                return o.get(names[-1])
        return None
