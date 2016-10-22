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

from .. import AriaError
from ..validation import Issue

class ReaderError(AriaError):
    """
    ARIA reader error.
    """

class ReaderNotFoundError(ReaderError):
    """
    ARIA reader error: reader not found for source.
    """

class ReaderSyntaxError(ReaderError):
    """
    ARIA read format error.
    """

    def __init__(self, message, cause=None, cause_tb=None, location=None, line=None, column=None, locator=None, snippet=None, level=Issue.SYNTAX):
        super(ReaderError, self).__init__(message, cause, cause_tb)
        self.issue = Issue(message, location=location, line=line, column=column, locator=locator, snippet=snippet, level=level)

class AlreadyReadError(ReaderError):
    """
    ARIA reader error: already read.
    """
