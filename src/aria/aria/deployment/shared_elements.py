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

from .utils import validate_dict_values, instantiate_dict, coerce_value, coerce_dict_values, dump_dict_values, dump_properties
from .. import UnimplementedFunctionalityError
from ..validation import Issue
from ..utils import StrictList, StrictDict, as_agnostic, classname, deepcopy_with_locators, puts
from collections import OrderedDict

class Function(object):
    """
    An intrinsic function.
    
    Serves as a placeholder for a value that should eventually be derived
    by calling the function.
    """
    
    @property
    def as_raw(self):
        raise UnimplementedFunctionalityError(classname(self) + '.as_raw')

    def _evaluate(self, context, container):
        raise UnimplementedFunctionalityError(classname(self) + '._evaluate')

    def __deepcopy__(self, memo):
        # Circumvent cloning in order to maintain our state
        return self

class Element(object):
    """
    Base class for :class:`DeploymentPlan` elements.
    
    All elements support validation, diagnostic dumping, and representation as
    raw data (which can be translated into JSON or YAML) via :code:`as_raw`.
    """
    
    @property
    def as_raw(self):
        raise UnimplementedFunctionalityError(classname(self) + '.as_raw')

    def validate(self, context):
        pass

    def coerce_values(self, context, container, report_issues):
        pass
    
    def dump(self, context):
        pass

class TemplateElement(Element):
    """
    Base class for :class:`DeploymentTemplate` elements.
    
    All template elements can be instantiated into :class:`DeploymentPlan` elements. 
    """

    def instantiate(self, context, container):
        pass

class Parameter(TemplateElement):
    """
    Represents a typed value.

    Used by both :class:`DeploymentTemplate` and :class:`DeploymentPlan` elements.
    """
    
    def __init__(self, type_name, value, description):
        self.type_name = type_name
        self.value = value
        self.description = description

    @property
    def as_raw(self):
        return OrderedDict((
            ('type_name', self.type_name),
            ('value', self.value),
            ('description', self.description)))

    def instantiate(self, context, container):
        return Parameter(self.type_name, self.value, self.description)

    def coerce_values(self, context, container, report_issues):
        if self.value is not None:
            self.value = coerce_value(context, container, self.value, report_issues)

class Metadata(TemplateElement):
    """
    Custom values associated with the deployment template and its plans.

    Properties:
    
    * :code:`values`: Dict of custom values
    """
    
    def __init__(self):
        self.values = StrictDict(key_class=basestring)

    @property
    def as_raw(self):
        return deepcopy_with_locators(self.values)

    def instantiate(self, context, container):
        r = Metadata()
        r.values.update(self.values)
        return r

    def dump(self, context):
        puts('Metadata:')
        with context.style.indent:
            for name, value in self.values.iteritems():
                puts('%s: %s' % (name, context.style.meta(value)))

class Interface(TemplateElement):
    """
    A typed set of operations.
    
    This class is used by both deployment template and deployment plan elements.
    
    Properties:
    
    * :code:`name`: Name
    * :code:`type_name`: Must be represented in the :class:`DeploymentContext`
    * :code:`inputs`: Dict of :class:`Parameter`
    * :code:`operations`: Dict of :class:`Operation`
    """
    
    def __init__(self, name, type_name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        
        self.name = name
        self.type_name = type_name
        self.inputs = StrictDict(key_class=basestring, value_class=Parameter)
        self.operations = StrictDict(key_class=basestring, value_class=Operation)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('inputs', {k: v.as_raw for k, v in self.inputs.iteritems()}),
            ('operations', [v.as_raw for v in self.operations.itervalues()])))

    def instantiate(self, context, container):
        r = Interface(self.name, self.type_name)
        instantiate_dict(context, container, r.inputs, self.inputs)
        instantiate_dict(context, container, r.operations, self.operations)
        return r

    def validate(self, context):
        if self.type_name:
            if context.deployment.interface_types.get_descendant(self.type_name) is None:
                context.validation.report('interface "%s" has an unknown type: %s' % (self.name, repr(self.type_name)), level=Issue.BETWEEN_TYPES)        

        validate_dict_values(context, self.inputs)
        validate_dict_values(context, self.operations)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.inputs, report_issues)
        coerce_dict_values(context, container, self.operations, report_issues)
    
    def dump(self, context):
        puts(context.style.node(self.name))
        with context.style.indent:
            puts('Interface type: %s' % context.style.type(self.type_name))
            dump_properties(context, self.inputs, 'Inputs')
            dump_dict_values(context, self.operations, 'Operations')

