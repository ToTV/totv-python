# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, absolute_import


class TOTVException(Exception):
    pass


class ValidationError(TOTVException):
    pass


class TrackerError(TOTVException):
    pass


class BadResponse(TrackerError):
    pass


class DuplicateError(TrackerError):
    pass


class NotFoundError(TrackerError):
    pass
