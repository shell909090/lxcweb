#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2014-01-13
@author: shell.xu
'''
from distutils.core import setup

version = '1.0'
description = 'lxc management system in web'
long_description = ' lxc management system in web, written by webpy.'

setup(
    name='lxcweb', version=version,
    description=description, long_description=long_description,
    author='Shell.E.Xu', author_email='shell909090@gmail.com',
    packages=['lxcweb',],
    data_files=[
        ('/etc/lxcweb/', ['lxcweb.conf',]),
        ('/usr/share/lxcweb/', ['static',]),
    ]
)
