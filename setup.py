#!/usr/bin/env python

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

from setuptools import setup
import sys

if sys.version_info < (2, 7):
    sys.exit('ARIA requires Python 2.7+')
if sys.version_info >= (3, 0):
    sys.exit('ARIA does not support Python 3')

setup(
    name='aria',
    version='0.1',
    description='ARIA',
    license='Apache License Version 2.0',

    author='GigaSpaces',
    author_email='info@ariatosca.org',
    
    url='http://ariatosca.org/',
    download_url='https://github.com/aria-tosca',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration'],

    packages=[
        'aria',
        'aria.consumption',
        'aria.deployment',
        'aria.loading',
        'aria.presentation',
        'aria.reading',
        'aria.tools',
        'aria.utils',
        'aria.validation',
        'aria_extension_tosca',
        'aria_extension_tosca.v1_0',
        'aria_extension_tosca.v1_0.utils'],

    package_dir={
        'aria': 'src/aria/aria',
        'aria_extension_tosca': 'src/tosca/aria_extension_tosca'},
      
    package_data={
        'aria.tools': [
            'web/**'],
        'aria_extension_tosca': [
            'profiles/tosca-simple-profile-1.0/**',
            'profiles/tosca-simple-nfv-1.0/**']},
    
    scripts=[
        'src/aria/scripts/aria',
        'src/aria/scripts/aria-rest'],
      
    # Please make sure this is in sync with src/aria/requirements.txt
    install_requires=[
        'ruamel.yaml==0.12.13',
        'clint==0.5.1',
        'Jinja2==2.8',
        'requests==2.11.1',
        'CacheControl[filecache]==0.11.6',
        'shortuuid==0.4.3'])
