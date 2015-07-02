# -*- coding: utf-8 -*-
import random
import unittest
import logging
from totv import tracker
from totv import exc

logging.captureWarnings(True)


class ClientTest(unittest.TestCase):
    hash_1 = "40b8b386a0c2f03d492399b9aa7297aefdb84641"
    id_1 = 9999999999999
    name_1 = "test.torrent-group"

    def setUp(self):
        self.client = tracker.Client("https://localhost:34001/api")
        self.client.torrent_add("40b8b386a0c2f03d492399b9aa7297aefdb84641", 100, self.name_1)

    def test_torrent_get(self):
        # TODO this will pass once torrent client get primed onstartup
        t1 = self.client.torrent_get("85a60894fad856dd1340f45a0c8ea8ece9316baa")
        self.assertIsNotNone(t1)
        self.assertEqual(t1['torrent_id'], 3200)
        with self.assertRaises(exc.NotFoundError):
            self.client.torrent_get(999999999999999)

    def test_torrent_add(self):
        resp = self.client.torrent_add(self.hash_1, self.id_1, self.name_1)
        self.assertTrue(resp)

    def test_torrent_del(self):
        resp = self.client.torrent_del(self.id_1)
        self.assertTrue(resp)

    def test_user_get(self):
        resp = self.client.user_get(94)
        self.assertEqual(resp['user_id'], 94)

    def test_user_update(self):
        a = random.randint(0, 1000)
        resp = self.client.user_update(94, downloaded=a, uploaded=a)
        self.assertTrue(resp)

        user = self.client.user_get(94)
        self.assertEqual(user['downloaded'], a)
        self.assertEqual(user['uploaded'], a)

    def test_user_add(self):
        resp = self.client.user_add(999999, "asdfadfasdfasdfasdfasd")
        self.assertTrue(resp)

    def test_whitelist_add(self):
        self.assertTrue(self.client.whitelist_add("test2", "moo"))

    def test_whitelist_del(self):
        resp = self.client.whitelist_del("test2")
        self.assertTrue(resp)

    def test_version(self):
        resp = self.client.version
        self.assertIn("name", resp)
        self.assertIn("version", resp)

    def test_uptime(self):
        resp = self.client.uptime
        self.assertGreater(resp['process'], 0)
        self.assertGreater(resp['system'], 0)
        self.assertGreater(resp['system'], resp['process'])
