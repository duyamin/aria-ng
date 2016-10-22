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

from .validation import Issue
import sys

class AriaError(Exception):
    """
    Base class for ARIA errors.
    """
    
    def __init__(self, message=None, cause=None, cause_tb=None):
        super(AriaError, self).__init__(message)
        self.cause = cause
        if cause_tb is None:
            _, e, tb = sys.exc_info()
            if cause == e:
                # Make sure it's our traceback
                cause_tb = tb
        self.cause_tb = cause_tb

class UnimplementedFunctionalityError(AriaError):
    """
    ARIA error: functionality is unimplemented.
    """

class InvalidValueError(AriaError):
    """
    ARIA error: value is invalid.
    """

    def __init__(self, message, cause=None, cause_tb=None, location=None, line=None, column=None, locator=None, snippet=None, level=Issue.FIELD):
        super(InvalidValueError, self).__init__(message, cause, cause_tb)
        self.issue = Issue(message, location=location, line=line, column=column, locator=locator, snippet=snippet, level=level, exception=cause)
