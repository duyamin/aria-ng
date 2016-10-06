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

from .exceptions import LoaderNotFoundError
from .location import LiteralLocation, UriLocation
from .literal import LiteralLoader
from .file import FileTextLoader
from .uri import UriTextLoader

class LoaderSource(object):
    """
    Base class for ARIA loader sources.
    
    Loader sources provide appropriate :class:`Loader` instances for locations.
    
    A :class:`LiteralLocation` is handled specially by wrapping the literal value
    in a :class:`LiteralLoader`.
    """
    
    def get_loader(self, context, location, origin_location):
        if isinstance(location, LiteralLocation):
            return LiteralLoader(location)
        
        raise LoaderNotFoundError('location: %s' % location)

class DefaultLoaderSource(LoaderSource):
    """
    The default ARIA loader source will generate a :class:`UriTextLoader` for
    locations that are non-file URIs, and a :class:`FileTextLoader` for file
    URIs.
    """
    
    def get_loader(self, context, location, origin_location):
        if isinstance(location, UriLocation):
            if location.as_file is not None:
                return FileTextLoader(context, location, origin_location)
            else:
                return UriTextLoader(context, location, origin_location)
            
        return super(DefaultLoaderSource, self).get_loader(context, location, origin_location)
