# -*- coding: utf-8 -*-
import random
from string import ascii_lowercase, digits
import unittest
import logging
import http.client as httplib
import random
from totv import tracker
from totv import exc

logging.captureWarnings(True)


def rand_info_hash(n=40):
    return ''.join(random.SystemRandom().choice(ascii_lowercase + digits) for _ in range(n))


class ClientTest(unittest.TestCase):
    """
    This test suite is used to test both the client itself as well as acting as a test suite for the
    tracker and api endpoints used on the tracker. Eventually the tracker will have integrated tests for
    these.
    """
    hash_1 = rand_info_hash()
    id_1 = random.randint(1000000, 1000000000)
    name_1 = "test.torrent.{}-group".format(rand_info_hash(10))
    added = []

    def setUp(self):
        self.client = tracker.Client("https://localhost:34001/api")
        self.tracker_host = "http://localhost:34000/"

    def _load_test_torrent(self):
        self.client.torrent_add(self.hash_1, self.id_1, self.name_1)
        self.added.append(self.hash_1)

    def tearDown(self):
        for ih in self.added:
            try:
                self.client.torrent_del(ih)
            except exc.NotFoundError:
                pass
        self.added = []

    def test_torrent_get(self):
        self._load_test_torrent()
        t1 = self.client.torrent_get(self.hash_1)
        self.assertIsNotNone(t1)
        self.assertEqual(t1['torrent_id'], self.id_1)
        with self.assertRaises(exc.NotFoundError):
            self.client.torrent_get(rand_info_hash())

    def test_torrent_add(self):
        resp = self.client.torrent_add(self.hash_1, self.id_1, self.name_1)
        self.assertEqual(httplib.CREATED, resp.status_code)
        resp2 = self.client.torrent_add(self.hash_1, self.id_1, self.name_1)
        self.assertEqual(httplib.ACCEPTED, resp2.status_code)

    def test_torrent_del(self):
        self._load_test_torrent()
        resp = self.client.torrent_del(self.hash_1)
        self.assertTrue(resp)
        with self.assertRaises(exc.NotFoundError):
            self.client.torrent_del(rand_info_hash())

    def test_user_get(self):
        resp = self.client.user_get(94)
        self.assertEqual(resp['user_id'], 94)
        with self.assertRaises(exc.NotFoundError):
            self.client.user_get(99999999999)

    def test_user_update(self):
        a = random.randint(0, 1000)
        resp = self.client.user_update(94, downloaded=a, uploaded=a*2)
        self.assertTrue(resp)

        user = self.client.user_get(94)
        self.assertEqual(user['downloaded'], a)
        self.assertEqual(user['uploaded'], a*2)

    def test_user_add(self):
        user_name = "test_user_{}".format(rand_info_hash(5))
        user_id = random.randint(1000000, 1000000000)
        passkey = rand_info_hash(22)
        resp = self.client.user_add(user_name, user_id, passkey, can_leech=True)
        self.assertTrue(resp)
        with self.assertRaises(exc.DuplicateError):
            self.client.user_add(user_name, user_id, rand_info_hash(22), can_leech=True)
        self.assertTrue(self.client.user_del(user_id))
        with self.assertRaises(exc.NotFoundError):
            self.client.user_del(user_id)

    def test_whitelist_add(self):
        prefix = rand_info_hash(6)
        client = "test_client_{}".format(rand_info_hash(4))
        resp = self.client.whitelist_add(prefix, client)
        self.assertTrue(resp)

        with self.assertRaises(exc.DuplicateError):
            self.client.whitelist_add(prefix, client)

        self.client.whitelist_del(prefix)

    def test_whitelist_del(self):
        with self.assertRaises(exc.NotFoundError):
            self.client.whitelist_del(rand_info_hash(10))

    def test_version(self):
        resp = self.client.version()
        self.assertIn("name", resp)
        self.assertIn("version", resp)

    def test_uptime(self):
        resp = self.client.uptime()
        self.assertGreater(resp['process'], 0)
        self.assertGreater(resp['system'], 0)
        self.assertGreater(resp['system'], resp['process'])
