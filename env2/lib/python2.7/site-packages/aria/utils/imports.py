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

def import_fullname(name, paths=[]):
    """
    Imports a variable or class based on a full name, optionally searching for it in the paths.
    """
    
    if name is None:
        return None
    
    def do_import(name):
        if name and ('.' in name):
            module_name, name = name.rsplit('.', 1)
            return getattr(__import__(module_name, fromlist=[name], level=0), name)
        else:
            raise ImportError('import not found: %s' % name)
    
    try:
        return do_import(name)
    except:
        for p in paths:
            try:
                return do_import('%s.%s' % (p, name))
            except Exception as e:
                raise ImportError('cannot import %s, because %s' % (name, e))

    raise ImportError('import not found: %s' % name)

def import_modules(name):
    """
    Imports a module and all its sub-modules, recursively. Relies on modules defining a 'MODULES' attribute
    listing their sub-module names.
    """
    
    module = __import__(name, fromlist=['MODULES'], level=0)
    if hasattr(module, 'MODULES'):
        for m in module.MODULES:
            import_modules('%s.%s' % (name, m))
