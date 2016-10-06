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

from ..utils import as_file
import os

class Location(object):
    def is_equivalent(self, location):
        return False
    
    @property
    def file_search_path(self):
        return None

    @property
    def uri_search_path(self):
        return None

class UriLocation(Location):
    def __init__(self, uri):
        self.uri = uri

    def is_equivalent(self, location):
        return isinstance(location, UriLocation) and (location.uri == self.uri)

    @property
    def file_search_path(self):
        the_file = self.as_file
        return os.path.dirname(the_file) if the_file is not None else None

    @property
    def uri_search_path(self):
        the_file = self.as_file
        return os.path.dirname(self.uri) if the_file is None else None
        # Yes, it's weird, but dirname handles URIs, too: http://stackoverflow.com/a/35616478/849021
    
    @property
    def as_file(self):
        return as_file(self.uri)

    def __str__(self):
        return self.uri

class LiteralLocation(Location):
    def __init__(self, content):
        self.content = content

    def is_equivalent(self, location):
        return isinstance(location, LiteralLocation) and (location.content == self.content)
    
    def __str__(self):
        return '<literal>'
