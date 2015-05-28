# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals
import requests
import requests_cache

_base_url = ""
_api_key = ""


def configure(base_url, key):
    """ Configured the modules required parameters used to make authenticated requests

    :param base_url: base url used for requests
    :type base_url: str
    :param key: Bots API Key
    :type key: str
    """
    global _base_url, _api_key
    _base_url = base_url
    _api_key = key


def bot_api_request(endpoint, method='GET', payload=None):
    """ Make an HTTP api request to the tracker using the configured irc key

    :param endpoint:
    :type endpoint:
    :param method:
    :type method:
    :param payload:
    :type payload:
    :return:
    :rtype: dict
    """
    requests_cache.install_cache(cache_name='site_cache', backend='memory', expire_after=10800)
    url = _base_url + endpoint
    headers = {
        'X-IRCBOT-API-KEY': _api_key, 'Content-type': 'application/json',
        'Accept': 'application/json'
    }
    if method == 'GET':
        r = requests.get(url, headers=headers)
    elif method == 'POST':
        r = requests.post(url, headers=headers, data=payload)
    else:
        r = requests.get(url, headers=headers)
    return r.json()
