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

from types import MethodType

class InterfaceMethod(object):
    def __init__(self, fn, interface_name, name=None):
        self.fn = fn
        self.interface_name = interface_name
        self.name = name

class Interface(object):
    pass

def has_interfaces_interface(self, name):
    if not hasattr(self, '_interfaces'):
        setattr(self, '_interfaces', {})

    interface = self._interfaces.get(name)
    
    if interface is None:
        interface_template = self.__class__.INTERFACES.get(name)
        if interface_template is None:
            raise AttributeError('no interface: %s' % name)
        interface = Interface()
        for method in interface_template.itervalues():
            setattr(interface, method.name, MethodType(method.fn, self, None))
        self._interfaces[name] = interface

    return interface

def has_interfaces_iter_interface_names(self):
    return self.__class__.INTERFACES.iterkeys()

def has_interfaces_iter_interface_methods(self):
    for interface_name, interface in self.__class__.INTERFACES.iteritems():
        for method_name in interface:
            yield interface_name, method_name

def has_interfaces(cls):
    # Make sure we have INTERFACES
    if not hasattr(cls, 'INTERFACES'):
        cls.INTERFACES = {}
    
    # Inherit INTERFACES from base classes 
    for base in cls.__bases__:
        if hasattr(base, 'INTERFACES'):
            cls.INTERFACES.update(base.INTERFACES)

    for name, method in cls.__dict__.iteritems():
        if isinstance(method, InterfaceMethod):
            if method.name is None:
                method.name = name
            
            # Accumulate
            interface = cls.INTERFACES.get(method.interface_name)
            if interface is None:
                interface = {}
                cls.INTERFACES[method.interface_name] = interface
            interface[method.name] = method
            
            # Bind stub method
            def closure(name):
                def stub(*args, **kwargs):
                    raise AttributeError('method must be called via its interface: %s' % name)
                return stub
            setattr(cls, name, MethodType(closure(name), None, cls))

    # Bind methods
    setattr(cls, 'interface', MethodType(has_interfaces_interface, None, cls))
    setattr(cls, 'iter_interface_names', MethodType(has_interfaces_iter_interface_names, None, cls))
    setattr(cls, 'iter_interface_methods', MethodType(has_interfaces_iter_interface_methods, None, cls))
    
    return cls

def interfacemethod(interface_name, name=None):
    def decorator(f):
        return InterfaceMethod(f, interface_name, name)
    return decorator
    
