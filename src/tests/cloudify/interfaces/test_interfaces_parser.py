########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

# import testtools
# from dsl_parser.interfaces.constants import NO_OP
#
# from dsl_parser.interfaces.interfaces_parser import (
#     merge_node_type_interfaces,
#     merge_relationship_type_and_instance_interfaces,
#     merge_node_type_and_node_template_interfaces,
#     merge_relationship_type_interfaces)
# from dsl_parser.elements import operation
#
# from dsl_parser.tests.interfaces import validate
from ..framework.abstract_test_parser import AbstractTestParser
import yaml

# NO_OP = ''

class InterfacesParserTest(AbstractTestParser):

    # def _validate_type_interfaces(self, interfaces):
    #     validate(interfaces, operation.NodeTypeInterfaces)
    #
    # def _validate_instance_interfaces(self, interfaces):
    #     validate(interfaces, operation.NodeTemplateInterfaces)

    def _assert_merged_interfaces(self,
                                  node_type_interfaces,
                                  node_template_interfaces,
                                  expected_merged_interfaces):
        merged_interfaces = self._merge_interfaces(
            node_type_interfaces, node_template_interfaces
        )

        for operation_name, operation in expected_merged_interfaces.iteritems():

            expected_merged_interfaces[operation_name].update({
                'max_retries': None,
                'retry_interval': None,
                'has_intrinsic_functions': False,
                'plugin': operation.get('plugin') or None,
                'inputs': operation.get('inputs') or {},
                'executor': operation.get('executor') or None})

        self.assertEqual(expected_merged_interfaces, merged_interfaces)

    def _merge_interfaces(self,
                          node_type_interfaces=None,
                          derived_node_type_interfaces=None,
                          node_template_interfaces=None,
                          relationship_type_interfaces=None,
                          derived_relationship_type_interfaces=None,
                          relationship_template_interfaces=None):

        node_type_interfaces = node_type_interfaces or {}
        derived_node_type_interfaces = derived_node_type_interfaces or {}
        node_template_interfaces = node_template_interfaces or {}
        relationship_type_interfaces = relationship_type_interfaces or {}
        derived_relationship_type_interfaces = derived_relationship_type_interfaces or {}
        relationship_template_interfaces = relationship_template_interfaces or {}

        blueprint_dict = {
            'tosca_definitions_version': 'cloudify_dsl_1_3',
            'node_types': {
                'node_type': {
                    'interfaces': node_type_interfaces
                },
                'derived_node_type': {
                    'derived_from': 'node_type',
                    'interfaces': derived_node_type_interfaces
                }
            },
            'node_templates': {
                'node1': {
                    'type': 'node_type',
                    'interfaces': node_template_interfaces,
                    'relationships': [{
                         'type': 'relationship_type',
                          'target': 'node2',
                          'source_interfaces': relationship_template_interfaces
                    }]},
                'node2': {  # only here to be the target of node1's relationship
                    'type': 'node_type'
                }
            },
            'relationships': {
                'relationship_type': {
                    'source_interfaces': relationship_type_interfaces
                },
                'derived_relationship_type': {
                    'source_interfaces': derived_relationship_type_interfaces
                },

            },
            'plugins': {
                'mock': {
                    'source': 'path',
                    'executor': 'central_deployment_agent'
                }
            }
        }
        blueprint_yaml = yaml.dump(blueprint_dict)
        parsed = self.parse(blueprint_yaml)
        if node_type_interfaces:
            if node_type_interfaces:
                if derived_node_type_interfaces:
                    return
        operations = parsed['nodes'][0]['operations']
        return {op: operations[op] for op in operations if '.' in op}

    def test_merge_node_type_interfaces(self):

        node_type_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }}
        node_template_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }}}}}

        expected_merged_interfaces = {
            'interface1.start': {
                'plugin': 'mock',
                'operation': 'tasks.start',
                'executor': 'central_deployment_agent',
            },
            'interface1.stop': {
                'plugin': 'mock',
                'operation': 'tasks.stop',
                'inputs': {
                    'key': {
                        'default': 'value'
                    }
                },
                'executor': 'central_deployment_agent',
            },

            'interface2.start': {
                'operation': None,
            }
        }

        self._assert_merged_interfaces(node_type_interfaces,
                                       node_template_interfaces,
                                       expected_merged_interfaces)

    def test_merge_node_type_interfaces_no_interfaces_on_overriding(self):

        node_template_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }
        node_type_interfaces = {}

        expected_merged_interfaces = {
            'interface1.start': {
                'operation': None,
            },
            'interface1.stop': {
                'operation': None,
            },
            'interface2.start': {
                'operation': None
            }
        }

        self._assert_merged_interfaces(node_type_interfaces,
                                       node_template_interfaces,
                                       expected_merged_interfaces)

    def test_merge_node_type_interfaces_no_interfaces_on_overridden(self):

        node_type_interfaces = {}

        node_template_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }

        expected_merged_interfaces = {

            'interface1.start': {
                'operation': None
            },
            'interface1.stop': {
                'operation': None
            },
            'interface2.start': {
                'operation': None
            }
        }

        self._assert_merged_interfaces(node_type_interfaces,
                                       node_template_interfaces,
                                       expected_merged_interfaces)

    def test_merge_node_type_and_node_template_interfaces(self):

        node_template_interfaces = {
            'interface1': {
                'start': 'mock.tasks.start-overridden'
            }
        }

        node_type_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }}}}}

        expected_merged_interfaces = {
            'interface1.start': {
                'operation': 'tasks.start-overridden',
                'plugin': 'mock',
                'executor': 'central_deployment_agent'
            },
            'interface1.stop': {
                'operation': 'tasks.stop',
                'plugin': 'mock',
                'executor': 'central_deployment_agent',
                'inputs': {
                    'key': 'value'
                }}}

        self._assert_merged_interfaces(node_type_interfaces,
                                       node_template_interfaces,
                                       expected_merged_interfaces)

    def test_merge_node_type_no_interfaces_and_node_template_interfaces(self):

        node_type_interfaces = {}
        node_template_interfaces = {
            'interface1': {
                'start': 'mock.tasks.start'
            }
        }

        expected_merged_interfaces = {
            'interface1.start': {
                'operation': 'tasks.start',
                'plugin': 'mock',
                'executor': 'central_deployment_agent'
            }
        }

        self._assert_merged_interfaces(node_type_interfaces,
                                       node_template_interfaces,
                                       expected_merged_interfaces)

    def test_merge_node_type_interfaces_and_node_template_no_interfaces(self):

        node_type_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                }
            }
        }
        node_template_interfaces = {}

        expected_merged_interfaces = {
            'interface1.start': {
                'operation': 'tasks.start',
                'plugin': 'mock',
                'executor': 'central_deployment_agent'
            }
        }

        self._assert_merged_interfaces(node_type_interfaces,
                                       node_template_interfaces,
                                       expected_merged_interfaces)

    def test_merge_relationship_type_interfaces(self):

        node_type_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }

        node_template_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }}}}}

        expected_merged_interfaces = {

                'interface1.start': {
                    'operation': 'tasks.start',
                    'executor': 'central_deployment_agent',
                    'plugin': 'mock'
                },
                'interface1.stop': {
                    'operation': 'tasks.stop',
                    'executor': 'central_deployment_agent',
                    'plugin': 'mock',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }}
                },
                'interface2.start': {
                    'operation': None
                }
            }

        self._assert_merged_interfaces(node_type_interfaces,
                                       node_template_interfaces,
                                       expected_merged_interfaces)

    def test_merge_relationship_type_interfaces_no_interfaces_on_overriding(self):

        node_type_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }
        node_template_interfaces = {}

        expected_merged_interfaces = {
            'interface1.start': {
                'operation': None,
            },
            'interface1.stop': {
                'operation': None
            },
            'interface2.start': {
                'operation': None
            }
        }

        self._assert_merged_interfaces(node_type_interfaces,
                                       node_template_interfaces,
                                       expected_merged_interfaces)

    def test_merge_relationship_type_interfaces_no_interfaces_on_overridden(self):  # NOQA

        node_template_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }
        node_type_interfaces = {}

        expected_merged_interfaces = {
            'interface1': {
                'start': NO_OP,
                'stop': NO_OP
            },
            'interface2': {
                'start': NO_OP
            }
        }

        self._validate_type_interfaces(node_template_interfaces)
        self._validate_type_interfaces(node_type_interfaces)
        actual_merged_interfaces = merge_relationship_type_interfaces(
            node_template_interfaces=node_template_interfaces,
            node_type_interfaces=node_type_interfaces)

        self.assertEqual(actual_merged_interfaces,
                         expected_merged_interfaces)

    # def test_merge_relationship_type_and_instance_interfaces(self):
    #
    #     relationship_type_interfaces = {
    #         'interface1': {
    #             'start': {
    #                 'implementation': 'mock.tasks.start'
    #             },
    #             'stop': {
    #                 'implementation': 'mock.tasks.stop',
    #                 'inputs': {
    #                     'key': {
    #                         'default': 'value'
    #                     }
    #                 }
    #             }
    #         }
    #     }
    #
    #     relationship_instance_interfaces = {
    #         'interface1': {
    #             'start': 'mock.tasks.start-overridden'
    #         }
    #     }
    #
    #     expected_merged_interfaces = {
    #         'interface1': {
    #             'start': {
    #                 'implementation': 'mock.tasks.start-overridden',
    #                 'inputs': {},
    #                 'executor': None,
    #                 'max_retries': None,
    #                 'retry_interval': None
    #             },
    #             'stop': {
    #                 'implementation': 'mock.tasks.stop',
    #                 'inputs': {
    #                     'key': 'value'
    #                 },
    #                 'executor': None,
    #                 'max_retries': None,
    #                 'retry_interval': None
    #             }
    #         }
    #     }
    #
    #     self._validate_type_interfaces(relationship_type_interfaces)
    #     self._validate_instance_interfaces(relationship_instance_interfaces)
    #     actual_merged_interfaces = \
    #         merge_relationship_type_and_instance_interfaces(
    #             relationship_type_interfaces=relationship_type_interfaces,
    #             relationship_instance_interfaces=relationship_instance_interfaces)  # noqa
    #
    #     self.assertEqual(actual_merged_interfaces,
    #                      expected_merged_interfaces)
    #
    # def test_merge_relationship_type_no_interfaces_and_instance_interfaces(self):  # NOQA
    #
    #     relationship_type_interfaces = {}
    #     relationship_instance_interfaces = {
    #         'interface1': {
    #             'start': 'mock.tasks.start-overridden'
    #         }
    #     }
    #
    #     expected_merged_interfaces = {
    #         'interface1': {
    #             'start': {
    #                 'implementation': 'mock.tasks.start-overridden',
    #                 'inputs': {},
    #                 'executor': None,
    #                 'max_retries': None,
    #                 'retry_interval': None
    #             }
    #         }
    #     }
    #
    #     self._validate_type_interfaces(relationship_type_interfaces)
    #     self._validate_instance_interfaces(relationship_instance_interfaces)
    #     actual_merged_interfaces = \
    #         merge_relationship_type_and_instance_interfaces(
    #             relationship_type_interfaces=relationship_type_interfaces,
    #             relationship_instance_interfaces=relationship_instance_interfaces)  # noqa
    #
    #     self.assertEqual(actual_merged_interfaces,
    #                      expected_merged_interfaces)
    #
    # def test_merge_relationship_type_and_instance_no_interfaces(self):
    #
    #     relationship_type_interfaces = {
    #         'interface1': {
    #             'start': {
    #                 'implementation': 'mock.tasks.start'
    #             },
    #             'stop': {
    #                 'implementation': 'mock.tasks.stop',
    #                 'inputs': {
    #                     'key': {
    #                         'default': 'value'
    #                     }
    #                 }
    #             }
    #         }
    #     }
    #
    #     relationship_instance_interfaces = {}
    #
    #     expected_merged_interfaces = {
    #         'interface1': {
    #             'start': {
    #                 'implementation': 'mock.tasks.start',
    #                 'inputs': {},
    #                 'executor': None,
    #                 'max_retries': None,
    #                 'retry_interval': None
    #             },
    #             'stop': {
    #                 'implementation': 'mock.tasks.stop',
    #                 'inputs': {
    #                     'key': 'value'
    #                 },
    #                 'executor': None,
    #                 'max_retries': None,
    #                 'retry_interval': None
    #             }
    #         }
    #     }
    #
    #     self._validate_type_interfaces(relationship_type_interfaces)
    #     self._validate_instance_interfaces(relationship_instance_interfaces)
    #     actual_merged_interfaces = \
    #         merge_relationship_type_and_instance_interfaces(
    #             relationship_type_interfaces=relationship_type_interfaces,
    #             relationship_instance_interfaces=relationship_instance_interfaces)  # noqa
    #
    #     self.assertEqual(actual_merged_interfaces,
    #                      expected_merged_interfaces)
