
from .utils.data_types import get_primitive_data_type, get_data_type_name, coerce_value
from aria import Issue
from aria.presentation import report_issue_for_unknown_type, derived_from_validator
import re

#
# PropertyDefinition, AttributeDefinition, ParameterDefinition, EntrySchema
#

def data_type_validator(type_name='data type'):
    """
    Makes sure that the field refers to a valid data type, whether complex or primitive. 
    
    Used with the :func:`field_validator` decorator for "type" fields in :class:`PropertyDefinition`, :class:`AttributeDefinition`, :class:`ParameterDefinition`, and :class:`EntrySchema`.
    
    Extra behavior beyond validation: generated function returns true if field is a complex data type.
    """

    def validator(field, presentation, context):
        field._validate(presentation, context)
    
        value = getattr(presentation, field.name)
        if value is not None:
            # Can be a complex data type
            if (context.presentation.data_types is not None) and (value in context.presentation.data_types):
                return True
            # Can be a primitive data type
            if get_primitive_data_type(value) is None:
                report_issue_for_unknown_type(context, presentation, type_name, field.name, value)
    
        return False

    return validator

#
# PropertyDefinition, AttributeDefinition
#

def entry_schema_validator(field, presentation, context):
    """
    According to whether the data type supports "entry\_schema" (e.g., it is or inherits from list or map),
    make sure that we either have or don't have a valid data type value.
    
    Used with the :func:`field_validator` decorator for the "entry\_schema" field in :class:`PropertyDefinition` and :class:`AttributeDefinition`.
    """

    field._validate(presentation, context)

    def type_uses_entry_schema(the_type):
        use_entry_schema = the_type._get_extension('use_entry_schema', False) if hasattr(the_type, '_get_extension') else False
        if use_entry_schema:
            return True
        parent = the_type._get_parent(context) if hasattr(the_type, '_get_parent') else None
        if parent is None:
            return False
        return type_uses_entry_schema(parent)

    value = getattr(presentation, field.name)
    the_type = presentation._get_type(context)
    if the_type is None:
        return
    use_entry_schema = type_uses_entry_schema(the_type)
    
    if use_entry_schema:
        if value is None:
            context.validation.report('"entry_schema" does not have a value as required by data type "%s" in "%s"' % (get_data_type_name(the_type), presentation._container._fullname), locator=presentation._locator, level=Issue.BETWEEN_TYPES)
    else:
        if value is not None:
            context.validation.report('"entry_schema" has a value but it is not used by data type "%s" in "%s"' % (get_data_type_name(the_type), presentation._container._fullname), locator=presentation._locator, level=Issue.BETWEEN_TYPES)

def data_value_validator(field, presentation, context):
    """
    Makes sure that the field contains a valid value according to data type and constraints.
    
    Used with the :func:`field_validator` decorator for the "default" field in :class:`PropertyDefinition` and :class:`AttributeDefinition`.
    """

    field._validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        the_type = presentation._get_type(context)
        entry_schema = presentation.entry_schema
        constraints = presentation._get_constraints(context) if hasattr(presentation, '_get_constraints') else None # AttributeDefinition does not have this
        coerce_value(context, presentation, the_type, entry_schema, constraints, value, field.name)

#
# DataType
#

_data_type_validator = data_type_validator()
_data_type_derived_from_validator = derived_from_validator('data_types')

def data_type_derived_from_validator(field, presentation, context):
    """
    Makes sure that the field refers to a valid parent data type (complex or primitive).
    
    Used with the :func:`field_validator` decorator for the "derived\_from" field in :class:`DataType`.
    """
    
    if _data_type_validator(field, presentation, context):
        # Validate derivation only if a complex data type (primitive types have no derivation hierarchy)
        _data_type_derived_from_validator(field, presentation, context)

def data_type_constraints_validator(field, presentation, context):
    """
    Makes sure that we do not have constraints if we are a complex type (with no primitive ancestor).
    """

    field._validate(presentation, context)
    
    value = getattr(presentation, field.name)
    if value is not None:
        if presentation._get_primitive_ancestor(context) is None:
            context.validation.report('data type "%s" defines constraints but does not have a primitive ancestor' % presentation._fullname, locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_TYPES)

def data_type_properties_validator(field, presentation, context):
    """
    Makes sure that we do not have properties if we have a primitive ancestor.
    
    Used with the :func:`field_validator` decorator for the "properties" field in :class:`DataType`.
    """

    field._validate(presentation, context)
    
    values = getattr(presentation, field.name)
    if values is not None:
        if presentation._get_primitive_ancestor(context) is not None:
            context.validation.report('data type "%s" defines properties even though it has a primitive ancestor' % presentation._fullname, locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_TYPES)

#
# ConstraintClause
#

