from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY, InfoMetricFamily

IDRAC8_REDFISH_BASE_URL = '/redfish/v1'
RAID_CTRL_URL = "/Systems/System.Embedded.1/Storage/Controllers"

status = [{
        'type': 'health',
        'value': 0
    },{
        'type': 'state',
        'value': 0
}]

class Raid(object):
    def __init__(self, conn, prefix):
        self._conn = conn
        self.prefix = prefix
        self.metrics = {}

    """ list and parse controllers """
    def _list(self):
        ret = self._conn.get(RAID_CTRL_URL)
        try:
            raid_ctrl = list()

            """ parse raid controller name """
            for member in ret['Members']:

                raid_ctrl_url = member['@odata.id']
                raid_ctrl.append(raid_ctrl_url.replace(IDRAC8_REDFISH_BASE_URL + RAID_CTRL_URL + '/', ''))

        except KeyError as e:
            raise "Invalid dict key from redfish response: " + e

        return raid_ctrl

    """ """
    def get_metrics(self):

        raids_ctrl = {}
        self.metrics['raid_controller'] = dict()
        self.metrics['disk'] = dict()

        """ list controllers """
        raid_ctrl = self._list()
        for ctrl in raid_ctrl:
            ret = self._get_disks(ctrl)
            self.metrics['raid_controller'][ctrl] = ret[0]
            self.metrics['disk'] = { **self.metrics['disk'], **ret[1] }

    def _get_disks(self, ctrl_name):

        """ get controllers info """
        ctrl_status = self._conn.get(RAID_CTRL_URL + '/' + ctrl_name)

        try:
            ctrl = ctrl_status['Status']
            if ctrl['Health'] and ctrl['State']:
                status[0]['value'] = ctrl['Health']
                status[1]['value'] = ctrl['State']

            disks = {}
            """ get disk list by controller """
            for disk in ctrl_status['Devices']:

                disk_name = disk['Name']
                disk_status = disk['Status']
                disks[disk_name] = {
                    'health': disk_status['Health'],
                    'state': disk_status['State']
                }
        except KeyError as e:
            raise "Invalid dict key from redfish response: " + e

        return [status, disks]

    """ transform metric value into valid prom metric value """
    def _cast(self, value):
        valid = ["OK", "Enabled"]
        invalid = ["", "KO", "Disabled"]

        if value in valid:
            return 1
        elif valid in invalid:
            return 0
        return value

    """ metrics must be on a specific format for prometheus """
    def parse_for_prom(self):
        label_names = ['name']
        metrics = list()
        for metric_name, v in self.metrics.items():
            """ add prefix define in collector call """
            i = InfoMetricFamily(self.prefix + '_' + metric_name, '', labels=label_names)

            for name, value in v.items():
                if type(value) is list:
                    print(name)
                    print(value)
                    for item in value:
                        m = GaugeMetricFamily(self.prefix + '_' + metric_name, '', labels=label_names)
                        m.add_metric([value[0]['type']], self._cast(value[0]['value']))
                        m.add_metric([value[1]['type']], self._cast(value[1]['value']))
                else:
                    i.add_metric([name], self._cast(value))

                metrics.append(m)
            metrics.append(i)

        metrics.append(i)

        return metrics
