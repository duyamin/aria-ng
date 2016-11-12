# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# NodeTemplate, RelationshipTemplate
#

def get_default_raw_from_copy(presentation, field_name):
    """
    Used for the :code:`_get_default_raw` field hook.
    """

    copy = presentation._raw.get('copy')
    if copy is not None:
        templates = getattr(presentation._container, field_name)
        if templates is not None:
            template = templates.get(copy)
            if template is not None:
                return template._raw
    return None
