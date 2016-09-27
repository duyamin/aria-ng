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

from aria.utils import deepcopy_with_locators

def prepare_deployment_plan(plan, inputs=None, **kwargs):
    """
    Prepare a plan for deployment
    """
    
    #print '!!! prepare_deployment_plan', inputs, kwargs
    
    if inputs:
        for input_name, the_input in inputs.iteritems():
            plan['inputs'][input_name] = deepcopy_with_locators(the_input)
            
    # TODO: now that we have inputs, we should scan properties and inputs
    # and evaluate functions
    
    return plan
