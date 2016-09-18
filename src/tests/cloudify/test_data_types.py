from .suite import ParserTestCase, TempDirectoryTestCase

from dsl_parser.exceptions import (
    DSLParsingLogicException,
    DSLParsingException,
    ERROR_UNKNOWN_TYPE,
    ERROR_CODE_CYCLE,
    ERROR_VALUE_DOES_NOT_MATCH_TYPE,
    ERROR_INVALID_TYPE_NAME,
)

class TestDataTypes(ParserTestCase, TempDirectoryTestCase):
    def test_unknown_type(self):
        self.template.version_section('cloudify_dsl', '1.2')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template.data_types_section(
            properties_first='\n        type: unknown-type')
        # TODO check that we get a corresponding validation issue for
        # a data_type property type of an invalid value
        self.assert_parser_raise_exception(
            error_code=ERROR_UNKNOWN_TYPE,
            exception_types=DSLParsingLogicException)

    def test_simple(self):
        self.template.version_section('cloudify_dsl', '1.2')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template.data_types_section()
        self.parse()

    def test_definitions(self):
        extras = (
            '  pair_of_pairs_type:\n'
            '    properties:\n'
            '      first:\n'
            '        type: pair_type\n'
            '      second:\n'
            '        type: pair_type\n'
        )
        self.template.version_section('cloudify_dsl', '1.2')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template.data_types_section(extras=extras)
        self.parse()

    def test_infinite_list(self):
        self.template.version_section('cloudify_dsl', '1.2')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += (
            '\n'
            'data_types:\n'
            '  list_type:\n'
            '    properties:\n'
            '      head:\n'
            '        type: integer\n'
            '      tail:\n'
            '        type: list_type\n'
            '        default:\n'
            '          head: 1\n'
        )
        # TODO check for validation issue that indicates cyclic definition
        # of a data type
        self.assert_parser_raise_exception(
            error_code=ERROR_CODE_CYCLE,
            exception_types=DSLParsingLogicException)

    def test_definitions_with_default_error(self):
        extras = (
            '  pair_of_pairs_type:\n'
            '    properties:\n'
            '      first:\n'
            '        type: pair_type\n'
            '        default:\n'
            '          first: 1\n'
            '          second: 2\n'
            '          third: 4\n'
            '      second:\n'
            '        type: pair_type\n'
        )
        self.template.version_section('cloudify_dsl', '1.2')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template.data_types_section(extras=extras)
        # TODO check for a validation issue that indicates that we are trying
        # to add a default value for a property that does not exist.
        self.assert_parser_raise_exception(
            error_code=106,
            exception_types=DSLParsingLogicException)

    def test_unknown_type_in_datatype(self):
        self.template.version_section('cloudify_dsl', '1.2')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
data_types:
  pair_type:
    properties:
      first:
        type: unknown-type
      second: {}
"""
        # TODO check that we get a corresponding validation issue for
        # a data_type property type of an invalid value
        self.assert_parser_raise_exception(
            ERROR_UNKNOWN_TYPE,
            DSLParsingLogicException)
