# -*- coding: utf-8 -*-
from string import ascii_lowercase, digits
import unittest
import logging
import http.client as httplib
import random
from urllib.parse import quote_plus
import bencodepy
import requests
from totv import tracker
from totv import exc

logging.captureWarnings(True)


def rand_info_hash(n=40):
    return ''.join(random.SystemRandom().choice(ascii_lowercase + digits) for _ in range(n))


class FakeTorrentClient(object):
    """
    Emulates a client, allowing simple customizations of each request type.
    """
    def __init__(self, info_hash=None, passkey=None, host="http://localhost:30000/", peer_id=None,
                 port=12345, uploaded=0, downloaded=0, left=0, corrupt=0, key=None, numwant=30,
                 supportcrypto=1, no_peer_id=1, ip="12.34.56.78"):
        self.passkey = passkey or rand_info_hash(32)
        self._params = {
            "info_hash": quote_plus(info_hash or rand_info_hash()),
            "peer_id": peer_id or "-DE13B0-!ixmP~saB1w4",
            "uploaded": uploaded,
            "downloaded": downloaded,
            "left": left,
            "ip": ip,
            "port": port,
            "corrupt": corrupt,
            "key": key or rand_info_hash(8).upper(),
            "numwant": numwant,
            "compact": 1,
            "no_peer_id": no_peer_id,
            "supportcrypto": supportcrypto,
            "event": "started"
        }
        self.host = host

    def _make_url(self, endpoint):
        return "{}{}{}".format(self.host, self.passkey, endpoint)

    def _gen_params(self, options=None):
        params = self._params.copy()
        if options:
            params.update(options)
        return params

    def announce(self, options=None, event="announce"):
        params = self._gen_params(options)
        params['event'] = event
        return requests.get(self._make_url("/announce"), params=params)

    def stop(self, options=None):
        return self.announce(options=options, event="stopped")

    def start(self, options=None):
        return self.announce(options=options, event="start")

    def completed(self, options=None):
        return self.announce(options=options, event="completed")


class ClientTest(unittest.TestCase):
    """
    This test suite is used to test both the client itself as well as acting as a test suite for the
    tracker and api endpoints used on the tracker. Eventually the tracker will have integrated tests for
    these.
    """
    hash_1 = rand_info_hash()
    id_1 = random.randint(1000000, 1000000000)
    name_1 = "test.torrent.{}-group".format(rand_info_hash(10))
    user_name = "test_user"
    user_id = 99999999
    passkey = rand_info_hash(32)
    added = []

    def setUp(self):
        self.client = tracker.Client("https://localhost:34001/api")
        self.tracker_host = "http://localhost:34000/"
        self.client.user_add(self.user_name, self.user_id, self.passkey)

    def _load_test_torrent(self):
        self.client.torrent_add(self.hash_1, self.id_1, self.name_1)
        self.added.append(self.hash_1)

    def assertBencodedValues(self, benc_str, checks=None):
        try:
            benc_data = bencodepy.decode(benc_str)
        except bencodepy.DecodingError as err:
            self.fail(err)
        else:
            if checks:
                self.assertDictContainsSubset(checks, benc_data)
                # for k, v in checks.items():
                #     self.assertEqual(v, benc_data[k])

    def tearDown(self):
        for ih in self.added:
            try:
                self.client.torrent_del(ih)
            except exc.NotFoundError:
                pass
        self.added = []
        self.client.user_del(self.user_id)

    def test_announce(self):
        self._load_test_torrent()
        torrent_client = FakeTorrentClient(info_hash=self.hash_1, host="http://127.0.0.1:34000/")
        resp = torrent_client.announce()
        self.assertTrue(resp.ok)
        peers = self.client.get_torrent_peers(self.hash_1)
        for peer in peers:
            if peer['peer_id'] == torrent_client._params['peer_id']:
                break
        else:
            self.fail("Could not find peer in active swarm")

    def test_announce_failures(self):
        self._load_test_torrent()
        torrent_client = FakeTorrentClient(info_hash=self.hash_1, host="http://127.0.0.1:34000/")
        resp_1 = torrent_client.announce(options={'info_hash': rand_info_hash()})
        self.assertEqual(900, resp_1.status_code)
        self.assertBencodedValues(resp_1.content, {b"failure reason": b"Generic Error :("})

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
