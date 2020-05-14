import yaml
import falcon

from wsgiref import simple_server
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from prometheus_client.exposition import generate_latest

from Request import Req
from Collector import Collector
from werkzeug.middleware.dispatcher import DispatcherMiddleware

IDRAC_VERSION = ('idrac8', 'idrac9')

class metricHandler:
    def __init__(self, config_file):
        self._config_file = config_file
        self._hosts = dict()

    def parse_config(self, config_file):
        with open(config_file, 'r') as stream:
            try:
                config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        self._hosts = config

    def on_get(self, req, resp, target):
        resp.set_header('Content-Type', CONTENT_TYPE_LATEST)

        self.parse_config(self._config_file)

        """ TODO: CHECK CONFIG FILE VALIDITY """

        """ throw error if target not found """
        if target not in self._hosts['hosts']:
            resp.status = falcon.HTTP_404
            resp.body = 'not found'
            return
        host = self._hosts['hosts'][target]

        """ create collector for each remote """
        if host['version'] in IDRAC_VERSION:
            conn = Req(host['proto'], target, host['username'], host['password'], host['verify'])

        """ collect data throw redfish library sushi """
        registry = Collector(
            'system', # service name
            host['version'], # iDRAC version
            conn, # conn object from Req
            'redfish_exporter' # prefix for metrics name
        )

        collected_metric = generate_latest(registry)
        resp.body = collected_metric

"""
    Main app
"""
def falcon_app(config_file="./config.yaml", ip="127.0.0.1", port=9111):
    print('starting server http://127.0.0.1:{}/metrics'.format(port))
    api = falcon.API()
    api.add_route(
            '/metrics/{target}',
            metricHandler(config_file=config_file)
    )

    httpd = simple_server.make_server(ip, port, api)
    httpd.serve_forever()
