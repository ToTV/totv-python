# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, absolute_import


def format_time_delta(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds %= 60
    return hours, minutes, seconds