class Operation(TemplateElement):
    """
    A typed set of operations.
    
    This class is used by both deployment template and deployment plan elements.
    
    Properties:
    
    * :code:`name`: Name
    * :code:`implementation`: Implementation string (interpreted by the orchestrator)
    * :code:`dependencies`: List of strings (interpreted by the orchestrator)
    * :code:`executor`: Executor string (interpreted by the orchestrator)
    * :code:`max_retries`: Maximum number of retries allowed in case of failure
    * :code:`retry_interval`: Interval between retries
    * :code:`inputs`: Dict of :class:`Parameter`
    """
    
    def __init__(self, name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        
        self.name = name
        self.implementation = None
        self.dependencies = StrictList(value_class=basestring)
        self.executor = None # Cloudify
        self.max_retries = None # Cloudify
        self.retry_interval = None # Cloudify
        self.inputs = StrictDict(key_class=basestring, value_class=Parameter)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('implementation', self.implementation),
            ('dependencies', self.dependencies),
            ('executor', self.executor),
            ('max_retries', self.max_retries),
            ('retry_interval', self.retry_interval),
            ('inputs', {k: v.as_raw for k, v in self.inputs.iteritems()})))

    def instantiate(self, context, container):
        r = Operation(self.name)
        r.implementation = self.implementation
        r.dependencies = self.dependencies
        r.executor = self.executor
        r.max_retries = self.max_retries
        r.retry_interval = self.retry_interval
        instantiate_dict(context, container, r.inputs, self.inputs)
        return r

    def validate(self, context):
        validate_dict_values(context, self.inputs)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.inputs, report_issues)

    def dump(self, context):
        puts(context.style.node(self.name))
        with context.style.indent:
            if self.implementation is not None:
                puts('Implementation: %s' % context.style.literal(self.implementation))
            if self.dependencies:
                puts('Dependencies: %s' % ', '.join((str(context.style.literal(v)) for v in self.dependencies)))
            if self.executor is not None:
                puts('Executor: %s' % context.style.literal(self.executor))
            if self.max_retries is not None:
                puts('Max retries: %s' % context.style.literal(self.max_retries))
            if self.retry_interval is not None:
                puts('Retry interval: %s' % context.style.literal(self.retry_interval))
            dump_properties(context, self.inputs, 'Inputs')

class Artifact(TemplateElement):
    """
    A file associated with a node.

    This class is used by both deployment template and deployment plan elements.

    Properties:
    
    * :code:`name`: Name
    * :code:`type_name`: Must be represented in the :class:`DeploymentContext`
    * :code:`source_path`: Source path (CSAR or repository)
    * :code:`target_path`: Path at destination machine
    * :code:`repository_url`: Repository URL
    * :code:`repository_credential`: Dict of string
    * :code:`properties`: Dict of :class:`Parameter`
    """
    
    def __init__(self, name, type_name, source_path):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        if not isinstance(type_name, basestring):
            raise ValueError('must set type_name (string)')
        if not isinstance(source_path, basestring):
            raise ValueError('must set source_path (string)')
        
        self.name = name
        self.type_name = type_name
        self.source_path = source_path
        self.target_path = None
        self.repository_url = None
        self.repository_credential = StrictDict(key_class=basestring, value_class=basestring)
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('source_path', self.source_path),
            ('target_path', self.target_path),
            ('repository_url', self.repository_url),
            ('repository_credential', as_agnostic(self.repository_credential)),
            ('properties', {k: v.as_raw for k, v in self.properties.iteritems()})))

    def instantiate(self, context, container):
        r = Artifact(self.name, self.type_name, self.source_path)
        r.target_path = self.target_path
        r.repository_url = self.repository_url
        r.repository_credential = self.repository_credential
        instantiate_dict(context, container, r.properties, self.properties)
        return r

    def validate(self, context):
        if context.deployment.artifact_types.get_descendant(self.type_name) is None:
            context.validation.report('artifact "%s" has an unknown type: %s' % (self.name, repr(self.type_name)), level=Issue.BETWEEN_TYPES)        

        validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        puts(context.style.node(self.name))
        with context.style.indent:
            puts('Artifact type: %s' % context.style.type(self.type_name))
            puts('Source path: %s' % context.style.literal(self.source_path))
            if self.target_path is not None:
                puts('Target path: %s' % context.style.literal(self.target_path))
            if self.repository_url is not None:
                puts('Repository URL: %s' % context.style.literal(self.repository_url))
            if self.repository_credential:
                puts('Repository credential: %s' % context.style.literal(self.repository_credential))
            dump_properties(context, self.properties)

