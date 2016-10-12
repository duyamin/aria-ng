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

from .. import VERSION
from ..consumption import ConsumptionContext
from ..loading import UriLocation, URI_LOADER_PREFIXES
from ..utils import import_fullname, ArgumentParser

class BaseArgumentParser(ArgumentParser):
    def __init__(self, description, **kwargs):
        super(BaseArgumentParser, self).__init__(description='ARIA version %s %s' % (VERSION, description), **kwargs)
    
class CommonArgumentParser(BaseArgumentParser):
    def __init__(self, description, **kwargs):
        super(CommonArgumentParser, self).__init__(description='ARIA version %s %s' % (VERSION, description), **kwargs)
        self.add_argument('--loader-source', default='aria.loading.DefaultLoaderSource', help='loader source class for the parser')
        self.add_argument('--reader-source', default='aria.reading.DefaultReaderSource', help='reader source class for the parser')
        self.add_argument('--presenter-source', default='aria.presentation.DefaultPresenterSource', help='presenter source class for the parser')
        self.add_argument('--presenter', help='force use of this presenter class in parser')
        self.add_argument('--prefix', nargs='*', help='prefixes for imports')
        self.add_argument('--debug', action='store_true', help='print debug info')

    def parse_known_args(self, args=None, namespace=None):
        namespace, args = super(CommonArgumentParser, self).parse_known_args(args, namespace)
        
        if namespace.prefix:
            for prefix in namespace.prefix:
                URI_LOADER_PREFIXES.append(prefix)
        
        return namespace, args

def create_context_from_namespace(ns, **kwargs):
    args = vars(ns).copy()
    args.update(kwargs)
    return create_context(**args)

def create_context(uri, loader_source, reader_source, presenter_source, presenter, debug, **kwargs):
    context = ConsumptionContext()
    context.loading.loader_source = import_fullname(loader_source)()
    context.reading.reader_source = import_fullname(reader_source)()
    context.presentation.location=UriLocation(uri) if isinstance(uri, basestring) else uri
    context.presentation.presenter_source = import_fullname(presenter_source)()
    context.presentation.presenter_class = import_fullname(presenter)
    context.presentation.print_exceptions = debug
    return context
