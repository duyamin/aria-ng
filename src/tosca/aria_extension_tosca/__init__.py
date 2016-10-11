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

from aria import DSL_SPECIFICATION_PACKAGES
from aria.presentation import PRESENTER_CLASSES
from aria.loading import FILE_LOADER_SEARCH_PATHS
from .v1_0 import ToscaSimplePresenter1_0
from .nfv_v1_0 import ToscaSimpleNfvPresenter1_0
import os.path

def install_aria_extension():
    global PRESENTER_CLASSES
    PRESENTER_CLASSES += (ToscaSimplePresenter1_0, ToscaSimpleNfvPresenter1_0)
    
    # DSL specification
    DSL_SPECIFICATION_PACKAGES.append('aria_extension_tosca')
    
    # Imports
    the_dir = os.path.dirname(__file__)
    FILE_LOADER_SEARCH_PATHS.append(os.path.join(the_dir, 'profiles'))

MODULES = (
    'v1_0',
    'nfv_v1_0')

__all__ = (
    'MODULES',
    'install_aria_extension')
