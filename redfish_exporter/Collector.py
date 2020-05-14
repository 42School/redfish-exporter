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
        self._prefix = prefix
        self._set_labels()

    def _set_labels(self):
        self._labels.update({'service': self._service})

    """ regroup all metrics to be display """
    def _get_metrics(self):
        raid = Raid(self._conn)
        return raid.get_raid_metrics()

    """ Method called by generate_lastest() prometheud fct """
    def collect(self):
        metrics = self._get_metrics()
        custom_label_names = []
        custom_label_values = []

        """ push exporter version """
        m = GaugeMetricFamily(
            self._prefix + '_version',
            'Version of redfish_exporter running',
            labels=['version'] + custom_label_names)
        m.add_metric([__version__] + custom_label_values, 1.0)
        yield m

        label_names = ['name'] + custom_label_names
        for metric_name, v in metrics.items():
            """ add prefix define in collector call """
            m = InfoMetricFamily(self._prefix + '_' + metric_name, '', labels=label_names)

            for name, value in v.items():
                m.add_metric([name] + custom_label_values, value)
            yield m
