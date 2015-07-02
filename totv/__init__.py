# -*- coding: utf-8 -*-
"""
General libraries used for totv
"""
from __future__ import unicode_literals, absolute_import
from os.path import expanduser, exists
from os import makedirs

lib_dir = expanduser("~/.config/totv")
if not exists(lib_dir):
    makedirs(lib_dir)
