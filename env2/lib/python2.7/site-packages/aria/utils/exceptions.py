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

from .console import puts, colored, indent
import sys, linecache 

def print_exception(e, full=True, cause=False, tb=None):
    """
    Prints the exception with nice colors and such.
    """
    def format_heading(e):
        return '%s%s: %s' % (colored.red('Caused by ') if cause else '', colored.red(e.__class__.__name__, bold=True), colored.red(e))

    puts(format_heading(e))
    if full:
        if cause:
            if tb:
                print_traceback(tb)
        else:
            print_traceback()
    if hasattr(e, 'cause') and e.cause:
        tb = e.cause_tb if hasattr(e, 'cause_tb') else None
        print_exception(e.cause, full=full, cause=True, tb=tb)

def print_traceback(tb=None):
    """
    Prints the traceback with nice colors and such.
    """
    
    if tb is None:
        _, _, tb = sys.exc_info()
    while tb is not None:
        frame = tb.tb_frame
        lineno = tb.tb_lineno
        code = frame.f_code
        filename = code.co_filename
        name = code.co_name
        with indent(2):
            puts('File "%s", line %s, in %s' % (colored.blue(filename), colored.cyan(lineno), colored.cyan(name)))
            linecache.checkcache(filename)
            line = linecache.getline(filename, lineno, frame.f_globals)
            if line:
                with indent(2):
                    puts(colored.black(line.strip()))
        tb = tb.tb_next
