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

from .exceptions import LoaderError, LoaderNotFoundError, DocumentNotFoundError
from .context import LoadingContext
from .loader import Loader
from .source import LoaderSource, DefaultLoaderSource
from .location import Location, UriLocation, LiteralLocation
from .literal import LiteralLoader
from .uri import SESSION, SESSION_CACHE_PATH, URI_LOADER_SEARCH_PATHS, UriLoader, UriTextLoader
from .file import FILE_LOADER_SEARCH_PATHS, FileTextLoader

__all__ = (
    'LoaderError',
    'LoaderNotFoundError',
    'DocumentNotFoundError',
    'LoadingContext',
    'Loader',
    'LoaderSource',
    'DefaultLoaderSource',
    'Location',
    'UriLocation',
    'LiteralLocation',
    'LiteralLoader',
    'SESSION',
    'SESSION_CACHE_PATH',
    'URI_LOADER_SEARCH_PATHS',
    'UriLoader',
    'UriTextLoader',
    'FILE_LOADER_SEARCH_PATHS',
    'FileTextLoader')