def constraint_clause_field_validator(field, presentation, context):
    """
    Makes sure that field contains a valid value for the container type.
    
    Used with the :func:`field_validator` decorator for various field in :class:`ConstraintClause`.
    """

    field._validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        the_type = presentation._get_type(context)
        constraints = the_type._get_constraints(context) if hasattr(the_type, '_get_constraints') else None
        coerce_value(context, presentation, the_type, None, constraints, value, field.name)

def constraint_clause_in_range_validator(field, presentation, context):
    """
    Makes sure that the value is a list with exactly two elements, that both lower bound contains a valid
    value for the container type, and that the upper bound is either "UNBOUNDED" or a valid value for the
    container type.
    
    Used with the :func:`field_validator` decorator for the "in\_range" field in :class:`ConstraintClause`.
    """

    field._validate(presentation, context)

    values = getattr(presentation, field.name)
    if isinstance(values, list):
        # Make sure list has exactly two elements
        if len(values) == 2:
            lower, upper = values
            the_type = presentation._get_type(context)
            
            # Lower bound must be coercible
            lower = coerce_value(context, presentation, the_type, None, None, lower, field.name)
            
            if upper != 'UNBOUNDED':
                # Upper bound be coercible
                upper = coerce_value(context, presentation, the_type, None, None, upper, field.name)
                
                # Second "in_range" value must be greater than first
                if (lower is not None) and (upper is not None) and (lower >= upper):
                    context.validation.report('upper bound of "in_range" constraint is not greater than the lower bound in "%s": %s <= %s' % (presentation._container._fullname, repr(lower), repr(upper)), locator=presentation._locator, level=Issue.FIELD)
        else:
            context.validation.report('constraint "%s" is not a list of exactly 2 elements in "%s"' % (field.name, presentation._fullname), locator=presentation._get_child_locator(field.name), level=Issue.FIELD)

def constraint_clause_valid_values_validator(field, presentation, context):
    """
    Makes sure that the value is a list of valid values for the container type.
    
    Used with the :func:`field_validator` decorator for the "valid\_values" field in :class:`ConstraintClause`.
    """
    
    field._validate(presentation, context)
    
    values = getattr(presentation, field.name)
    if isinstance(values, list):
        the_type = presentation._get_type(context)
        for value in values:
            coerce_value(context, presentation, the_type, None, None, value, field.name)

def constraint_clause_pattern_validator(field, presentation, context):
    """
    Makes sure that the value is a valid regular expression.
    
    Used with the :func:`field_validator` decorator for the "pattern" field in :class:`ConstraintClause`.
    """

    field._validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        try:
            # Note: the TOSCA 1.0 spec does not specify the regular expression grammar, so we will just use Python's
            re.compile(value)
        except re.error as e:
            context.validation.report('constraint "%s" is not a valid regular expression in "%s"' % (field.name, presentation._fullname), locator=presentation._get_child_locator(field.name), level=Issue.FIELD, exception=e)

#
# RequirementAssignment
#

def node_template_or_type_validator(field, presentation, context):
    """
    Makes sure that the field refers to either a node template or a node type.
    
    Used with the :func:`field_validator` decorator for the "node" field in :class:`RequirementAssignment`.
    """
    
    field._validate(presentation, context)
    
    value = getattr(presentation, field.name)
    if value is not None:
        node_templates = context.presentation.node_templates or {}
        node_types = context.presentation.node_types or {}
        if (value not in node_templates) and (value not in node_types):
            report_issue_for_unknown_type(context, presentation, 'node template or node type', field.name, value)

def capability_definition_or_type_validator(field, presentation, context):
    """
    Makes sure refers to either a capability assignment name in the node template referred to by the "node" field
    or a general capability type.
    
    If the value refers to a capability type, make sure the "node" field was not assigned.  
    
    Used with the :func:`field_validator` decorator for the "capability" field in :class:`RequirementAssignment`.
    """
    
    field._validate(presentation, context)
    
    value = getattr(presentation, field.name)
    if value is not None:
        node, node_variant = presentation._get_node(context)
        if node_variant == 'node_template':
            capabilities = node._get_capabilities(context)
            if value in capabilities:
                return

        capability_types = context.presentation.capability_types
        if (capability_types is not None) and (value in capability_types):
            if node is not None:
                context.validation.report('"%s" refers to a capability type even though "node" has a value in "%s"' % (presentation._name, presentation._container._fullname), locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_FIELDS)
            return
        
        if node_variant == 'node_template':
            context.validation.report('requirement "%s" refers to an unknown capability definition name or capability type in "%s": %s' % (presentation._name, presentation._container._fullname, repr(value)), locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_TYPES)
        else:
            context.validation.report('requirement "%s" refers to an unknown capability type in "%s": %s' % (presentation._name, presentation._container._fullname, repr(value)), locator=presentation._get_child_locator(field.name), level=Issue.BETWEEN_TYPES)

