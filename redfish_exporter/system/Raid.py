import json
import os
from prometheus_client.core import GaugeMetricFamily

IDRAC8_REDFISH_BASE_URL = '/redfish/v1'
RAID_CTRL_URL = {
    'idrac8': '/Systems/System.Embedded.1/Storage/Controllers',
    'idrac9': '/Systems/System.Embedded.1/Storage'
}

class Raid(object):
    def __init__(self, conn, prefix, config, idrac_version):
        self._conn = conn
        self.prefix = prefix
        self.idrac_version = idrac_version
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
            ret, err, status = self._conn.get(RAID_CTRL_URL[self.idrac_version])
            if err:
                raise Exception(err)

        try:
            """ parse raid controller name """
            for member in ret['Members']:
                raid_ctrl_url = member['@odata.id']
                self._ctrl_list.append(raid_ctrl_url.replace(IDRAC8_REDFISH_BASE_URL + RAID_CTRL_URL[self.idrac_version] + '/', ''))
        except KeyError as e:
            raise Exception(e)

    def _get_metrics(self):

        """ get controllers details """
        for ctrl in self._ctrl_list:
            self._details(ctrl)

    def _get_disk_idrac8(self, ctrl_name, ctrl_status):
        if len(ctrl_status['Devices']) < 1:
            return
        try:
            """ get disk list by controller """
            for disk in ctrl_status['Devices']:
                disk_name = disk['Name']
                """ unused disk name """
                if 'Backplane' not in disk_name and 'Integrated' not in disk_name:
                    if 'Physical Disk' in disk_name:
                        disk_name = disk_name.replace('Physical Disk', 'HDD')
                    elif 'Solid State Disk' in disk_name:
                        disk_name = disk_name.replace('Solid State Disk', 'SSD')
                    disk_status = disk['Status']
                    self.metrics[ctrl_name]['disks'].append({
                        'name': disk_name,
                        'health': disk_status['Health'],
                        'state': disk_status['State']
                    })
        except KeyError as e:
            raise Exception(e)

    def _get_disk_idrac9(self, ctrl_name, ctrl_status):
        if len(ctrl_status['Drives']) < 1:
            return
        try:
            """ get disk link by controller """
            for disk in ctrl_status['Drives']:
                disk_url = disk['@odata.id']
                err = None
                ret, err, status = self._conn.get(disk_url.replace(IDRAC8_REDFISH_BASE_URL, ''))
                if err:
                    raise Exception(err)

                disk_name = ret['Name']
                """ unused disk name """
                if 'Backplane' not in disk_name and 'Integrated' not in disk_name:
                    disk_status = ret['Status']
                    self.metrics[ctrl_name]['disks'].append({
                        'name': disk_name,
                        'health': disk_status['Health'],
                        'state': disk_status['State']
                    })
        except KeyError as e:
            raise Exception(e)

    def _details(self, ctrl_name):
        """ get controllers info """
        if self._config['local']:
            ctrl_status = self._controller_details_json
        else:
            ctrl_status, err, status = self._conn.get(RAID_CTRL_URL[self.idrac_version] + '/' + ctrl_name)
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
        except KeyError:
            raise Exception('Invalid dict key from redfish for controller disk')

        if self.idrac_version == 'idrac8':
            self._get_disk_idrac8(ctrl_name, ctrl_status)
        elif self.idrac_version == 'idrac9':
            self._get_disk_idrac9(ctrl_name, ctrl_status)

    """ transform metric value into valid prom metric value """
    def _cast(self, value):
        valid = ['OK', 'Enabled', True, 'True']
        invalid = ['', 'KO', 'Disabled', 'Critical', None, 'None']

        if value in valid:
            return 1
        return 0

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

        ctrl = GaugeMetricFamily(self.prefix + '_controller', '', labels=['name', 'health', 'state'])
        for metric_name, v in self.metrics.items():
            """ add prefix to metric and expose it """
            sum_status = int(self._cast(v['health']) + self._cast(v['state']))
            ctrl.add_metric([metric_name, v['health'], v['state']], sum_status)

            """ expose disks state """
            if len(v['disks']) > 0:
                gauge = GaugeMetricFamily(self.prefix + '_disk', '', labels=['name', 'controller', 'health', 'state'])
                for disk in v['disks']:
                    sum_status = int(self._cast(disk['health']) + self._cast(disk['state']))
                    gauge.add_metric([disk['name'], metric_name, disk['health'], disk['state']], sum_status)
                yield gauge
        yield ctrl
