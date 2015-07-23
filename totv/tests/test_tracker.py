# -*- coding: utf-8 -*-
from string import ascii_lowercase, digits
import unittest
import logging
import http.client as httplib
import random
from urllib.parse import quote_plus
import bencodepy
import binascii
import requests
from totv import tracker
from totv import exc

logging.captureWarnings(True)


def rand_info_hash(n=40):
    return ''.join(random.SystemRandom().choice(ascii_lowercase[0:6] + digits) for _ in range(n))


def hex2bin(hex_info_hash):
    return binascii.a2b_hex(hex_info_hash.upper())


class FakeTorrentClient(object):
    """
    Emulates a client, allowing simple customizations of each request type.
    """
    def __init__(self, info_hash=None, passkey=None, host="http://localhost:30000/", peer_id=None,
                 port=12345, uploaded=0, downloaded=0, left=0, corrupt=0, key=None, numwant=30,
                 supportcrypto=1, no_peer_id=1, ip="12.34.56.78"):
        self.passkey = passkey or rand_info_hash(32)
        self._params = {
            "info_hash": info_hash or rand_info_hash(),
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
        for k in ['info_hash']:
            try:
                params[k] = hex2bin(params[k])
            except KeyError:
                pass
        try:
            params['peer_id'] = quote_plus(params['peer_id'])
        except KeyError:
            pass
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


class TestTorrent(object):
    def __init__(self, info_hash, torrent_id, name):
        self.info_hash = info_hash
        self.torrent_id = torrent_id
        self.name = name


class TestUser(object):
    def __init__(self, username, user_id, passkey):
        self.username = username
        self.user_id = user_id
        self.passkey = passkey


class _TrackerTestBase(unittest.TestCase):
    _added = []
    _users = []
    _ip = "10.0.10.232"
    _torrent_client = FakeTorrentClient()

    def setUp(self):
        self.client = tracker.Client("https://{}:34001/api".format(self._ip))
        self.tracker_host = "http://{}:34000/".format(self._ip)
        self._torrent_client = FakeTorrentClient(host="http://{}:34000/".format(self._ip))
        try:
            self.client.whitelist_add("-DE", "Deluge Test")
        except exc.DuplicateError:
            pass

    def tearDown(self):
        """ Cleanup anything that may be left """
        for ih in self._added:
            try:
                self.client.torrent_del(ih)
            except exc.NotFoundError:
                pass
        self._added = []
        for user_id in self._users:
            try:
                self.client.user_del(user_id)
            except exc.NotFoundError:
                pass
        self._users = []
        try:
            self.client.whitelist_del("-DE")
        except exc.NotFoundError:
            pass

    def _rand_torrent_name(self):
        """ Generate a random torrent name that should be unique """
        return "test.torrent.{}-group".format(rand_info_hash(10))

    def _load_test_torrent(self, info_hash=None, torrent_id=None, name=None):
        """
        :rtype: TestTorrent
        """
        if info_hash is None:
            info_hash = rand_info_hash()
        if torrent_id is None:
            torrent_id = random.randint(100000, 99999999)
        if name is None:
            name = self._rand_torrent_name()
        self.client.torrent_add(info_hash, torrent_id, name)
        self._added.append(info_hash)
        return TestTorrent(info_hash, torrent_id, name)

    def _load_test_user(self, user_name=None, user_id=None, passkey=None):
        """
        :rtype: TestUser
        """
        if user_name is None:
            user_name = rand_info_hash(10)
        if user_id is None:
            user_id = random.randint(100000, 99999999)
        if passkey is None:
            passkey = rand_info_hash(32)
        try:
            self.client.user_add(user_name, user_id, passkey)
        except exc.DuplicateError:
            pass
        self._users.append(user_id)
        return TestUser(user_name, user_id, passkey)

    def assertTrackerErrorOK(self, expected_status, resp):
        """
        Make sure the error response returned is the expected one.
        """
        self.assertEqual(expected_status, resp.status_code, "Got unexpected status code: {}".format(resp.status_code))
        self.assertBencodedValues(resp.content, {b"failure reason": tracker.messages[resp.status_code]})

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

    def _rand_peer_id(self):
        return "-DE-{}".format(rand_info_hash(6))


class TrackerTest(_TrackerTestBase):
    """
    This test suite is used to test both the client itself as well as acting as a test suite for the
    tracker and api endpoints used on the tracker. Eventually the tracker will have integrated tests for
    these.
    """

    def test_announce(self):
        user = self._load_test_user()
        tor = self._load_test_torrent()
        self._torrent_client.passkey = user.passkey
        self._torrent_client._params['info_hash'] = tor.info_hash

        # Check for first peer added
        passkey1, peer_id1 = rand_info_hash(32), self._rand_peer_id()
        opts_1 = {'passkey': passkey1, 'peer_id': peer_id1}
        resp = self._torrent_client.announce(opts_1)
        self.assertTrue(resp.ok)
        peers = self.client.get_torrent_peers(tor.info_hash)
        self.assertIn(peer_id1, [p['peer_id'] for p in peers])

        # Add a 2nd
        passkey2, peer_id2 = rand_info_hash(32), self._rand_peer_id()
        self._torrent_client.announce({'passkey': passkey2, 'peer_id': peer_id2})
        peers2 = self.client.get_torrent_peers(tor.info_hash)
        self.assertEqual(2, len(peers2))
        self.assertIn(peer_id2, [p['peer_id'] for p in peers2])

        # Try and remove the 1st peer
        self.assertTrue(self._torrent_client.stop(opts_1).ok)

        # Make sure it is removed from swarm
        self.assertEqual(1, len(self.client.get_torrent_peers(tor.info_hash)))

    def test_announce_bad_passkey(self):
        # Test for a invalid passkey
        resp_1 = self._torrent_client.announce(options={'info_hash': rand_info_hash()})
        self.assertEqual(tracker.MSG_INVALID_AUTH, resp_1.status_code)
        self.assertBencodedValues(resp_1.content, {b"failure reason": b"Invalid passkey supplied"})

    def test_announce_bad_infohash(self):
        # Test for a invalid info_hash
        self._torrent_client.passkey = self._load_test_user().passkey
        self.assertTrackerErrorOK(
            tracker.MSG_INFO_HASH_NOT_FOUND,
            self._torrent_client.announce(options={'info_hash': rand_info_hash()})
        )
        self.assertTrackerErrorOK(
            tracker.MSG_QUERY_PARSE_FAIL,
            self._torrent_client.announce(options={'info_hash': ""})
        )

    def test_announce_missing_params(self):
        self._torrent_client._params['info_hash'] = self._load_test_torrent().info_hash
        self._torrent_client.passkey = self._load_test_user().passkey
        del self._torrent_client._params['port']
        del self._torrent_client._params['left']
        self.assertTrackerErrorOK(tracker.MSG_QUERY_PARSE_FAIL, self._torrent_client.announce())

    def test_announce_bonus(self):
        self._torrent_client._params['info_hash'] = self._load_test_torrent().info_hash
        user = self._load_test_user()
        self._torrent_client.passkey = user.passkey

        data = self.client.user_get(user.user_id)
        self.assertEqual(0, data['points'])
        self._torrent_client.announce(options={"uploaded": 1})

        self.client.user_update(user.user_id, uploaded=1000000000001)

        self._torrent_client.announce(options={"uploaded": 1000000000001})
        data_3 = self.client.user_get(user.user_id)
        self.assertEqual(data_3['points'], 1)


class ClientTest(_TrackerTestBase):
    """
    Tests for the API portion of the tracker, using the client library.
    """
    def test_torrent_get(self):
        tor = self._load_test_torrent()
        t1 = self.client.torrent_get(tor.info_hash)
        self.assertIsNotNone(t1)
        self.assertEqual(t1['torrent_id'], tor.torrent_id)
        with self.assertRaises(exc.NotFoundError):
            self.client.torrent_get(rand_info_hash())

    def test_torrent_counts(self):
        tor = self._load_test_torrent()
        counts = self.client.get_torrent_counts()
        self.assertTrue(len(counts) >= 1)
        for i in counts:
            if i['info_hash'] == tor.info_hash:
                break
        else:
            self.fail("Could not find matching entry")

    def test_torrent_add(self):
        name = self._rand_torrent_name()
        torrent_id = random.randint(999999, 99999999)
        info_hash = rand_info_hash()
        self._added.append(info_hash)
        resp = self.client.torrent_add(info_hash, torrent_id, name)
        self.assertEqual(httplib.CREATED, resp.status_code)
        resp2 = self.client.torrent_add(info_hash, torrent_id, name)
        self.assertEqual(httplib.ACCEPTED, resp2.status_code)
        self._added.append(info_hash)

    def test_torrent_del(self):
        tor = self._load_test_torrent()
        resp = self.client.torrent_del(tor.info_hash)
        self.assertTrue(resp)
        with self.assertRaises(exc.NotFoundError):
            self.client.torrent_del(rand_info_hash())

    def test_user_get(self):
        self._load_test_user()
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

if __name__ == '__main__':
    unittest.main()
