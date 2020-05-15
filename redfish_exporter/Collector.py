__version__ = '0.1'

from prometheus_client import Metric
from .Request import Req
from .system.Raid import Raid
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY, InfoMetricFamily

class Collector(object):
    def __init__(self, service, sys_version, conn, prefix):
        self._service = service
        self._sys_version = sys_version
        self._conn = conn
        self._labels = {}
        self.prefix = prefix
        self._set_labels()

    def _set_labels(self):
        self._labels.update({'service': self._service})

    """ Method called by generate_lastest() prometheud fct """
    def collect(self):
        custom_label_names = []
        custom_label_values = []

        raid = Raid(self._conn, self.prefix)
        raid_metrics = raid.parse_for_prom()

        """ push exporter version """
        m = GaugeMetricFamily(
            self.prefix + '_version',
            'Version of redfish_exporter running',
            labels=['version'] + custom_label_names)
        m.add_metric([__version__] + custom_label_values, __version__)
        yield m

        """ add raid emtrics """
        for item in raid_metrics:
            yield item
