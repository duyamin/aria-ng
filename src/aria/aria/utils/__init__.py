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

from .openclose import OpenClose
from .caching import cachedmethod, HasCachedMethods
from .formatting import JsonAsRawEncoder, YamlAsRawDumper, full_type_name, safe_str, safe_repr, string_list_as_string, as_raw, as_agnostic, json_dumps, yaml_dumps, yaml_loads
from .collections import FrozenList, EMPTY_READ_ONLY_LIST, FrozenDict, EMPTY_READ_ONLY_DICT, StrictList, StrictDict, merge, prune, deepcopy_with_locators, copy_locators, is_removable
from .exceptions import print_exception, print_traceback
from .imports import import_fullname, import_modules
from .threading import ExecutorException, FixedThreadPoolExecutor, LockedList
from .uris import as_file
from .argparse import ArgumentParser
from .console import puts, colored, indent
from .rest_server import RestServer, RestRequestHandler
from .rest_client import call_rest

__all__ = (
    'OpenClose',
    'cachedmethod',
    'HasCachedMethods',
    'JsonAsRawEncoder',
    'YamlAsRawDumper',
    'full_type_name',
    'safe_str',
    'safe_repr',
    'string_list_as_string',
    'as_raw',
    'as_agnostic',
    'json_dumps',
    'yaml_dumps',
    'yaml_loads',
    'FrozenList',
    'EMPTY_READ_ONLY_LIST',
    'FrozenDict',
    'EMPTY_READ_ONLY_DICT',
    'StrictList',
    'StrictDict',
    'merge',
    'prune',
    'deepcopy_with_locators',
    'copy_locators',
    'is_removable',
    'print_exception',
    'print_traceback',
    'import_fullname',
    'import_modules',
    'ExecutorException',
    'FixedThreadPoolExecutor',
    'LockedList',
    'as_file',
    'ArgumentParser',
    'puts',
    'colored',
    'indent',
    'RestServer',
    'RestRequestHandler',
    'call_rest')
