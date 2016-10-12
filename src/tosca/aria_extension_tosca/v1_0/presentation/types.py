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

def convert_shorthand_to_full_type_name(context, types_dict, name):
    if types_dict:
        if name not in types_dict:
            for full_name, v in types_dict.iteritems():
                extensions = v._extensions
                if extensions:
                    shorthand_name = extensions.get('shorthand_name')
                    if shorthand_name == name:
                        return full_name
    return name

def get_type_by_full_or_shorthand_name(context, name, *types_dict_names):
    types = context.presentation.get('service_template', *types_dict_names)
    if types:
        v = types.get(name)
        if v is not None:
            # Full name
            return v
        for v in types.itervalues():
            extensions = v._extensions
            if extensions:
                shorthand_name = extensions.get('shorthand_name')
                if shorthand_name == name:
                    # Shorthand name
                    return v
    return None
