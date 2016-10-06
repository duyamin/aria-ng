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
from .exceptions import LoaderError, DocumentNotFoundError
from ..utils import StrictList
from requests import Session
from requests.exceptions import ConnectionError
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache

SESSION = None
SESSION_CACHE_PATH = '/tmp'

URI_LOADER_SEARCH_PATHS = StrictList(value_class=basestring)

class UriLoader(Loader):
    """
    Base class for ARIA URI loaders.
    
    Extracts a document from a URI.
    
    Note that the "file:" schema is not supported: :class:`FileTextLoader` should
    be used instead.
    """

    def __init__(self, context, location, origin_location, headers={}):
        self.context = context
        self.location = location
        self.headers = headers
        self.search_paths = StrictList(value_class=basestring) 
        self.response = None

        def add_search_path(search_path):
            if search_path not in self.search_paths:
                self.search_paths.append(search_path)

        def add_search_paths(search_paths):
            for search_path in search_paths:
                add_search_path(search_path)

        if origin_location is not None:
            origin_search_path = origin_location.uri_search_path
            if origin_search_path is not None:
                add_search_path(origin_search_path)

        add_search_paths(context.uri_search_paths)
        add_search_paths(URI_LOADER_SEARCH_PATHS)
    
    def open(self):
        global SESSION
        if SESSION is None:
            SESSION = CacheControl(Session(), cache=FileCache(SESSION_CACHE_PATH))
            
        try:
            self.response = SESSION.get(self.location.uri, headers=self.headers)
            status = self.response.status_code
            if status == 404:
                self.response = None
                raise DocumentNotFoundError('URI not found: "%s"' % self.location)
            elif status != 200:
                self.response = None
                raise LoaderError('URI request error %d: "%s"' % (status, self.location))
        except ConnectionError as e:
            raise LoaderError('URI connection error: "%s"' % self.location, cause=e)
        except Exception as e:
            raise LoaderError('URI error: "%s"' % self.location, cause=e)

class UriTextLoader(UriLoader):
    """
    ARIA URI text loader.
    """

    def load(self):
        if self.response is not None:
            try:
                return self.response.text
            except Exception as e:
                raise LoaderError('URI: %s' % self.location, cause=e)
        return None
