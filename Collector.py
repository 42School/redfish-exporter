import time
import random
from prometheus_client import Metric
from collectors.System import systemScrape


class Collector(object):
    def __init__(self, host, username, password, service):
        self._scrape_ip = host
        self._username = username
        self._password = password
        self._service = service
        self._labels = {}
        self._set_labels()

    def _set_labels(self):
        self._labels.update({'service': self._service})

    def _get_metrics(self):

        system = systemScrape(self._scrape_ip, self._username, self._password)
        system.get_processor()

        metrics = {
            'requests': 100,
            'requests_status_2xx': 90,
            'requests_status_4xx': 3,
            'requests_status_5xx': 7,
            'uptime_sec': 123,
            'exclude_me': 1234,
        }

        return metrics

    def collect(self):
        metrics = self._get_metrics()

        if metrics:
            for k, v in metrics.items():
                metric = Metric(k, k, 'counter')
                labels = {}
                labels.update(self._labels)
                metric.add_sample(k, value=v, labels=labels)

                if metric.samples:
                    yield metric
                else:
                    pass
