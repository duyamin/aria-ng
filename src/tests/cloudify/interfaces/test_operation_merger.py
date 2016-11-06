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

import testtools

from cloudify.framework.abstract_test_parser import AbstractTestParser

# from . import validate


def raw_operation_mapping(implementation=None,
                          inputs=None,
                          executor=None,
                          max_retries=None,
                          retry_interval=None):

    """
    Used to simulate a possible operation written in
    the blueprint.
    """

    inputs = inputs or {}
    result = dict(operation=implementation,
                  inputs=inputs,
                  executor=executor,
                  max_retries=max_retries,
                  retry_interval=retry_interval)
    return result


def _create_simple_operation(implementation=None, **_):
    operation = (
        'create: {0}\n'.format(implementation or "{}")
    )
    return operation


def _create_operation_mapping(implementation=None,
                              inputs=None,
                              executor=None,
                              max_retries=None,
                              retry_interval=None):

    operation = (
        'create:\n'
    )

    if implementation:
        operation += '          implementation: {0}\n'.format(implementation)
    if executor:
        operation += '          executor: {0}\n'.format(executor)
    if max_retries:
        operation += '          max_retries: {0}\n'.format(max_retries)
    if retry_interval:
        operation += '          retry_interval: {0}\n'.format(retry_interval)
    if inputs:
        operation += '          inputs:\n'
        for inpt in inputs.keys():
            if type(inputs[inpt]) is dict:
                operation += '            {0}:\n'.format(inpt)
                for prop in inputs[inpt]:
                    operation += '              {0}: {1}\n'.format(prop, inputs[inpt][prop])
            else:
                operation += '            {0}: {1}\n'.format(inpt, inputs[inpt])
    return operation


def create_operation_in_node_type(implementation=None,
                                  inputs=None,
                                  executor=None,
                                  max_retries=None,
                                  retry_interval=None,
                                  operation_mapping=True):

    operation_creation_method = \
        _create_operation_mapping if operation_mapping else _create_simple_operation

    result = (
        '\n'
        'node_types:\n'
        '  test_type:\n'
        '    interfaces:\n'
        '      test_interface1:\n'
        '        {0}\n'.format(operation_creation_method(
            implementation=implementation,
            inputs=inputs,
            executor=executor,
            max_retries=max_retries,
            retry_interval=retry_interval
        ))
    )
    return result


def create_operation_in_node_template(implementation='',
                                      inputs=None,
                                      executor='',
                                      max_retries=None,
                                      retry_interval=None,
                                      operation_mapping=True):

    operation_creation_method = \
        _create_operation_mapping if operation_mapping else _create_simple_operation

    result = (
        '\n'
        'node_templates:\n'
        '  test_node:\n'
        '    type: test_type\n'
        '    interfaces:\n'
        '      test_interface1:\n'
        '        {0}\n'.format(operation_creation_method(
            implementation=implementation,
            inputs=inputs,
            executor=executor,
            max_retries=max_retries,
            retry_interval=retry_interval
        ))
    )
    return result

NO_OP = raw_operation_mapping()
TYPE_WITH_NONE_OP = (
    '\n'
    'node_types:\n'
    '  test_type:\n'
    '    interfaces:\n'
    '      test_interface1:\n'
    '        create:\n'
)
TEMPLATE_WITH_NONE_OP = (
    '\n'
    'node_templates:\n'
    '  test_node:\n'
    '    type: test_type\n'
    '    interfaces:\n'
    '      test_interface1:\n'
    '        create:\n'
)


