from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY, InfoMetricFamily
import json

""" uncomment for testing purpose (faster) """
with open('./metrics/Chassis-embedded1.json') as json_data:
    chassis_general_json = json.load(json_data)
with open('./metrics/PowerSupplies.json') as json_data:
    power_detail_json = json.load(json_data)
with open('./metrics/Thermal.json') as json_data:
    thermal_detail_json = json.load(json_data)

IDRAC8_REDFISH_BASE_URL = '/redfish/v1'
CHASSIS_URL = "/Chassis/System.Embedded.1"

class Chassis(object):
    def __init__(self, conn, prefix):
        self._conn = conn
        self.prefix = prefix
        self._metrics = {}
        self._link_list = {}
        self._get_link()
        self._get_metrics()

    """ list and parse chassis general information """
    def _get_link(self):
        ret = self._conn.get(CHASSIS_URL)

        """ uncomment for testing purpose (faster) """
        ret = chassis_general_json
        try:
            # Pages return 400
            #ret_link = ret['Links']['CooledBy']
            #self._link_list['fan'] = []

            #""" get fans url details link """
            #for link in ret_link:
            #    self._link_list['fan'].append(link['@odata.id'])

            ret_link = ret['Links']['PoweredBy']
            self._link_list['power'] = []
            """ get power url details link """
            for link in ret_link:
                self._link_list['power'].append(link['@odata.id'].replace(IDRAC8_REDFISH_BASE_URL, ''))
            self._link_list['thermal'] = ret['Thermal']['@odata.id'].replace(IDRAC8_REDFISH_BASE_URL, '')

        except KeyError as e:
            raise "Invalid dict key from redfish response: " + e

    def _get_metrics(self):
        self._details()

    def _details(self):

        try:
            """ get detailed metrics for fans """
            # Pages return 400
            #for fan_link in self._link_list['fan']:
            #    fan_status = self._conn.get(fan_link)

            """ get detailed metrics for power """
            for power_link in self._link_list['power']:
                power_status = self._conn.get(power_link)

                """ uncomment for testing purpose (faster) """
                power_status = power_detail_json
                self._metrics['power'] = {
                    'name': power_status['MemberID'],
                    'power_capacity': power_status['PowerCapacityWatts'],
                    'health': power_status['Status']['Health'],
                    'state': power_status['Status']['State'],
                    'redundancy': {
                        'health': power_status['Redundancy'][0]['Status']['Health'],
                        'state': power_status['Redundancy'][0]['Status']['State'],

                    }
                }

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

        for metric_name, v in self._metrics.items():
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
