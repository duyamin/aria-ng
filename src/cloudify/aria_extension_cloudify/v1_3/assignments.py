
from aria.presentation import Presentation, AsIsPresentation, has_fields, allow_unknown_fields, short_form_field, primitive_field, object_dict_field, object_dict_unknown_fields
from aria import dsl_specification

class PropertyAssignment(AsIsPresentation):
    pass

@has_fields
class TriggerAssignment(Presentation):
    @primitive_field(str, required=True)
    def type(self):
        """
        Trigger type.
        
        :rtype: str
        """

    @object_dict_field(PropertyAssignment)
    def properties(self):
        """
        Optional parameters that will be passed to the trigger.
        
        :rtype: dict of str, :class:`PropertyAssignment`
        """

@has_fields
class PolicyAssignment(Presentation):
    @primitive_field(str, required=True)
    def type(self):
        """
        Policy type.
        
        :rtype: str
        """

    @object_dict_field(PropertyAssignment)
    def properties(self):
        """
        Optional properties for configuring the policy.
        
        :rtype: dict of str, :class:`PropertyAssignment`
        """

    @object_dict_field(TriggerAssignment)
    def triggers(self):
        """
        A dict of triggers.
        
        :rtype: dict of str, :class:`TriggerAssignment`
        """

@short_form_field('implementation')
@has_fields
class OperationAssignment(Presentation):
    @primitive_field(str)
    def implementation(self):
        """
        The script or plugin task name to execute.
        
        ARIA NOTE: The spec seems to mistakingly mark this as a required field.
        
        :rtype: str
        """

    @object_dict_field(PropertyAssignment)
    def inputs(self):
        """
        Schema of inputs that will be passed to the implementation as kwargs.
        
        :rtype: dict of str, :class:`PropertyAssignment`
        """

    @primitive_field(str)
    def executor(self):
        """
        Valid values: :code:`central_deployment_agent`, :code:`host_agent`.
        
        :rtype: str
        """

    @primitive_field(int)
    def max_retries(self):
        """
        Maximum number of retries for a task. -1 means infinite retries (Default: :code:`task_retries` in manager blueprint Cloudify Manager Type for remote workflows and :code:`task_retries` workflow configuration for local workflows).
        
        :rtype: int
        """

    @primitive_field(int)
    def retry_interval(self):
        """
        Minimum wait time (in seconds) in between task retries (Default: :code:`task_retry_interval` in manager blueprint Cloudify Manager Type for remote workflows and :code:`task_retry_interval` workflow configuration for local workflows).
        
        :rtype: int
        """

@allow_unknown_fields
@has_fields
@dsl_specification('interfaces-2', 'cloudify-1.3')
class InterfaceAssignment(Presentation):
    """
    Interfaces provide a way to map logical tasks to executable operations.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-interfaces/>`__.
    """

    @object_dict_unknown_fields(OperationAssignment)
    def operations(self):
        """
        :rtype: dict of str, :class:`OperationAssignment`
        """
