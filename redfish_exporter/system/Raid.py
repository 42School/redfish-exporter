import json
import os
from prometheus_client.core import InfoMetricFamily

IDRAC8_REDFISH_BASE_URL = '/redfish/v1'
RAID_CTRL_URL = "/Systems/System.Embedded.1/Storage/Controllers"

class Raid(object):
    def __init__(self, conn, prefix, config):
        self._conn = conn
        self.prefix = prefix
        self.metrics = {}
        self._ctrl_list = []
        self._config = config
        self._controller_details_json = {}
        self._controller_list_json = {}

        """ get local metrics for testing (faster) """
        if config['local']:
            with open('./metrics/Controllers-raid-details.json') as json_data:
                self._controller_details_json = json.load(json_data)
            with open('./metrics/Controllers-list.json') as json_data:
                self._controller_list_json = json.load(json_data)

        self._list()
        self._get_metrics()

    """ list and parse controllers """
    def _list(self):
        err = None
        if self._config['local']:
            ret = self._controller_list_json
        else:
            ret, err, status = self._conn.get(RAID_CTRL_URL)
            if err:
                raise Exception(err)

        try:
            """ parse raid controller name """
            for member in ret['Members']:
                raid_ctrl_url = member['@odata.id']
                self._ctrl_list.append(raid_ctrl_url.replace(IDRAC8_REDFISH_BASE_URL + RAID_CTRL_URL + '/', ''))
        except KeyError as e:
            raise Exception(e)

    def _get_metrics(self):

        """ get controllers details """
        for ctrl in self._ctrl_list:
            self._details(ctrl)

    def _details(self, ctrl_name):
        """ get controllers info """
        if self._config['local']:
            ctrl_status = self._controller_details_json
        else:
            ctrl_status, err, status = self._conn.get(RAID_CTRL_URL + '/' + ctrl_name)
            if err:
                raise Exception(err)

        try:
            ctrl = ctrl_status['Status']

            """ don't keep unused controller """
            if ctrl['Health'] and ctrl['State']:
                self.metrics[ctrl_name] = {
                    'health': ctrl['Health'],
                    'state': ctrl['State'],
                    'disks': []
                }

            """ get disk list by controller """
            for disk in ctrl_status['Devices']:

                disk_name = disk['Name']
                disk_status = disk['Status']
                self.metrics[ctrl_name]['disks'].append({
                    'name': disk_name,
                    'health': disk_status['Health'],
                    'state': disk_status['State']
                })
        except KeyError:
            msg = "Invalid dict key from redfish response"
            raise Exception(msg)

    """ 
        metrics must be on a specific format for prometheus

        {
            'controller1': {
                'health': 'OK',
                'state': 'Enabled'
                'disks': [{
                        'name': 'disk1',
                        'health': 'OK',
                        'state': 'Enabled'
                    },{
                        ...
                        ...
                }]
            },
                ...
                ...
        }
    """
    def parse_for_prom(self):
        metrics = list()

        for metric_name, v in self.metrics.items():
            """ add prefix to metric and expose it """
            info = InfoMetricFamily(self.prefix + '_controller', '', labels=[])
            info.add_metric([], {
                'health': v['health'] or 'NoValue',
                'state': v['state'] or 'NoValue'
            })
            yield info

            """ expose disks state """
            info = InfoMetricFamily(self.prefix + '_disk', '', labels=[])
            for disk in v['disks']:
                info.add_metric([], disk)
            yield info
