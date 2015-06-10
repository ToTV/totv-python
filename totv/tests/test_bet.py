# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, absolute_import
from unittest import TestCase
from totv import db
from totv import bet


class DBTestCase(TestCase):

    def setUp(self):
        self.engine = db.make_engine("sqlite:///:memory:")
        self.connection = self.engine.connect()
        #self.connection.execute("CREATE DATABASE testdb")

    def tearDown(self):
        #self.connection.execute("DROP DATABASE testdb")
        pass


class TestBet(DBTestCase):
    def setUp(self):
        super(TestBet, self).setUp()
        self.person_a = "1"
        self.person_b = "2"

    def test_place_bet(self):
        b = bet.Bet(self.person_a, self.person_b, 200)
        b1_res = bet.place(db.Session(), b)
        self.assertTrue(b1_res)
        self.assertTrue(b.bet_id > 0)


