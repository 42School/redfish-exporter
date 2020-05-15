from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY, InfoMetricFamily
import json

""" uncomment for testing purpose (faster) """
#with open('./metrics/Controllers-raid-details.json') as json_data:
#    controller_details_json = json.load(json_data)
#with open('./metrics/Controllers-list.json') as json_data:
#    controller_list_json = json.load(json_data)

IDRAC8_REDFISH_BASE_URL = '/redfish/v1'
RAID_CTRL_URL = "/Systems/System.Embedded.1/Storage/Controllers"

class Raid(object):
    def __init__(self, conn, prefix):
        self._conn = conn
        self.prefix = prefix
        self.metrics = {}
        self._ctrl_list = []
        self._list()
        self._get_metrics()

    """ list and parse controllers """
    def _list(self):
        ret = self._conn.get(RAID_CTRL_URL)
        """ uncomment for testing purpose (faster) """
        #ret = controller_list_json
        try:
            """ parse raid controller name """
            for member in ret['Members']:
                raid_ctrl_url = member['@odata.id']
                self._ctrl_list.append(raid_ctrl_url.replace(IDRAC8_REDFISH_BASE_URL + RAID_CTRL_URL + '/', ''))

        except KeyError as e:
            raise "Invalid dict key from redfish response: " + e

    def _get_metrics(self):

        """ get controllers details """
        for ctrl in self._ctrl_list:
            self._details(ctrl)

    def _details(self, ctrl_name):

        """ get controllers info """
        ctrl_status = self._conn.get(RAID_CTRL_URL + '/' + ctrl_name)
        """ uncomment for testing purpose (faster) """
        #ctrl_status = controller_details_json

        try:
            ctrl = ctrl_status['Status']

            """ don't keep unused controller """
            if ctrl['Health'] and ctrl['State']:
                self.metrics[ctrl_name] = {
                    'health': ctrl['Health'],
                    'status': ctrl['State'],
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
            raise "Invalid dict key from redfish response: "

    """ transform metric value into valid prom metric value """
    def _cast(self, value):
        valid = ["OK", "Enabled"]
        invalid = ["", "KO", "Disabled"]

        if value in valid:
            return 1
        elif valid in invalid:
            return 0
        return value

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
        label_names = ['name', 'state', 'health']
        metrics = list()

        for metric_name, v in self.metrics.items():
            """ add prefix define in collector call """
            gauge = GaugeMetricFamily(self.prefix + '_controller', '', labels=label_names)

            """ expose raid status """
            gauge.add_metric([metric_name, v['status'], v['health']], self._cast(v['health']))
            metrics.append(gauge)

            """ expose disks status """
            for disk in v['disks']:
                gauge = GaugeMetricFamily(self.prefix + '_controller_disk', '', labels=label_names + ['disk'])
                gauge.add_metric([metric_name, disk['state'], disk['health'], disk['name']], self._cast(disk['health']))
                metrics.append(gauge)

        return metrics
