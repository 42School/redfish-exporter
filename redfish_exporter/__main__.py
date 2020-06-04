import json
import logging
import yaml
import time
import sys
import os
import logging.config
import pkg_resources
import urllib
import traceback

from os import path
from argparse import ArgumentParser
from time import strftime
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from prometheus_client import push_to_gateway, generate_latest, pushadd_to_gateway
from prometheus_client.exposition import basic_auth_handler

from .Request import Req
from .Collector import Collector

config_logging_file = path.dirname(__file__) + '/../logging-config.ini'
IDRAC_VERSION = ('idrac8', 'idrac9')
config = {
    'local': None,
    'ip': '127.0.0.1',
    'port': 9110,
    'user': None,
    'password': None,
}
__version__ = 1.2

""" TODO: CHECK CONFIG FILE VALIDITY """
 
""" test all remote url and credentials """
def get_idrac_status(hosts):
    for target, host in hosts['hosts'].items():
        req = Req(host['proto'], target, host['username'], host['password'], host['verify'])
        res, err, status = req.get()
        if err:
            return err, status
    return None, 200

""" parse yaml config file """
def parse_config(config_file):
    with open(config_file, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logging.error(exc)

    return config

def scrapeTarget(targets, config):
    for key, value in targets['hosts'].items():
        metrics(key, value, config)

""" use for basic auth to pushgateway """
def my_auth_handler(url, method, timeout, headers, data):
    username = config['user']
    password = config['password']
    return basic_auth_handler(url, method, timeout, headers, data, username, password)

""" Try connexion, exit if cant """
def testPushgatewayConnection(conn, version, config):
    registry = Collector('test_connection', version, conn, 'redfish_exporter', config)

    try:
        metric = generate_latest(registry)
        push_to_gateway(config['ip'] + ':' + str(config['port']), job='push_to_push', registry=registry, handler=my_auth_handler)
    except Exception as e:
        logger.error('Code error: ' + str(e))
        sys.exit(0)

def metrics(target, target_info, config):
    conn = Req(target_info['proto'], target, target_info['username'], target_info['password'], target_info['verify'])

    testPushgatewayConnection(conn, target_info['version'], config)

    """ create collector for each remote """
    if target_info['version'] not in IDRAC_VERSION:
        raise Exception('Invalid idrac version for target: ' + target)

    """ collect data throw redfish library sushi """
    registry = Collector(
        'scrape', # service name
        target_info['version'], # iDRAC version
        conn, # conn object from Req
        'redfish_exporter', # prefix for metrics name
        config # pushgateway config
    )

    push_to_gateway(config['ip'] + ':' + str(config['port']), job=target_info['name'], registry=registry, handler=my_auth_handler)

    logger.info('Succefull metrics push')

logging.config.fileConfig(config_logging_file)
logger = logging.getLogger(__name__)

def main(args=None):
    parser = ArgumentParser()
    parser.add_argument('--local', action='store_true', help='If set, metrics are get form local static json files (testing)')
    parser.add_argument('--config', nargs='?', default='./config.yaml', help='Path to configuration file with targets (config.yml)')
    parser.add_argument('--port', nargs='?', type=int, default='9091', help='Pushgateway remote port')
    parser.add_argument('--ip', nargs='?', default='127.0.0.1', help='Pushgateway ip to which exporter will send metrics')
    parser.add_argument('--user', nargs='?', default='pushgateway', help='Pushgateway user for basic auth')
    parser.add_argument('--password', nargs='?', default='pushgateway', help='Pushgateway password for basic auth')
    params = parser.parse_args(args if args is None else sys.argv[1:])
    targets = parse_config(params.config)

    """ check if target must be scrapped """
    if params.local:
        config['local'] = params.local
    if params.port:
        config['port'] = params.port
    if params.ip:
        config['ip'] = params.ip
    if params.user:
        config['user'] = params.user
    if params.password:
        config['password'] = params.password
    else:
        """ test remote connection before getting metrics """
        err, status = get_idrac_status(targets)
        while err:
            logger.error(err)
            time.sleep(5)
            err, status = get_idrac_status(targets)

    """ start deamon and scrape metrics every x seconds """
    while True:
        try:
            scrapeTarget(targets, config)
        except IOError as e:
            print(traceback.print_exc())
            logger.error("Can't push to '" + config['ip'] + "' " + str(e))
        except Exception as e:
            print(traceback.print_exc())
            logger.error("Can't scrape remote target: " + str(e))
        """ sleep time must be proportional to target number """
        time.sleep(len(targets['hosts'].items()) * 60)

if __name__ == "__main__":
    main()
