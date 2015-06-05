# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, absolute_import
from unittest import TestCase
from totv.service import tvrage


class TestBet(TestCase):

    def test_schedule(self):
        sched = tvrage.schedule("pqJG6PX20cXzXM2QSNqC")
        self.assertTrue(sched)


