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

from __future__ import absolute_import # so we can import standard 'collections'

from collections import OrderedDict
from copy import deepcopy

def cls_name(cls):
    module = str(cls.__module__)
    name = str(cls.__name__)
    return name if module == '__builtin__' else '%s.%s' % (module, name)

class FrozenList(list):
    """
    An immutable list.
    
    After initialization it will raise :class:`TypeError` exceptions if modification
    is attempted.
    
    Note that objects stored in the list may not be immutable.
    """
    def __init__(self, *args, **kwargs):
        self.locked = False
        super(FrozenList, self).__init__(*args, **kwargs)
        self.locked = True

    def __setitem__(self, index, value):
        if self.locked:
            raise TypeError('read-only list')
        return super(FrozenList, self).__setitem__(index, value)

    def __delitem__(self, index):
        if self.locked:
            raise TypeError('read-only list')
        return super(FrozenList, self).__delitem__(index)
    
    def __iadd__(self, values):
        if self.locked:
            raise TypeError('read-only list')
        return super(FrozenList, self).__iadd__(values)
    
    def __deepcopy__(self, memo):
        r = [deepcopy(v, memo) for v in self]
        return FrozenList(r)

    def append(self, value):
        if self.locked:
            raise TypeError('read-only list')
        return super(FrozenList, self).append(value)

    def extend(self, values):
        if self.locked:
            raise TypeError('read-only list')
        return super(FrozenList, self).append(values)

    def insert(self, index, value):
        if self.locked:
            raise TypeError('read-only list')
        return super(FrozenList, self).insert(index, value)

EMPTY_READ_ONLY_LIST = FrozenList()

class FrozenDict(OrderedDict):
    """
    An immutable ordered dict.
    
    After initialization it will raise :class:`TypeError` exceptions if modification
    is attempted.

    Note that objects stored in the dict may not be immutable.
    """
    
    def __init__(self, *args, **kwargs):
        self.locked = False
        super(FrozenDict, self).__init__(*args, **kwargs)
        self.locked = True

    def __setitem__(self, key, value):
        if self.locked:
            raise TypeError('read-only dict')
        return super(FrozenDict, self).__setitem__(key, value)

    def __delitem__(self, key):
        if self.locked:
            raise TypeError('read-only dict')
        return super(FrozenDict, self).__delitem__(key)
    
    def __deepcopy__(self, memo):
        r = [(deepcopy(k, memo), deepcopy(v, memo)) for k, v in self.iteritems()]
        return FrozenDict(r)

EMPTY_READ_ONLY_DICT = FrozenDict()

class StrictList(list):
    """
    A list that raises :class:`TypeError` exceptions when objects of the wrong type are inserted.
    """
    
    def __init__(self, items=None, value_class=None, wrapper_fn=None, unwrapper_fn=None):
        super(StrictList, self).__init__()
        if isinstance(items, StrictList):
            self.value_class = items.value_class
            self.wrapper_fn = items.wrapper_fn
            self.unwrapper_fn = items.unwrapper_fn
        self.value_class = value_class
        self.wrapper_fn = wrapper_fn
        self.unwrapper_fn = unwrapper_fn
        if items:
            for item in items:
                self.append(item)
    
    def _wrap(self, value):
        if (self.value_class is not None) and (not isinstance(value, self.value_class)):
            raise TypeError('value must be a "%s": %s' % (cls_name(self.value_class), repr(value)))
        if self.wrapper_fn is not None:
            value = self.wrapper_fn(value)
        return value

    def _unwrap(self, value):
        if self.unwrapper_fn is not None:
            value = self.unwrapper_fn(value)
        return value

    def __getitem__(self, index):
        value = super(StrictList, self).__getitem__(index)
        value = self._unwrap(value)
        return value
        
    def __setitem__(self, index, value):
        value = self._wrap(value)
        return super(StrictList, self).__setitem__(index, value)

    def __iadd__(self, values):
        values = [self._wrap(v) for v in values]
        return super(StrictList, self).__iadd__(values)

    def append(self, value):
        value = self._wrap(value)
        return super(StrictList, self).append(value)

    def extend(self, values):
        values = [self._wrap(v) for v in values]
        return super(StrictList, self).extend(values)

    def insert(self, index, value):
        value = self._wrap(value)
        return super(StrictList, self).insert(index, value)

