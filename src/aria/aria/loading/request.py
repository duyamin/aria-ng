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
from requests import Session
from requests.exceptions import ConnectionError
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache

SESSION = None
SESSION_CACHE_PATH = '/tmp'

class RequestLoader(Loader):
    """
    Base class for ARIA URI loaders.
    
    Extracts a document from a URI.
    
    Note that the "file:" schema is not supported: :class:`FileTextLoader` should
    be used instead.
    """

    def __init__(self, context, uri, headers={}):
        self.context = context
        self.uri = uri
        self.headers = headers
        self._response = None
    
    def open(self):
        global SESSION
        if SESSION is None:
            SESSION = CacheControl(Session(), cache=FileCache(SESSION_CACHE_PATH))
            
        try:
            self._response = SESSION.get(self.uri, headers=self.headers)
        except ConnectionError as e:
            raise LoaderError('request connection error: "%s"' % self.uri, cause=e)
        except Exception as e:
            raise LoaderError('request error: "%s"' % self.uri, cause=e)

        status = self._response.status_code
        if status == 404:
            self._response = None
            raise DocumentNotFoundError('document not found: "%s"' % self.uri)
        elif status != 200:
            self._response = None
            raise LoaderError('request error %d: "%s"' % (status, self.uri))

class RequestTextLoader(RequestLoader):
    """
    ARIA URI text loader.
    """

    def load(self):
        if self._response is not None:
            try:
                return self._response.text
            except Exception as e:
                raise LoaderError('request error: %s' % self.uri, cause=e)
        return None