def node_filter_validator(field, presentation, context):
    """
    Makes sure that the field has a value only if "node" refers to a node type.

    Used with the :func:`field_validator` decorator for the "node\_filter" field in :class:`RequirementAssignment`.
    """

    field._validate(presentation, context)
    
    value = getattr(presentation, field.name)
    if value is not None:
        _, node_type_variant = presentation._get_node(context)
        if node_type_variant != 'node_type':
            context.validation.report('requirement "%s" has a node filter even though "node" does not refer to a node type in "%s"' % (presentation._fullname, presentation._container._fullname), locator=presentation._locator, level=Issue.BETWEEN_FIELDS)

#
# RelationshipAssignment
#

def relationship_template_or_type_validator(field, presentation, context):
    """
    Makes sure that the field refers to either a relationship template or a relationship type.
    
    Used with the :func:`field_validator` decorator for the "type" field in :class:`RelationshipAssignment`.
    """
    
    field._validate(presentation, context)
    
    value = getattr(presentation, field.name)
    if value is not None:
        relationship_templates = context.presentation.relationship_templates or {}
        relationship_types = context.presentation.relationship_types or {}
        if (value not in relationship_templates) and (value not in relationship_types):
            report_issue_for_unknown_type(context, presentation, 'relationship template or relationship type', field.name, value)

#
# PolicyType
#

def list_node_type_or_group_type_validator(field, presentation, context):
    """
    Makes sure that the field's elements refer to either node types or a group types.

    Used with the :func:`field_validator` decorator for the "targets" field in :class:`PolicyType`.
    """
    
    field._validate(presentation, context)
    
    values = getattr(presentation, field.name)
    if values is not None:
        for value in values:
            node_types = context.presentation.node_types or {}
            group_types = context.presentation.group_types or {}
            if (value not in node_types) and (value not in group_types):
                report_issue_for_unknown_type(context, presentation, 'node type or group type', field.name, value)

#
# PolicyDefinition
#

def policy_targets_validator(field, presentation, context):
    """
    Makes sure that the field's elements refer to either node templates or groups, and that
    they match the node types and group types declared in the policy type.

    Used with the :func:`field_validator` decorator for the "targets" field in :class:`PolicyDefinition`.
    """
    
    field._validate(presentation, context)
    
    values = getattr(presentation, field.name)
    if values is not None:
        for value in values:
            node_templates = context.presentation.node_templates or {}
            groups = context.presentation.groups or {}
            if (value not in node_templates) and (value not in groups):
                report_issue_for_unknown_type(context, presentation, 'node template or group', field.name, value)
            
            policy_type = presentation._get_type(context)    
            if policy_type is not None:
                node_types, group_types = policy_type._get_targets(context)

                ok = False
                
                if value in node_templates:
                    our_node_type = node_templates[value]._get_type(context)
                    for node_type in node_types:
                        if node_type._is_descendant(context, our_node_type):
                            ok = True
                            break

                elif value in groups:
                    our_group_type = groups[value]._get_type(context)
                    for group_type in group_types:
                        if group_type._is_descendant(context, our_group_type):
                            ok = True
                            break

                if not ok:
                    context.validation.report('policy definition target does not match either a node type or a group type declared in the policy type in "%s": %s' % (presentation._name, repr(value)), locator=presentation._locator, level=Issue.BETWEEN_TYPES)

#
# NodeFilter
#

def node_filter_properties_validator(field, presentation, context):
    """
    Makes sure that the field's elements refer to defined properties in the target node type.
    
    Used with the :func:`field_validator` decorator for the "properties" field in :class:`NodeFilter`.
    """
    
    field._validate(presentation, context)
    
    values = getattr(presentation, field.name)
    if values is not None:
        node_type = presentation._get_node_type(context)
        if node_type is not None:
            properties = node_type._get_properties(context)
            for name, _ in values:
                if name not in properties:
                    context.validation.report('node filter refers to an unknown property definition in "%s": %s' % (node_type._name, name), locator=presentation._locator, level=Issue.BETWEEN_TYPES)

def node_filter_capabilities_validator(field, presentation, context):
    """
    Makes sure that the field's elements refer to defined capabilities and properties in the target node type.
    
    Used with the :func:`field_validator` decorator for the "capabilities" field in :class:`NodeFilter`.
    """

    field._validate(presentation, context)
    
    values = getattr(presentation, field.name)
    if values is not None:
        node_type = presentation._get_node_type(context)
        if node_type is not None:
            capabilities = node_type._get_capabilities(context)
            for name, value in values:
                capability = capabilities.get(name)
                if capability is not None:
                    properties = value.properties
                    capability_properties = capability.properties
                    if (properties is not None) and (capability_properties is not None):
                        for property_name, _ in properties:
                            if property_name not in capability_properties:
                                context.validation.report('node filter refers to an unknown capability definition property in "%s": %s' % (node_type._name, property_name), locator=presentation._locator, level=Issue.BETWEEN_TYPES)
                else:
                    context.validation.report('node filter refers to an unknown capability definition in "%s": %s' % (node_type._name, name), locator=presentation._locator, level=Issue.BETWEEN_TYPES)
