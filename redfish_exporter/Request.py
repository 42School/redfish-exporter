import requests
import json
import re
import sys

"""
    Main request class,
    define default function for HTTP methods
"""
class Req():
    def __init__(self, proto, ip, username=None, password=None, verify=True):
        """ default url for login / search request """
        self._default_url = proto + "://" + ip
        self._username = username
        self._password = password
        self._verify = verify
        self._session = requests.Session()
        self._session.verify = self._verify
        self._session.auth = (username, password)

        if username or password:
            self.set_http_basic_auth(username, password)

    """ Sets the http basic authentication information """
    def set_http_basic_auth(self, username, password):
        self._session.auth = (username, password)

    """ Close this connector and the associated HTTP session."""
    def close(self):
        self._session.close()

    """ special auth function for ilo (connexion with session instead of basic auth """
    def ilo_auth(self):
        auth_url = '/rest/v1/Sessions'
        data = {
            'UserName': self._username,
            'Password': self._password
        }
        self._req('POST', auth_url, data)

    def _req(self, method, path='', data=None):

        url = self._default_url + path
        try:
            response = self._session.request(method, url, data=data)
        except requests.ConnectionError as e:
            raise e

        return response

    def get(self, path="", data=None):
        resp = self._req("GET", path, data=data)
        return resp.json()
