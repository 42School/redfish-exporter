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


    def set_http_basic_auth(self, username, password):
        """Sets the http basic authentication information."""
        self._session.auth = (username, password)

    def close(self):
        """Close this connector and the associated HTTP session."""
        self._session.close()

    def get_session():
        return self._session

    def _req(self, method, path="", data=None):

        url = self._default_url + path
        try:
            response = self._session.request(method, url, json=data)
        except requests.ConnectionError as e:
            raise exceptions.ConnectionError(url=url, error=e)

        return response

    def get(self, path="", data=None):
        resp = self._req("GET", path, data=data)
        return resp.json()
