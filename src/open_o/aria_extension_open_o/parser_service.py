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

from aria import install_aria_extensions
from aria.tools.rest import validate_get, validate_post, model_get, model_post, instance_get, instance_post, indirect_validate_post, indirect_instance_post, indirect_model_post
from aria.tools.utils import CommonArgumentParser
from aria.utils import RestServer, JsonAsRawEncoder, print_exception, start_daemon, stop_daemon, status_daemon
from collections import OrderedDict
import os

API_VERSION = 1
PATH_PREFIX = 'openoapi/tosca/v%d' % API_VERSION
VALIDATE_PATH = '%s/validate' % PATH_PREFIX
INDIRECT_VALIDATE_PATH = '%s/indirect/validate' % PATH_PREFIX
MODEL_PATH = '%s/model' % PATH_PREFIX
INDIRECT_MODEL_PATH = '%s/indirect/model' % PATH_PREFIX
INSTANCE_PATH = '%s/instance' % PATH_PREFIX
INDIRECT_INSTANCE_PATH = '%s/indirect/instance' % PATH_PREFIX

DEFAULT_PORT = 8204

ROUTES = OrderedDict((
    ('^/$', {'file': 'index.html', 'media_type': 'text/html'}),
    ('^/' + VALIDATE_PATH, {'GET': validate_get, 'POST': validate_post, 'media_type': 'application/json'}),
    ('^/' + MODEL_PATH, {'GET': model_get, 'POST': model_post, 'media_type': 'application/json'}),
    ('^/' + INSTANCE_PATH, {'GET': instance_get, 'POST': instance_post, 'media_type': 'application/json'}),
    ('^/' + INDIRECT_VALIDATE_PATH, {'POST': indirect_validate_post, 'media_type': 'application/json'}),
    ('^/' + INDIRECT_MODEL_PATH, {'POST': indirect_model_post, 'media_type': 'application/json'}),
    ('^/' + INDIRECT_INSTANCE_PATH, {'POST': indirect_instance_post, 'media_type': 'application/json'})))

class ArgumentParser(CommonArgumentParser):
    def __init__(self):
        super(ArgumentParser, self).__init__(description='Open-O Common TOSCA Parser Service', prog='open-o-common-tosca-parser-service')
        self.add_argument('command', nargs='?', help='daemon command: start, stop, restart, or status')
        self.add_argument('--port', type=int, default=DEFAULT_PORT, help='HTTP port')
        self.add_argument('--root', help='web root directory')
        self.add_argument('--rundir', help='pid and log files directory for daemons (defaults to user home)')

def main():
    try:
        install_aria_extensions()
        
        arguments, _ = ArgumentParser().parse_known_args()

        rest_server = RestServer()
        rest_server.configuration = arguments
        rest_server.port = arguments.port
        rest_server.routes = ROUTES
        rest_server.static_root = arguments.root or os.path.join(os.path.dirname(__file__), 'web')
        rest_server.json_encoder = JsonAsRawEncoder(ensure_ascii=False, separators=(',', ':'))
        
        if arguments.command:
            rundir = os.path.abspath(arguments.rundir or os.path.expanduser('~'))
            pidfile_path = os.path.join(rundir, '.open-o-common-tosca-parser-service.pid')
            if arguments.command == 'start':
                log_path = os.path.join(rundir, 'open-o-common-tosca-parser-service.log')
                context = start_daemon(pidfile_path, log_path)
                if context is not None:
                    with context:
                        rest_server.start(daemon=True)
            elif arguments.command == 'stop':
                stop_daemon(pidfile_path)
            elif arguments.command == 'status':
                status_daemon(pidfile_path)
            else:
                print('Unknown command: %s' % arguments.command)
        else:
            rest_server.start()

    except Exception as e:
        print_exception(e)

if __name__ == '__main__':
    main()
