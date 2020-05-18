from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY, InfoMetricFamily
import json
import os

""" get metrics from local json example (faster) """
if os.environ.get('EXPORTER_LOCAL_METRICS'):
    with open('./metrics/Chassis-embedded1.json') as json_data:
        chassis_general_json = json.load(json_data)
    with open('./metrics/PowerSupplies.json') as json_data:
        power_detail_json = json.load(json_data)
    with open('./metrics/Thermal.json') as json_data:
        thermal_detail_json = json.load(json_data)

IDRAC8_REDFISH_BASE_URL = '/redfish/v1'
IDRAC8_REDFISH_MEMBERID = 'iDRAC.Embedded.1#'
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
        """ get metrics from local json example (faster) """
        if os.environ.get('EXPORTER_LOCAL_METRICS'):
            ret = chassis_general_json
        else:
            ret = self._conn.get(CHASSIS_URL)
        try:
            # Pages return 400
            #ret_link = ret['Links']['CooledBy']
            #self._link_list['fan'] = []

            #""" get fans url details link """
            #for link in ret_link:
            #    self._link_list['fan'].append(link['@odata.id'])
            """ get power url details link """
            self._link_list['power'] = ret['Power']['@odata.id'].replace(IDRAC8_REDFISH_BASE_URL, '')
            self._link_list['thermal'] = ret['Thermal']['@odata.id'].replace(IDRAC8_REDFISH_BASE_URL, '')

        except KeyError:
            raise e

    def _get_metrics(self):
        self._details()

    def _details(self):

        try:
            """ get detailed metrics for fans """
            # Pages return 400
            #for fan_link in self._link_list['fan']:
            #    fan_status = self._conn.get(fan_link)
 
            """ get detailed metrics for thermal """
            if os.environ.get('EXPORTER_LOCAL_METRICS'):
                thermal_status = thermal_detail_json
            else:
                thermal_status = self._conn.get(self._link_list['thermal'])

            self._metrics['thermal'] = {
                'location': []
            }
            for temp in thermal_status['Temperatures']:
                self._metrics['thermal']['location'].append({
                    'name': temp['MemberID'].replace(IDRAC8_REDFISH_MEMBERID, ''),
                    'degres': temp['ReadingCelsius'],
                    'limit': temp['UpperThresholdCritical']
                })

            """ get detailed metrics for power """
            if os.environ.get('EXPORTER_LOCAL_METRICS'):
                power_status = power_detail_json
            else:
                power_status = self._conn.get(self._link_list['power'])
            """
                Get redundancy info (same for both powersuppliies)
                Basic metric consumption
            """
            self._metrics['power'] = {
               'health': power_status['PowerSupplies'][0]['Redundancy'][0]['Status']['Health'],
               'state': power_status['PowerSupplies'][0]['Redundancy'][0]['Status']['State'],
               'limit': power_status['PowerControl'][0]['PowerLimit']['LimitInWatts'],
               'average': power_status['PowerControl'][0]['PowerMetrics']['AverageConsumedWatts'],
               'maxconsumed': power_status['PowerControl'][0]['PowerMetrics']['MaxConsumedWatts'],
               'minconsumed': power_status['PowerControl'][0]['PowerMetrics']['MinConsumedWatts'],
               'powersupplies': []
            }

            for powersupply in power_status['PowerSupplies']:
                self._metrics['power']['powersupplies'].append({
                    'name': powersupply['MemberID'].replace(IDRAC8_REDFISH_MEMBERID, ''),
                    'power_capacity': powersupply['PowerCapacityWatts'],
                    'health': powersupply['Status']['Health'],
                    'state': powersupply['Status']['State']
                })

            """ get detailed metrics for fan """
            self._metrics['fan'] = {
                'redundancy_health': thermal_status['Redundancy'][0]['Status']['Health'],
                'redundancy_state': thermal_status['Redundancy'][0]['Status']['State'],
                'list': []
            }
            for temp in thermal_status['Fans']:
                self._metrics['fan']['list'].append({
                    'name': temp['FanName'],
                    'rpm': temp['Reading'],
                    'low_limit': temp['LowerThresholdCritical'],
                    'health': temp['Status']['Health'],
                    'state': temp['Status']['State']
                })

        except KeyError as e:
            raise e

    def _parse_thermal_metrics(metrics):
        thermal = self._metrics['thermal']
        thermal_label_names = ['name', 'limit']

        """ add prefix define in collector call """
        gauge = GaugeMetricFamily(self.prefix + '_thermal', '', labels=thermal_label_names)

        for location in thermal['location']:
            gauge = GaugeMetricFamily(self.prefix + '_thermal_location', '', labels=thermal_label_names)
            gauge.add_metric(['thermal', location['name'], location['limit']], int(location['degres']))
            metrics.append(gauge)

        return metrics

    def _parse_power_metrics(metrics):
        powersupplies_label_names = ['name', 'health', 'state', 'power_capacity']
        power_label_names = ['health', 'state', 'limit', 'average', 'maxconsumed', 'minconsumed']
        power = self._metrics['power']
        """ add prefix define in collector call """
        gauge = GaugeMetricFamily(self.prefix + '_power', '', labels=power_label_names)

        for powersupplie in thermal['powersupplies']:
            gauge = GaugeMetricFamily(self.prefix + '_thermal_location', '', labels=powersupplies_label_names)
            gauge.add_metric(['thermal', powersupplie['name'], location['limit']], int(location['degres']))
            metrics.append(gauge)

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
            'thermal': {
                'location': [{
                    'name': 'InletTemp',
                    'degres': 20,
                    'limit': 75
                },{
                    ...
                    ...
                }]
            },
            'power': {
                'health': 'OK',
                'state': 'Enabled'
                'limit': '315',
                'average': '210',
                'maxconsumed': '220',
                'minconsumed': '200',
                'powersupplies': [{
                        'name': 'PDSU1',
                        'health': 'OK',
                        'state': 'Enabled'
                        'power_capacity': 750
                },{
                    ...
                    ...
                }]
            },
            'fan':
                'redundancy_health': 'OK',
                'redundancy_state': 'Enabled',
                'list': [{
                    'name': "fan1",
                    'rpm': 6300,
                    'low_limit': 800,
                    'health': 'OK',
                    'state': 'Enabled'
                    },{
                        ...
                        ...
                    }
                ]
            }
    """
    def parse_for_prom(self):
        fan_label_names = ['redundancy_health', 'redundancy_state']
        fanlist_label_names = ['name', 'rpm', 'low_limit', 'health', 'state']
        metrics = list()

        metrics = self._parse_thermal_metrics(metrics)
        metrics = self._parse_power_metrics(metrics)

        return metrics
