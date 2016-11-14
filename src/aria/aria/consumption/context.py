# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import threading

from ..validation import ValidationContext
from ..loading import LoadingContext
from ..reading import ReadingContext
from ..presentation import PresentationContext
from ..modeling import ModelingContext
from .style import Style


class ConsumptionContext(object):
    """
    Properties:

    * :code:`args`: The runtime arguments (usually provided on the command line)
    * :code:`out`: Message output stream (defaults to stdout)
    * :code:`style`: Message output style
    * :code:`validation`: :class:`aria.validation.ValidationContext`
    * :code:`loading`: :class:`aria.loading.LoadingContext`
    * :code:`reading`: :class:`aria.reading.ReadingContext`
    * :code:`presentation`: :class:`aria.presentation.PresentationContext`
    * :code:`modeling`: :class:`aria.service.ModelingContext`
    """

    @staticmethod
    def get_thread_local():
        """
        Gets the context attached to the current thread if there is one.
        """

        thread_locals = threading.local()
        return getattr(thread_locals, 'aria_consumption_context', None)

    def __init__(self, set_thread_local=True):
        self.args = []
        self.out = sys.stdout
        self.style = Style()
        self.validation = ValidationContext()
        self.loading = LoadingContext()
        self.reading = ReadingContext()
        self.presentation = PresentationContext()
        self.modeling = ModelingContext()

        if set_thread_local:
            self.set_thread_local()

    def set_thread_local(self):
        """
        Attaches this context to the current thread.
        """

        thread_locals = threading.local()
        thread_locals.aria_consumption_context = self

    def write(self, string):
        """
        Writes to our :code:`out`, making sure to encode UTF-8 if required.
        """

        try:
            self.out.write(string)
        except UnicodeEncodeError:
            self.out.write(string.encode('utf8'))

    def has_arg_switch(self, name):
        name = '--%s' % name
        return name in self.args

    def get_arg_value(self, name, default=None):
        name = '--%s=' % name
        for arg in self.args:
            if arg.startswith(name):
                return arg[len(name):]
        return default

    def get_arg_value_int(self, name, default=None):
        value = self.get_arg_value(name)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
        return default
