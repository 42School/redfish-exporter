__version__ = '0.1'

import time
import random
from prometheus_client import Metric
from Request import Req
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY, InfoMetricFamily

IDRAC8_REDFISH_BASE_URL = "/redfish/v1"
ILO4_REDFISH_BASE_URL = "/rest/v1"
RAID_CTRL_URL = "/Systems/System.Embedded.1/Storage/Controllers"

class Collector(object):
    def __init__(self, service, sys_version, conn, prefix):
        self._service = service
        self._sys_version = sys_version
        self._conn = conn
        self._labels = {}
        self._prefix = prefix
        self._set_labels()

    def _set_labels(self):
        self._labels.update({'service': self._service})

    """ regroup all metrics to be display """
    def _get_metrics(self):

        resp_ctrl_list = self._conn.get(IDRAC8_REDFISH_BASE_URL + RAID_CTRL_URL)

        raids_ctrl = {}
        metrics = {}
        metrics['raid_controller'] = dict()
        metrics['disk'] = dict()
        """ parse raid controller name """
        for member in resp_ctrl_list['Members']:

            raid_ctrl_url = member['@odata.id']
            raid_ctrl_name = raid_ctrl_url.replace(IDRAC8_REDFISH_BASE_URL + RAID_CTRL_URL + '/', '')

            """ get controllers info """
            resp_ctrl_status = self._conn.get(IDRAC8_REDFISH_BASE_URL + RAID_CTRL_URL + '/' + raid_ctrl_name)

            ctrl_status = resp_ctrl_status['Status']
            if ctrl_status['Health'] and ctrl_status['State']:
                metrics['raid_controller'][raid_ctrl_name] = {
                    'health': ctrl_status['Health'],
                    'state': ctrl_status['State']
                }
            else:
                metrics['raid_controller'][raid_ctrl_name] = { 'health': '', 'state': ''}

            """ get disk list by controller """
            for disk in resp_ctrl_status['Devices']:

                disk_name = disk['Name']
                disk_status = disk['Status']
                metrics['disk'][disk_name] = {
                    'health': disk_status['Health'],
                    'state': disk_status['State']
                }

        return metrics

    """ Method called by generate_lastest() prometheud fct """
    def collect(self):
        metrics = self._get_metrics()
        custom_label_names = []
        custom_label_values = []

        """ push exporter version """
        m = GaugeMetricFamily(
            self._prefix + '_version',
            'Version of redfish_exporter running',
            labels=['version'] + custom_label_names)
        m.add_metric([__version__] + custom_label_values, 1.0)
        yield m

        label_names = ['name'] + custom_label_names
        for metric_name, v in metrics.items():
            """ add prefix define in collector call """
            m = InfoMetricFamily(self._prefix + '_' + metric_name, '', labels=label_names)

            for name, value in v.items():
                m.add_metric([name] + custom_label_values, value)
            yield m
