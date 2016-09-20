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

from .. import install_aria_extensions
from ..consumption import ConsumerChain, Read, Validate, Template, Inputs, Plan
from ..utils import RestServer, JsonAsRawEncoder, print_exception, as_raw
from ..loading import LiteralLocation
from .utils import CommonArgumentParser, create_context_from_namespace
from collections import OrderedDict
from urlparse import urlparse, parse_qs
import urllib, os

API_VERSION = 1
PATH_PREFIX = 'openoapi/tosca/v%d' % API_VERSION
INDIRECT_VALIDATE_PATH = '%s/indirect/validate' % PATH_PREFIX
VALIDATE_PATH = '%s/validate' % PATH_PREFIX
PLAN_PATH = '%s/plan' % PATH_PREFIX
INDIRECT_PLAN_PATH = '%s/indirect/plan' % PATH_PREFIX

#
# Utils
#

def parse_path(handler):
    parsed = urlparse(urllib.unquote(handler.path))
    query = parse_qs(parsed.query, keep_blank_values=True)
    return parsed.path, query

def parse_indirect_payload(handler):
    try:
        payload = handler.json_payload
    except:
        handler.send_plain_text_response(400, 'Payload is not JSON\n')
        return None, None
    
    for key in payload.iterkeys():
        if key not in ('uri', 'inputs'):
            handler.send_plain_text_response(400, 'Payload has unsupported field: %s\n' % key)
            return None, None
    
    try:
        uri = payload['uri']
    except:
        handler.send_plain_text_response(400, 'Payload does not have required "uri" field\n')
        return None, None
    
    inputs = payload.get('inputs')
    
    return uri, inputs 

def validate(uri):
    context = create_context_from_namespace(args, uri=uri)
    ConsumerChain(context, (Read, Validate)).consume()
    return context

def plan(uri, inputs):
    context = create_context_from_namespace(args, uri=uri)
    if inputs:
        if isinstance(inputs, dict):
            for name, value in inputs.iteritems():
                context.deployment.set_input(name, value)
        else:
            context.args.append('--inputs=%s' % inputs)
    ConsumerChain(context, (Read, Validate, Template, Inputs, Plan)).consume()
    return context

def issues(context):
    return {'issues': [as_raw(i) for i in context.validation.issues]}

#
# Handlers
#

def validate_get(handler):
    path, _ = parse_path(handler)
    uri = path[len(VALIDATE_PATH) + 2:]
    context = validate(uri)
    return issues(context) if context.validation.has_issues else {}

def validate_post(handler):
    payload = handler.payload
    context = validate(LiteralLocation(payload))
    return issues(context) if context.validation.has_issues else {}

def indirect_validate_post(handler):
    uri, _ = parse_indirect_payload(handler)
    if uri is None:
        return None  
    context = validate(uri)
    return issues(context) if context.validation.has_issues else {}

def plan_get(handler):
    path, query = parse_path(handler)
    uri = path[len(PLAN_PATH) + 2:]
    inputs = query.get('inputs')
    if inputs:
        inputs = inputs[0]
    context = plan(uri, inputs)
    return issues(context) if context.validation.has_issues else context.deployment.plan_as_raw

def plan_post(handler):
    _, query = parse_path(handler)
    inputs = query.get('inputs')
    if inputs:
        inputs = inputs[0]
    payload = handler.payload
    context = plan(LiteralLocation(payload), inputs)
    return issues(context) if context.validation.has_issues else context.deployment.plan_as_raw

def indirect_plan_post(handler):
    uri, inputs = parse_indirect_payload(handler)
    if uri is None:
        return None
    context = plan(uri, inputs)
    return issues(context) if context.validation.has_issues else context.deployment.plan_as_raw

#
# Server
#

ROUTES = OrderedDict((
    ('^/$', {'file': 'index.html', 'media_type': 'text/html'}),
    ('^/' + VALIDATE_PATH, {'GET': validate_get, 'POST': validate_post, 'media_type': 'application/json'}),
    ('^/' + PLAN_PATH, {'GET': plan_get, 'POST': plan_post, 'media_type': 'application/json'}),
    ('^/' + INDIRECT_VALIDATE_PATH, {'POST': indirect_validate_post, 'media_type': 'application/json'}),
    ('^/' + INDIRECT_PLAN_PATH, {'POST': indirect_plan_post, 'media_type': 'application/json'})))

class ArgumentParser(CommonArgumentParser):
    def __init__(self):
        super(ArgumentParser, self).__init__(description='REST Server', prog='aria-rest')
        self.add_argument('--port', type=int, default=8204, help='HTTP port')
        self.add_argument('--root', help='web root directory')

def main():
    try:
        install_aria_extensions()
        
        global args
        args, _ = ArgumentParser().parse_known_args()

        rest_server = RestServer()
        rest_server.port = args.port
        rest_server.routes = ROUTES
        rest_server.static_root = args.root or os.path.join(os.path.dirname(__file__), 'web')
        rest_server.json_encoder = JsonAsRawEncoder(ensure_ascii=False, separators=(',', ':'))
        
        rest_server.start()

    except Exception as e:
        print_exception(e)

if __name__ == '__main__':
    main()