class NodeTemplateNodeTypeOperationMergerTest(AbstractTestParser):

    def _assert_operations(self,
                           yaml,
                           expected_operation,
                           dsl_version=AbstractTestParser.BASIC_VERSION_SECTION_DSL_1_0):
        plan = self.parse(yaml, dsl_version=dsl_version)
        actual_operation = plan['nodes'][0]['operations']['create']
        if expected_operation is None:
            self.assertIsNone(actual_operation)
        else:
            for prop in expected_operation.keys():
                if prop == 'operation' and actual_operation[prop]:
                    self.assertEqual(expected_operation[prop],
                                     actual_operation['plugin'] + '.' + actual_operation[prop])
                else:
                    self.assertEqual(expected_operation[prop], actual_operation[prop])

    def create_dsl_blueprint(self,
                             node_type1_operation,
                             node_template1_operation,
                             node_type2_operation=None,
                             node_template2_operation=None,
                             add_plugin=True):

        plugin = self.BASIC_PLUGIN if add_plugin else ''

        dsl_blueprint = """

tosca_definitions_version: cloudify_dsl_1_3
node_types:
    type1:
        interfaces:
            interface1:
                op1: {node_type1_operation}
    type2:
        interfaces:
            interface1:
                op1: {node_type2_operation}
node_templates:
    node1:
        type: type1
        interfaces:
            interface1:
                op1: {node_template1_operation}
    node2:
        type: type2
        interfaces:
            interface1:
                op1: {node_template2_operation}
{plugin}
""".format(node_type1_operation=self.create_dsl_operation(node_type1_operation),
           node_type2_operation=self.create_dsl_operation(node_type2_operation),
           node_template1_operation=self.create_dsl_operation(node_template1_operation),
           node_template2_operation=self.create_dsl_operation(node_template2_operation),
           plugin=plugin)

        return dsl_blueprint

    @staticmethod
    def create_dsl_operation(operation):

        if not operation:
            return '{}'

        dsl_operation = ''
        for line in operation.splitlines():
            dsl_operation += '\n{indentation}{operation_attribute}'.format(
                indentation=20*' ',
                operation_attribute=line)
        return dsl_operation

    @staticmethod
    def create_parsed_operation(operation):
        return {
            'operation': operation.get('operation') or None,
            'plugin': operation.get('plugin') or None,
            'inputs': operation.get('inputs') or {},
            'executor': operation.get('executor') or None,
            'max_retries': None,
            'retry_interval': None,
            'has_intrinsic_functions': False
        }

    def assert_operation_merger(self,
                                dsl_blueprint,
                                expected_template_merger,
                                expected_type_merger=None):
        parsed_blueprint = self.parse(dsl_blueprint)

        actual_template_merger = parsed_blueprint['nodes'][0]['operations']['op1']
        self.assertEqual(expected_template_merger, actual_template_merger)

        if expected_type_merger:
            actual_type_merger = parsed_blueprint['nodes'][1]['operations']['op1']
            self.assertEqual(expected_type_merger, actual_type_merger)

    def test_no_op_overrides_no_op(self):

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='',
            node_template1_operation='',
            node_type2_operation='',
            add_plugin=False)
        expected_template_merger = self.create_parsed_operation({})
        expected_type_merger = self.create_parsed_operation({})

        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_no_op_overrides_operation_mapping_no_inputs(self):
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'inputs: {}',
            node_template1_operation='',
            node_type2_operation='')
        expected_template_merger = self.create_parsed_operation({})
        expected_type_merger = self.create_parsed_operation({})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_no_op_overrides_operation_mapping(self):

        yaml = self.BASIC_PLUGIN + create_operation_in_node_type(
            implementation='test_plugin.tasks.create',
            inputs={}
        ) + create_operation_in_node_template()
        self._assert_operations(yaml, NO_OP)

    def test_no_op_overrides_none(self):

        yaml = """
node_types:
    test_type:
        interfaces:
          test_interface1:
            create:
        """ + create_operation_in_node_template()
        self._assert_operations(yaml, NO_OP)

    def test_no_op_overrides_operation_mapping_with_executor(self):

        yaml = self.BASIC_PLUGIN + create_operation_in_node_type(
            implementation='test_plugin.tasks.create',
            executor='host_agent'
        ) + create_operation_in_node_template()
        self._assert_operations(yaml, NO_OP)

    def test_operation_overrides_no_op(self):

        yaml = self.BASIC_PLUGIN + \
            create_operation_in_node_type() + \
            create_operation_in_node_template(
                implementation='test_plugin.tasks.create',
                operation_mapping=False
            )
        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            executor='central_deployment_agent'))

    def test_operation_overrides_operation_mapping(self):

        yaml = self.BASIC_PLUGIN + \
            create_operation_in_node_type(
                implementation='test_plugin.tasks.create',
                inputs={
                    'key': {
                        'default': 'value'
                    }
                }
            ) + create_operation_in_node_template(
                implementation='test_plugin.tasks.create-overridden',
                operation_mapping=False
            )
        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            executor='central_deployment_agent'))

    def test_operation_overrides_operation_mapping_no_inputs(self):

        yaml = self.BASIC_PLUGIN + \
            create_operation_in_node_type(
               implementation='test_plugin.tasks.create',
            ) + create_operation_in_node_template(
                implementation='test_plugin.tasks.create-overridden',
                operation_mapping=False
            )
        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            executor='central_deployment_agent'))

    def test_operation_overrides_none(self):
        yaml = self.BASIC_PLUGIN + TYPE_WITH_NONE_OP + create_operation_in_node_template(
            implementation='test_plugin.tasks.create-overridden',
            operation_mapping=False
        )
        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            executor='central_deployment_agent'))

    def test_operation_overrides_operation_mapping_with_executor(self):

        yaml = self.BASIC_PLUGIN + create_operation_in_node_type(
            implementation='test_plugin.tasks.create',
            executor='central_deployment_agent'
        ) + create_operation_in_node_template(
            implementation='test_plugin.tasks.create-overridden',
            operation_mapping=False
        )
        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            executor='central_deployment_agent'))

    def test_operation_overrides_operation(self):
        yaml = self.BASIC_PLUGIN + create_operation_in_node_type(
            implementation='test_plugin.tasks.create',
            operation_mapping=False
        ) + create_operation_in_node_template(
            implementation='test_plugin.tasks.create-overridden',
            operation_mapping=False
        )
        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            executor='central_deployment_agent'))

    def test_operation_mapping_overrides_no_op(self):

        yaml = self.BASIC_PLUGIN + create_operation_in_node_type() + \
               create_operation_in_node_template(
            implementation='test_plugin.tasks.create',
            inputs={
                'key': 'value'
            }
        )
        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={'key': 'value'},
            executor='central_deployment_agent'))

    def test_operation_mapping_overrides_operation_mapping(self):
        yaml = self.BASIC_PLUGIN + create_operation_in_node_type(
            implementation='test_plugin.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        ) + create_operation_in_node_template(
            implementation='test_plugin.tasks.create-overridden',
            inputs={
               'key': 'value-overridden'
            }
        )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            inputs={'key': 'value-overridden'},
            executor='central_deployment_agent'))

    def test_operation_mapping_overrides_operation_mapping_no_inputs(self):
        yaml = self.BASIC_PLUGIN + create_operation_in_node_type(
            implementation='test_plugin.tasks.create'
        ) + create_operation_in_node_template(
            implementation='test_plugin.tasks.create-overridden',
            inputs={
                'key': 'value'
            }
        )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            inputs={'key': 'value'},
            executor='central_deployment_agent'))

    def test_operation_mapping_overrides_none(self):
        yaml = self.BASIC_PLUGIN + TYPE_WITH_NONE_OP + create_operation_in_node_template(
            implementation='test_plugin.tasks.create',
            inputs={
                'key': 'value'
            }
        )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={'key': 'value'},
            executor='central_deployment_agent'))

    def test_operation_mapping_overrides_operation_mapping_with_executor(self):
        yaml = self.BASIC_PLUGIN + create_operation_in_node_type(
            implementation='mock.tasks.create',
            executor='host_agent'
        ) + create_operation_in_node_template(
            implementation='test_plugin.tasks.create-overridden',
            inputs={
                'key': 'value'
            },
            executor='central_deployment_agent'
        )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            inputs={'key': 'value'},
            executor='central_deployment_agent'))

    def test_operation_mapping_overrides_operation(self):
        yaml = self.BASIC_PLUGIN + create_operation_in_node_type(
            implementation='test_plugin.tasks.create',
            operation_mapping=False
        ) + create_operation_in_node_template(
            implementation='test_plugin.tasks.create-overridden',
            inputs={
                'key': 'value'
            }
        )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            inputs={'key': 'value'},
            executor='central_deployment_agent'))

    def test_none_overrides_no_op(self):
        yaml = create_operation_in_node_type() + TEMPLATE_WITH_NONE_OP
        self._assert_operations(yaml, NO_OP)

    def test_none_overrides_operation_mapping(self):
        yaml = self.BASIC_PLUGIN + create_operation_in_node_type(
            implementation='test_plugin.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        ) + TEMPLATE_WITH_NONE_OP

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={
                'key': 'value'
            },
            executor='central_deployment_agent'))

    def test_none_overrides_operation_mapping_no_inputs(self):
        yaml = self.BASIC_PLUGIN + create_operation_in_node_type(
            implementation='test_plugin.tasks.create',
        ) + TEMPLATE_WITH_NONE_OP

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            executor='central_deployment_agent'))

    def test_none_overrides_none(self):
        yaml = self.BASIC_PLUGIN + TYPE_WITH_NONE_OP + TEMPLATE_WITH_NONE_OP
        self._assert_operations(yaml, raw_operation_mapping())

    def test_none_overrides_operation_mapping_with_executor(self):
        yaml = self.BASIC_PLUGIN + create_operation_in_node_type(
            implementation='test_plugin.tasks.create',
            executor='central_deployment_agent'
        ) + TEMPLATE_WITH_NONE_OP

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            executor='central_deployment_agent'))

    def test_none_overrides_operation(self):
        yaml = self.BASIC_PLUGIN + create_operation_in_node_type(
            implementation='test_plugin.tasks.create',
            executor='central_deployment_agent',
            operation_mapping=False
        ) + TEMPLATE_WITH_NONE_OP

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            executor='central_deployment_agent'))

    def test_operation_mapping_with_executor_overrides_no_op(self):
        yaml = self.BASIC_PLUGIN + create_operation_in_node_type() + \
               create_operation_in_node_template(
                   implementation='test_plugin.tasks.create',
                   inputs={
                       'key': 'value'
                   },
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={'key': 'value'},
            executor='central_deployment_agent'))

    def test_operation_mapping_with_executor_overrides_operation_mapping(self):
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   inputs={
                       'key': {
                           'default': 'value'
                       }
                   }
               ) + \
               create_operation_in_node_template(
                   implementation='test_plugin.tasks.create-overridden',
                   inputs={
                       'key': 'value'
                   },
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            inputs={'key': 'value'},
            executor='central_deployment_agent'))

    def test_operation_mapping_with_executor_overrides_operation_mapping_no_inputs(self):  # NOQA
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
               ) + \
               create_operation_in_node_template(
                   implementation='test_plugin.tasks.create-overridden',
                   inputs={
                       'key': 'value'
                   },
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            inputs={'key': 'value'},
            executor='central_deployment_agent'))

    def test_operation_mapping_with_executor_overrides_none(self):
        yaml = self.BASIC_PLUGIN + TYPE_WITH_NONE_OP + \
               create_operation_in_node_template(
                   implementation='test_plugin.tasks.create',
                   inputs={
                       'key': 'value'
                   },
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={'key': 'value'},
            executor='central_deployment_agent'))

    def test_operation_mapping_with_executor_overrides_operation_mapping_with_executor(self):  # NOQA
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   executor='host_agent'
               ) + \
               create_operation_in_node_template(
                   implementation='test_plugin.tasks.create-overridden',
                   inputs={
                       'key': 'value'
                   },
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            inputs={'key': 'value'},
            executor='central_deployment_agent'))

    def test_operation_mapping_with_executor_overrides_operation(self):
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   operation_mapping=False
               ) + \
               create_operation_in_node_template(
                   implementation='test_plugin.tasks.create-overridden',
                   inputs={'key': 'value'},
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create-overridden',
            inputs={'key': 'value'},
            executor='central_deployment_agent'))

    def test_operation_mapping_no_implementation_overrides_no_op(self):
        yaml = create_operation_in_node_type() + \
               create_operation_in_node_template(
                   inputs={'key': 'value'},
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            executor='central_deployment_agent'))

    def test_operation_mapping_no_implementation_overrides_operation_mapping(self):  # NOQA
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   inputs={}
               ) + \
               create_operation_in_node_template(
                   inputs={'key': 'value'}
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={'key': 'value'},
            executor='central_deployment_agent'))

    def test_operation_mapping_no_implementation_overrides_operation_mapping_no_inputs(self):  # NOQA
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
               ) + \
               create_operation_in_node_template(
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={},
            executor='central_deployment_agent'))

    def test_operation_mapping_no_implementation_overrides_none(self):
        yaml = TYPE_WITH_NONE_OP + \
               create_operation_in_node_template(
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            inputs={},
            executor='central_deployment_agent'))

    def test_operation_mapping_no_implementation_overrides_operation_mapping_with_executor(self):  # NOQA
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   executor='host_agent'
               ) + \
               create_operation_in_node_template(
                   inputs={},
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={},
            executor='central_deployment_agent'))

    def test_operation_mapping_no_implementation_overrides_operation(self):
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   operation_mapping=False
               ) + \
               create_operation_in_node_template(
                   inputs={},
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={},
            executor='central_deployment_agent'))

    def test_operation_mapping_no_inputs_overrides_no_op(self):
        yaml = create_operation_in_node_type() + \
               create_operation_in_node_template(
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            executor='central_deployment_agent'))

    def test_operation_mapping_no_inputs_overrides_operation_mapping(self):  # NOQA
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   inputs={}
               ) + \
               create_operation_in_node_template(
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={},
            executor='central_deployment_agent'))

    def test_operation_mapping_no_inputs_overrides_operation_mapping_no_inputs(self):  # NOQA
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
               ) + \
               create_operation_in_node_template(
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={},
            executor='central_deployment_agent'))

    def test_operation_mapping_no_inputs_overrides_none(self):
        yaml = TYPE_WITH_NONE_OP + \
               create_operation_in_node_template(
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            executor='central_deployment_agent'))

    def test_operation_mapping_no_inputs_overrides_operation_mapping_with_executor(self):  # NOQA
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   executor='host_agent'
               ) + \
               create_operation_in_node_template(
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={},
            executor='central_deployment_agent'))

    def test_operation_mapping_no_inputs_overrides_operation(self):
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   operation_mapping=False
               ) + \
               create_operation_in_node_template(
                   executor='central_deployment_agent'
               )

        self._assert_operations(yaml, raw_operation_mapping(
            implementation='test_plugin.tasks.create',
            inputs={},
            executor='central_deployment_agent'))

    def test_operation_mapping_overrides_operation_mapping_with_retry(self):
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   max_retries=1,
                   retry_interval=2
               ) + \
               create_operation_in_node_template(
                   inputs={'some': 'input'}
               )

        self._assert_operations(
            yaml, raw_operation_mapping(
                implementation='test_plugin.tasks.create',
                inputs={'some': 'input'},
                executor='central_deployment_agent',
                max_retries=1,
                retry_interval=2),
            dsl_version=AbstractTestParser.BASIC_VERSION_SECTION_DSL_1_3)

    def test_operation_mapping_with_retry_overrides_operation_mapping_with_retry(self):  # noqa
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   max_retries=1,
                   retry_interval=2
               ) + \
               create_operation_in_node_template(
                   max_retries=3,
                   retry_interval=4
               )

        self._assert_operations(
            yaml, raw_operation_mapping(
                implementation='test_plugin.tasks.create',
                executor='central_deployment_agent',
                max_retries=3,
                retry_interval=4),
            dsl_version=AbstractTestParser.BASIC_VERSION_SECTION_DSL_1_3)

    def test_operation_mapping_with_retry_overrides_operation_mapping_with_retry_zero_values(self):  # noqa
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   max_retries=1,
                   retry_interval=2
               ) + \
               create_operation_in_node_template(
                   max_retries=0,
                   retry_interval=0
               )

        self._assert_operations(
            yaml, raw_operation_mapping(
                implementation='test_plugin.tasks.create',
                executor='central_deployment_agent',
                max_retries=0,
                retry_interval=0),
            dsl_version=AbstractTestParser.BASIC_VERSION_SECTION_DSL_1_3)

    def test_operation_mapping_with_impl_overrides_operation_mapping_with_retry(self):  # noqa
        yaml = self.BASIC_PLUGIN + \
               create_operation_in_node_type(
                   implementation='test_plugin.tasks.create',
                   max_retries=1,
                   retry_interval=2
               ) + \
               create_operation_in_node_template(
                   implementation='test_plugin.tasks.create-override',
                   inputs={'some': 'input'}
               )

        self._assert_operations(
            yaml, raw_operation_mapping(
                implementation='test_plugin.tasks.create-override',
                executor='central_deployment_agent',
                inputs={'some': 'input'}),
            dsl_version=AbstractTestParser.BASIC_VERSION_SECTION_DSL_1_3)


