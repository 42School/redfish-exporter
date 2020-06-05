import requests
import json
import re
import sys

requests.packages.urllib3.disable_warnings()

"""
    Main request class,
    define default function for HTTP methods
"""
class Req():
    def __init__(self, proto, ip, username=None, password=None, verify=True):
        """ default url for login / search request """
        self._default_url = proto + "://" + ip + '/redfish/v1'
        self._username = username
        self._password = password
        self._verify = verify
        self._session = requests.Session()
        self._session.verify = self._verify
        self._session.auth = (username, password)
        self._reset_ret()

        if username or password:
            self.set_http_basic_auth(username, password)

    """ Sets the http basic authentication information """
    def set_http_basic_auth(self, username, password):
        self._session.auth = (username, password)

    """ reset ret result """
    def _reset_ret(self):
        self.error = None
        self.status = 200

    """ Close this connector and the associated HTTP session."""
    def close(self):
        self._session.close()

    def _req(self, method, path='', data=None):
        url = self._default_url + path
        self._reset_ret()
        response = None

        try:
            response = self._session.request(method, url, data=data, timeout=30)
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.ConnectionError as err:
            self.error = str(err)
            self.status = 503
        except requests.exceptions.Timeout as err:
            self.error = str(err)
            self.status = 522
        except requests.exceptions.RequestException as err:
            self.error = str(err)
            self.status = 500
        except Exception as err:
            self.error = str(err)
            self.status = 500
        return response

    def get(self, path='', data=None):
        resp = self._req('GET', path, data=data)
        return resp, self.error, self.status
