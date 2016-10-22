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
from ..utils import print_exception

class Consumer(object):
    """
    Base class for ARIA consumers.
    
    Consumers provide useful functionality by consuming presentations.
    """
    
    def __init__(self, context):
        self.context = context
    
    def consume(self):
        pass
    
    def dump(self):
        pass

    def _handle_exception(self, e):
        if hasattr(e, 'issue') and isinstance(e.issue, Issue):
            self.context.validation.report(issue=e.issue)
        else:
            self.context.validation.report(exception=e)
        if not isinstance(e, AriaError):
            print_exception(e)

class ConsumerChain(Consumer):
    """
    ARIA consumer chain.
    
    Calls consumers in order, handling exception by calling `_handle_exception` on them, 
    and stops the chain if there are any validation issues.
    """

    def __init__(self, context, consumer_classes=None, handle_exceptions=True):
        super(ConsumerChain, self).__init__(context)
        self.handle_exceptions = handle_exceptions
        self.consumers = []
        if consumer_classes:
            for consumer_class in consumer_classes:
                self.append(consumer_class)
    
    def append(self, *consumer_classes):
        for consumer_class in consumer_classes:
            self.consumers.append(consumer_class(self.context))

    def consume(self):
        for consumer in self.consumers:
            try:
                consumer.consume()
            except Exception as e:
                if self.handle_exceptions:
                    consumer._handle_exception(e)
                else:
                    raise e
            if self.context.validation.has_issues:
                break