class StrictDict(OrderedDict):
    """
    An ordered dict that raises :class:`TypeError` exceptions when keys or values of the wrong type are used.
    """
    
    def __init__(self, items=None, key_class=None, value_class=None, wrapper_fn=None, unwrapper_fn=None):
        super(StrictDict, self).__init__()
        if isinstance(items, StrictDict):
            self.key_class = items.key_class
            self.value_class = items.value_class
            self.wrapper_fn = items.wrapper_fn
            self.unwrapper_fn = items.unwrapper_fn
        self.key_class = key_class
        self.value_class = value_class
        self.wrapper_fn = wrapper_fn
        self.unwrapper_fn = unwrapper_fn
        if items:
            for k, v in items:
                self[k] = v
    
    def __getitem__(self, key):
        if (self.key_class is not None) and (not isinstance(key, self.key_class)):
            raise TypeError('key must be a "%s": %s' % (cls_name(self.key_class), repr(key)))
        value = super(StrictDict, self).__getitem__(key)
        if self.unwrapper_fn is not None:
            value = self.unwrapper_fn(value)
        return value
        
    def __setitem__(self, key, value):
        if (self.key_class is not None) and (not isinstance(key, self.key_class)):
            raise TypeError('key must be a "%s": %s' % (cls_name(self.key_class), repr(key)))
        if (self.value_class is not None) and (not isinstance(value, self.value_class)):
            raise TypeError('value must be a "%s": %s' % (cls_name(self.value_class), repr(value)))
        if self.wrapper_fn is not None:
            value = self.wrapper_fn(value)
        return super(StrictDict, self).__setitem__(key, value)

def merge(a, b, path=[], strict=False):
    """
    Merges dicts, recursively.
    """
    
    # TODO: a.add_yaml_merge(b), see https://bitbucket.org/ruamel/yaml/src/86622a1408e0f171a12e140d53c4ffac4b6caaa3/comments.py?fileviewer=file-view-default
    
    for key, value_b in b.iteritems():
        if key in a:
            value_a = a[key]
            if isinstance(value_a, dict) and isinstance(value_b, dict):
                merge(value_a, value_b, path + [str(key)], strict)
            elif value_a != value_b:
                if strict:
                    raise ValueError('dict merge conflict at %s' % '.'.join(path + [str(key)]))
                else:
                    a[key] = value_b
        else:
            a[key] = value_b
    return a

def is_removable(container, k, v):
    return (v is None) or ((isinstance(v, dict) or isinstance(v, list)) and (len(v) == 0))

def prune(value, is_removable_fn=is_removable):
    """
    Deletes :code:`None` and empty lists and dicts, recursively.
    """
    
    if isinstance(value, list):
        for i in range(len(value)):
            v = value[i]
            if is_removable_fn(value, i, v):
                del value[i]
            else:
                prune(v, is_removable_fn)
    elif isinstance(value, dict):
        for k, v in value.iteritems():
            if is_removable_fn(value, k, v):
                del value[k]
            else:
                prune(v, is_removable_fn)

    return value

def deepcopy_with_locators(value):
    """
    Like :code:`deepcopy`, but also copies over locators.
    """
    
    r = deepcopy(value)
    copy_locators(r, value)
    return r

def copy_locators(target, source):
    """
    Copies over :code:`_locator` for all elements, recursively.
    
    Assumes that target and source have exactly the same list/dict structure.
    """

    locator = getattr(source, '_locator', None)
    if locator is not None:
        try:
            setattr(target, '_locator', locator)
        except AttributeError:
            pass

    if isinstance(target, list) and isinstance(source, list):
        for i in range(len(target)):
            copy_locators(target[i], source[i])
    elif isinstance(target, dict) and isinstance(source, dict):
        for k, v in target.iteritems():
            copy_locators(v, source[k])