class GroupPolicy(TemplateElement):
    """
    Policies applied to groups.

    This class is used by both deployment template and deployment plan elements.

    Properties:
    
    * :code:`name`: Name
    * :code:`type_name`: Must be represented in the :class:`DeploymentContext`
    * :code:`properties`: Dict of :class:`Parameter`
    * :code:`triggers`: Dict of :class:`GroupPolicyTrigger`
    """
    
    def __init__(self, name, type_name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        if not isinstance(type_name, basestring):
            raise ValueError('must set type_name (string)')

        self.name = name
        self.type_name = type_name
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)
        self.triggers = StrictDict(key_class=basestring, value_class=GroupPolicyTrigger)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('properties', {k: v.as_raw for k, v in self.properties.iteritems()}),
            ('triggers', [v.as_raw for v in self.triggers.itervalues()])))

    def instantiate(self, context, container):
        r = GroupPolicy(self.name, self.type_name)
        instantiate_dict(context, container, r.properties, self.properties)
        instantiate_dict(context, container, r.triggers, self.triggers)
        return r

    def validate(self, context):
        if context.deployment.policy_types.get_descendant(self.type_name) is None:
            context.validation.report('group policy "%s" has an unknown type: %s' % (self.name, repr(self.type_name)), level=Issue.BETWEEN_TYPES)        

        validate_dict_values(context, self.properties)
        validate_dict_values(context, self.triggers)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)
        coerce_dict_values(context, container, self.triggers, report_issues)

    def dump(self, context):
        puts(context.style.node(self.name))
        with context.style.indent:
            puts('Group policy type: %s' % context.style.type(self.type_name))
            dump_properties(context, self.properties)
            dump_dict_values(context, self.triggers, 'Triggers')

class GroupPolicyTrigger(TemplateElement):
    """
    Triggers for :class:`GroupPolicy`.
    
    Properties:
    
    * :code:`name`: Name
    * :code:`implementation`: Implementation string (interpreted by the orchestrator)
    * :code:`properties`: Dict of :class:`Parameter`
    """
    
    def __init__(self, name, implementation):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')
        if not isinstance(implementation, basestring):
            raise ValueError('must set implementation (string)')
    
        self.name = name
        self.implementation = implementation
        self.properties = StrictDict(key_class=basestring, value_class=Parameter)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('implementation', self.implementation),
            ('properties', {k: v.as_raw for k, v in self.properties.iteritems()})))

    def instantiate(self, context, container):
        r = GroupPolicyTrigger(self.name, self.implementation)
        instantiate_dict(context, container, r.properties, self.properties)
        return r

    def validate(self, context):
        validate_dict_values(context, self.properties)

    def coerce_values(self, context, container, report_issues):
        coerce_dict_values(context, container, self.properties, report_issues)

    def dump(self, context):
        puts(context.style.node(self.name))
        with context.style.indent:
            puts('Implementation: %s' % context.style.literal(self.implementation))
            dump_properties(context, self.properties)
