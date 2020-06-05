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
        self.metrics['controllers'] = list()
        self.metrics['disks'] = list()

        """ get controllers details """
        for ctrl in self._ctrl_list:
            self._details(ctrl)

    def _disk_name(self, disk_name):
        if 'Physical Disk' in disk_name:
            disk_name = disk_name.replace('Physical Disk', 'HDD')
        elif 'Solid State Disk' in disk_name:
            disk_name = disk_name.replace('Solid State Disk', 'SSD')
        return disk_name

    def _get_disk_idrac8(self, ctrl_name, ctrl_status):
        if len(ctrl_status['Devices']) < 1:
            return
        try:
            """ get disk list by controller """
            for disk in ctrl_status['Devices']:

                disk_name = disk['Name']
                if 'Backplane' not in disk_name and 'Integrated' not in disk_name:
                    disk_status = disk['Status']
                    disk_name = self._disk_name(disk_name)
                    health = disk_status['Health'] if disk_status['Health'] else 'NoValue'
                    state = disk_status['State'] if disk_status['State'] else 'NoValue'

                    self.metrics['disks'].append({
                        'controller': ctrl_name,
                        'name': disk_name,
                        'health': health,
                        'state': state
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
                    disk_name = self._disk_name(disk_name)
                    disk_status = ret['Status']
                    health = disk_status['Health'] if disk_status['Health'] else 'NoValue'
                    state = disk_status['State'] if disk_status['State'] else 'NoValue'

                    self.metrics['disks'].append({
                        'controller': ctrl_name,
                        'name': disk_name,
                        'health': health,
                        'state': state
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
                self.metrics['controllers'].append({
                    'name': ctrl_name,
                    'health': ctrl['Health'],
                    'state': ctrl['State'],
                })
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
        """ add prefix to metric and expose controller it """
        ctrl = GaugeMetricFamily(self.prefix + '_controller', '', labels=['name', 'health', 'state'])

        for controller in self.metrics['controllers']:
            sum_status = int(self._cast(controller['health']) + self._cast(controller['state']))
            ctrl.add_metric([controller['name'], controller['health'], controller['state']], sum_status)

        yield ctrl

        """ add prefix to metric and expose disk it """
        gauge = GaugeMetricFamily(self.prefix + '_disk', '', labels=['controller','name', 'state', 'health'])

        for disk in self.metrics['disks']:
            sum_status = int(self._cast(disk['health']) + self._cast(disk['state']))
            gauge.add_metric([disk['controller'], disk['name'], disk['state'], disk['health']], sum_status)
        yield gauge
