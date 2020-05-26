import json
import logging
import yaml
import time
import sys
import os
import logging.config
import pkg_resources

from argparse import ArgumentParser
from time import strftime
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from prometheus_client import push_to_gateway, generate_latest, pushadd_to_gateway

from .Request import Req
from .Collector import Collector

config_logging_file = './logging-config.ini'
IDRAC_VERSION = ('idrac8', 'idrac9')
config = {
    'local': None,
    'ip': '127.0.0.1',
    'port': 9110
}
__version__ = 1.0

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

def metrics(target, target_info, config):
    """ create collector for each remote """
    if target_info['version'] in IDRAC_VERSION:
        conn = Req(target_info['proto'], target, target_info['username'], target_info['password'], target_info['verify'])

    """ collect data throw redfish library sushi """
    registry = Collector(
        'system', # service name
        target_info['version'], # iDRAC version
        conn, # conn object from Req
        'redfish_exporter', # prefix for metrics name
        config # pushgateway config
    )

    metric = generate_latest(registry)
    pushadd_to_gateway(config['ip'] + ':' + str(config['port']), job='superjob', registry=registry)

logging.config.fileConfig(config_logging_file)
""" maxBytes to small number, in order to demonstrate the generation of multiple log files (backupCount). """
handler = RotatingFileHandler("redfish-exporter.log", maxBytes=1024 * 1024 * 100, backupCount=3)
logger = logging.getLogger(__name__)

""" uncomment this line to log requests in file """
logger.addHandler(handler)

def main(args=None):
    parser = ArgumentParser()
    parser.add_argument('--local', default=None, help='If set, metrics are get form local static json files (testing)')
    parser.add_argument('--config', nargs='?', default='./config.yaml', help='Path to configuration file with targets (config.yml)')
    parser.add_argument('--port', nargs='?', type=int, default='9091', help='Pushgateway remote port')
    parser.add_argument('--ip', nargs='?', default='127.0.0.1', help='Pushgateway ip to which exporter will send metrics')
    params = parser.parse_args(args if args is None else sys.argv[1:])
    targets = parse_config(params.config)

    """ check if target must be scrapped """
    if params.local:
        config['local'] = params.local
    if params.port:
        config['port'] = params.port
    if params.ip:
        config['ip'] = params.ip
    else:
        """ test remote connection before getting metrics """
        err, status = get_idrac_status(targets)
        while err:
            logger.error(err)
            time.sleep(5)
            err, status = get_idrac_status(targets)

    """ start deamon and scrape metrics every x seconds """
    while True:
        scrapeTarget(targets, config)
        time.sleep(2 * 60)
