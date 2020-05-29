import json
from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily

IDRAC8_REDFISH_BASE_URL = '/redfish/v1'
IDRAC8_REDFISH_MEMBERID = 'iDRAC.Embedded.1#'
CHASSIS_URL = "/Chassis/System.Embedded.1"

class Chassis(object):
    def __init__(self, conn, prefix, config):
        self._conn = conn
        self.prefix = prefix
        self._metrics = {}
        self._link_list = {}
        self._config = config
        self._chassis_general_json = {}
        self._power_detail_json = {}
        self._thermal_detail_json = {}
        """ get metrics from local json example (faster) """
        if config['local']:
            with open('./metrics/Chassis-embedded1.json') as json_data:
                self._chassis_general_json = json.load(json_data)
            with open('./metrics/PowerSupplies.json') as json_data:
                self._power_detail_json = json.load(json_data)
            with open('./metrics/Thermal.json') as json_data:
                self._thermal_detail_json = json.load(json_data)

        self._get_link()
        self._get_metrics()

    """ list and parse chassis general information """
    def _get_link(self):
        """ get metrics from local json example (faster) """
        if self._config['local']:
            ret = self._chassis_general_json
        else:
            ret, err, status = self._conn.get(CHASSIS_URL)
            if err:
                raise Exception(err)
        try:
            """ get power url details link """
            self._link_list['power'] = ret['Power']['@odata.id'].replace(IDRAC8_REDFISH_BASE_URL, '')
            self._link_list['thermal'] = ret['Thermal']['@odata.id'].replace(IDRAC8_REDFISH_BASE_URL, '')
            self._metrics['general'] = {
                'power_state': ret['PowerState'],
                'tag_version': ret['SKU'],
                'model': ret['Model'],
                'health': ret['Status']['Health'],
                'state': ret['Status']['State'],
            }

        except KeyError:
            raise Exception("Key error")

    def _get_metrics(self):
        self._details()

    def _details(self):

        try:
            """ get detailed metrics for thermal """
            if self._config['local']:
                thermal_status = self._thermal_detail_json
            else:
                thermal_status, err, status = self._conn.get(self._link_list['thermal'])
                if err:
                    raise Exception(err)

            self._metrics['thermal'] = {
                'location': []
            }
            for temp in thermal_status['Temperatures']:
                temp_name = temp['MemberID'].replace(IDRAC8_REDFISH_MEMBERID, '')
                temp_name = temp_name.replace('SystemBoard', '')
                self._metrics['thermal']['location'].append({
                    'name': temp_name.replace('Temp', ''),
                    'degres': temp['ReadingCelsius'],
                    'limit': temp['UpperThresholdCritical']
                })

            """ get detailed metrics for power """
            if self._config['local']:
                power_status = self._power_detail_json
            else:
                power_status, err, status = self._conn.get(self._link_list['power'])
                if err:
                    raise Exception(err)
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
                    'name': temp['FanName'].replace('System Board Fan', ''),
                    'rpm': temp['Reading'],
                    'low_limit': temp['LowerThresholdCritical'],
                    'health': temp['Status']['Health'],
                    'state': temp['Status']['State']
                })
        except KeyError as e:
            raise e

    """ transform metric value into valid prom metric value """
    def _cast(self, value):
        valid = ['Ok', 'OK', 'Enabled']
        invalid = ['', 'KO', 'Disabled', 'Critical', 'None', '0', None]

        if value in valid:
            return 1
        elif value in invalid:
            return 0
        return float(value)

    """ 
        metrics must be on a specific format for prometheus

        {
            'general': {
                'power_state': 'On',
                'tag_version': 'QWE89IO',
                'model': 'PowerEdge R640',
                'health': 'Critical',
                'state': 'Enabled',
            }
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
        general = self._metrics['general']
        """ return general info """
        info = InfoMetricFamily(self.prefix + '_general', '', labels=[])
        info.add_metric([], general)
        yield info

        fans = self._metrics['fan']
        """ return thermal metrics """
        info = InfoMetricFamily(self.prefix + '_fan_redundancy', '', labels=[])
        info.add_metric([], {
            'health': fans['redundancy_health'] or 'NoValue',
            'state': fans['redundancy_state'] or 'NoValue'
        })
        yield info

        gauge = GaugeMetricFamily(self.prefix + '_fan', '', labels=['name', 'low_limit', 'type'])
        for fan in fans['list']:
            gauge.add_metric([fan['name'], str(fan['low_limit']), 'rpm'], self._cast(fan['rpm']))
            gauge.add_metric([fan['name'], str(fan['low_limit']), 'health'], self._cast(fan['health']))
            gauge.add_metric([fan['name'], str(fan['low_limit']), 'state'], self._cast(fan['state']))
        yield gauge

        thermal = self._metrics['thermal']
        """ return thermal metrics """
        gauge = GaugeMetricFamily(self.prefix + '_thermal_location', '', labels=['name', 'limit'])

        for location in thermal['location']:
            gauge.add_metric([location['name'], str(location['limit'])], location['degres'])
        yield gauge

        power = self._metrics['power']
        """ return power metrics """
        info = InfoMetricFamily(self.prefix + '_power', '', labels=[])
        info.add_metric([], {
            'health': power['health'] or 'NoValue',
            'state': power['state'] or 'NoValue'
        })
        yield info
        gauge = GaugeMetricFamily(self.prefix + '_power_comsumption', 'watt consumption', labels=['type', 'unit', 'limit'])
        gauge.add_metric(['average', 'watt', str(power['limit'])], int(power['average']))
        gauge.add_metric(['maxconsumed', 'watt', str(power['limit'])], int(power['maxconsumed']))
        gauge.add_metric(['minconsumed', 'watt', str(power['limit'])], int(power['minconsumed']))
        yield gauge

        """ return power supply metrics """
        info = InfoMetricFamily(self.prefix + '_power_supply', '', labels=[])
        gauge = GaugeMetricFamily(self.prefix + '_power_supply', '', labels=['type', 'name'])
        for powersupply in power['powersupplies']:
            info.add_metric([], {
                'health': powersupply['health'] or 'NoValue',
                'state': powersupply['state'] or 'NoValue'
            })
            gauge.add_metric(['power_capacity', powersupply['name']], int(powersupply['power_capacity']))

        yield info
        yield gauge
