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

from .relationships import is_contained_in

COMPUTE_NODE_NAME = 'cloudify.nodes.Compute'

def is_host(context, node_or_node_template):
    return context.deployment.node_types.is_descendant(COMPUTE_NODE_NAME, node_or_node_template.type_name)

def find_host_node_template(context, node_template):
    if is_host(context, node_template):
        return node_template
    
    for requirement in node_template.requirements:
        if is_contained_in(context, requirement.relationship_template):
            return find_host_node_template(context, context.deployment.template.node_templates.get(requirement.target_node_template_name))

    return None

def find_host_node(context, node):
    node_template = context.deployment.template.node_templates.get(node.template_name)
    if is_host(context, node_template):
        return node
    
    for relationship in node.relationships:
        if is_contained_in(context, relationship):
            return find_host_node(context, context.deployment.plan.nodes.get(relationship.target_node_id))

    return None

def find_hosted_node_templates(context, node_template):
    hosted = []
    if is_host(context, node_template):
        for t in context.deployment.template.node_templates.itervalues():
            if (t is not node_template) and (find_host_node_template(context, t) is node_template):
                hosted.append(t)
    return hosted