class NodeTypeNodeTypeOperationMergerTest(testtools.TestCase):

    def _assert_operations(self,
                           overriding_node_type_operation,
                           overridden_node_type_operation,
                           expected_merged_operation):

        if overriding_node_type_operation is not None:
            validate(overriding_node_type_operation,
                     operation.NodeTypeOperation)
        if overridden_node_type_operation is not None:
            validate(overridden_node_type_operation,
                     operation.NodeTypeOperation)

        merger = NodeTypeNodeTypeOperationMerger(
            overriding_operation=overriding_node_type_operation,
            overridden_operation=overridden_node_type_operation
        )

        actual_merged_operation = merger.merge()
        if expected_merged_operation is None:
            self.assertIsNone(actual_merged_operation)
        else:
            self.assertEqual(expected_merged_operation,
                             actual_merged_operation)

    def test_no_op_overrides_no_op(self):

        overriding_node_type_operation = {}
        overridden_node_type_operation = {}
        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_operation_mapping(self):

        overriding_node_type_operation = {}
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )
        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_operation_mapping_no_inputs(self):

        overriding_node_type_operation = {}
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )
        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_none(self):

        overriding_node_type_operation = {}
        overridden_node_type_operation = None
        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_operation_mapping_with_executor(self):

        overriding_node_type_operation = {}
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )
        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_no_op_overrides_operation(self):

        overriding_node_type_operation = {}
        overridden_node_type_operation = 'mock.tasks.create'

        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_no_op(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )
        overridden_node_type_operation = {}

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            }
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping_no_inputs(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            }
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_none(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )
        overridden_node_type_operation = None

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping_with_executor(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            }
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            }
        )
        overridden_node_type_operation = 'mock.tasks.create'

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={
                'key': {
                    'default': 'value-overridden'
                }
            },
            executor=None,
            max_retries=None,
            retry_interval=None)

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_no_op(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = {}

        expected_merged_operation = NO_OP

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_operation_mapping(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_operation_mapping_no_inputs(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_none(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = None

        expected_merged_operation = None

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_operation_mapping_with_executor(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_none_overrides_operation(self):

        overriding_node_type_operation = None
        overridden_node_type_operation = 'mock.tasks.create'

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )

        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_no_op(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )
        overridden_node_type_operation = {}

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation_mapping(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={
                'key': {
                    'default': 'value'
                }
            }
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation_mapping_no_inputs(self):  # NOQA

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_none(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = None

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation_mapping_with_executor(self):  # NOQA

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_no_inputs_overrides_operation(self):  # NOQA

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden'
        )
        overridden_node_type_operation = 'mock.tasks.create'

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_no_op(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )
        overridden_node_type_operation = {}

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_none(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )
        overridden_node_type_operation = None

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_operation_mapping(self):

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            executor='host_agent'
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_operation_mapping_no_inputs(self):  # NOQA

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            executor='host_agent'
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_operation_mapping_with_executor(self):  # NOQA

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            executor='central_deployment_agent'
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='central_deployment_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_executor_overrides_operation(self):  # NOQA

        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            executor='host_agent'
        )
        overridden_node_type_operation = 'mock.tasks.create'

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor='host_agent',
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_no_op(self):

        overriding_node_type_operation = 'mock.tasks.create'
        overridden_node_type_operation = {}

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_none(self):

        overriding_node_type_operation = 'mock.tasks.create'
        overridden_node_type_operation = None

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation_mapping(self):

        overriding_node_type_operation = 'mock.tasks.create-overridden'
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            inputs={}
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation_mapping_no_inputs(self):  # NOQA

        overriding_node_type_operation = 'mock.tasks.create-overridden'
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create'
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation_mapping_with_executor(self):  # NOQA

        overriding_node_type_operation = 'mock.tasks.create-overridden'
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            executor='host_agent'
        )

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_overrides_operation(self):  # NOQA

        overriding_node_type_operation = 'mock.tasks.create-overridden'
        overridden_node_type_operation = 'mock.tasks.create'

        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-overridden',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_overrides_operation_mapping_with_retry(self):
        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-override',
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            max_retries=1,
            retry_interval=2
        )
        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-override',
            inputs={},
            executor=None,
            max_retries=None,
            retry_interval=None
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )

    def test_operation_mapping_with_retry_overrides_operation_mapping_with_retry(self):  # noqa
        overriding_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create-override',
            max_retries=3,
            retry_interval=4
        )
        overridden_node_type_operation = raw_operation_mapping(
            implementation='mock.tasks.create',
            max_retries=1,
            retry_interval=2
        )
        expected_merged_operation = raw_operation_mapping(
            implementation='mock.tasks.create-override',
            inputs={},
            executor=None,
            max_retries=3,
            retry_interval=4
        )
        self._assert_operations(
            overriding_node_type_operation=overriding_node_type_operation,
            overridden_node_type_operation=overridden_node_type_operation,
            expected_merged_operation=expected_merged_operation
        )
