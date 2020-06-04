from prometheus_client import Metric
from .Request import Req
from .system.Raid import Raid
from .system.Chassis import Chassis
from prometheus_client.core import GaugeMetricFamily

__version__ = 1.2

class Collector(object):
    def __init__(self, service, idrac_version, conn, prefix, config):
        self._service = service
        self.idrac_version = idrac_version
        self._conn = conn
        self._labels = {}
        self.prefix = prefix
        self._set_labels()
        self._config = config

    def _set_labels(self):
        self._labels.update({'service': self._service})

    """ Method called by generate_lastest() prometheud fct """
    def collect(self):
        custom_label_names = []
        custom_label_values = []

        """ redfish exporter version """
        m = GaugeMetricFamily(
            self.prefix + '_version',
            'Version of redfish_exporter running',
            labels=[] + custom_label_names)
        m.add_metric([__version__] + custom_label_values, __version__)

        if self._service != 'test_connection':
            yield m
            """ get raids metrics """
            raid = Raid(self._conn, self.prefix, self._config, self.idrac_version)

            """ get raids metrics """
            chassis = Chassis(self._conn, self.prefix, self._config, self.idrac_version)
            
            """ add raid emtrics """
            yield from raid.parse_for_prom()
            
            """ add chassis emtrics """
            yield from chassis.parse_for_prom()
        else:
            yield m
