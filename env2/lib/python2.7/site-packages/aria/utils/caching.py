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

from functools import partial
from threading import Lock
from collections import OrderedDict

class cachedmethod(object):
    """
    Decorator for caching method return values.
    
    The implementation is thread-safe.
    
    Supports :code:`cache_info` to be compatible with Python 3's :code:`functools.lru_cache`. Note that the statistics
    are combined for all instances of the class.
    
    Won't use the cache if not called when bound to an object, allowing you to override the cache.
    
    Adapted from `this solution <http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/>`__.
    """
    
    ENABLED = True
    
    def __init__(self, fn):
        self.fn = fn
        self.hits = 0
        self.misses = 0
        self.lock = Lock()

    def cache_info(self):
        with self.lock:
            return (self.hits, self.misses, None, self.misses)
    
    def reset_cache_info(self):
        with self.lock:
            self.hits = 0
            self.misses = 0

    def __get__(self, instance, owner):
        if instance is None:
            # Don't use cache if not bound to an object
            # Note: This is also a way for callers to override the cache
            return self.fn
        return partial(self, instance)
    
    def __call__(self, *args, **kwargs):
        if not self.ENABLED:
            return self.fn(*args, **kwargs)
        
        instance = args[0]
        
        try:
            cache = instance._method_cache
        except AttributeError:
            instance._method_cache = {}
            # Note: Another thread may override it here, so we need to read it again
            # to make sure all threads are using the same cache
            cache = instance._method_cache
            
        key = (self.fn, args[1:], frozenset(kwargs.items()))
        
        try:
            with self.lock:
                r = cache[key]
                self.hits += 1
        except KeyError:
            r = self.fn(*args, **kwargs)
            with self.lock:
                cache[key] = r
                self.misses += 1
            # Another thread may override our cache entry here, so we need to read
            # it again to make sure all threads use the same return value
            r = cache.get(key, r)
            
        return r

class HasCachedMethods(object):
    """
    Provides convenience methods for working with :class:`cachedmethod`.
    """
    
    @property
    def _method_cache_info(self):
        """
        The cache infos of all cached methods.
        
        :rtype: dict of str, 4-tuple
        """
        
        r = OrderedDict()
        for k, p in self.__class__.__dict__.iteritems():
            if isinstance(p, property):
                # The property getter might be cached
                p = p.fget
            if hasattr(p, 'cache_info'):
                r[k] = p.cache_info()
        return r

    def _reset_method_cache(self):
        """
        Resets the caches of all cached methods.
        """
        
        if hasattr(self, '_method_cache'):
            self._method_cache = {}
            
        # Note: Another thread may already be storing entries in the cache here.
        # But it's not a big deal! It only means that our cache_info isn't
        # guaranteed to be accurate.
        
        for p in self.__class__.__dict__.itervalues():
            if isinstance(p, property):
                # The property getter might be cached
                p = p.fget
            if hasattr(p, 'reset_cache_info'):
                p.reset_cache_info()
