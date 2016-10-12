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

from .loader import Loader
from .file import FileTextLoader
from .request import RequestTextLoader
from .exceptions import DocumentNotFoundError
from ..utils import StrictList, as_file
import os

URI_LOADER_PREFIXES = StrictList(value_class=basestring)

class UriTextLoader(Loader):
    """
    Base class for ARIA URI loaders.
    
    Supports a list of search prefixes that are tried in order if the URI cannot be found.
    """
    
    def __init__(self, context, location, origin_location):
        self.context = context
        self.location = location
        self.origin_location = origin_location
        self._prefixes = StrictList(value_class=basestring)
        self._loader = None

        def add_prefix(prefix):
            if prefix not in self._prefixes:
                self._prefixes.append(prefix)

        def add_prefixes(prefixes):
            for prefix in prefixes:
                add_prefix(prefix)

        if origin_location is not None:
            origin_prefix = origin_location.prefix
            if origin_prefix:
                add_prefix(origin_prefix)
        
        add_prefixes(context.prefixes)
        add_prefixes(URI_LOADER_PREFIXES)

    def open(self):
        try:
            self._open(self.location.uri)
            return
        except DocumentNotFoundError:
            for prefix in self._prefixes:
                uri = os.path.join(prefix, self.location.uri)
                try:
                    self._open(uri)
                    return
                except DocumentNotFoundError:
                    pass
        raise DocumentNotFoundError('document not found at URI: "%s"' % self.location)

    def close(self):
        if self.loader is not None:
            self.loader.close()

    def load(self):
        return self.loader.load() if self.loader is not None else None

    def _open(self, uri):
        the_file = as_file(uri)
        if the_file is not None:
            uri = the_file
            loader = FileTextLoader(self.context, uri)
        else:
            loader = RequestTextLoader(self.context, uri)
        loader.open()
        self.loader = loader
        self.location.uri = uri
