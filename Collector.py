import time
import random
from prometheus_client import Metric
#from collectors.System import systemScrape
from Request import Req

REDFISH_BASE_URL = "/redfish/v1"
RAID_CTRL_URL = REDFISH_BASE_URL + "/Systems/System.Embedded.1/Storage/Controllers"

class Collector(object):
    def __init__(self, host, service, username=None, password=None, verify=True):
        self._scrape_ip = host
        self._username = username
        self._password = password
        self._service = service
        self._labels = {}
        self._set_labels()
        self._verify = verify

    def _set_labels(self):
        self._labels.update({'service': self._service})

    """ regroup all metrics to be display  """
    def _get_metrics(self):

        #system = systemScrape()
        req = Req("https", self._scrape_ip, self._username, self._password, self._verify)

        response = req.get(RAID_CTRL_URL)

        raids_ctrl = {}
        metrics = {}
        metrics["raid_controller"] = ()
        for member in response["Members"]:

            raid_ctrl_url = member["@odata.id"]
            raid_ctrl_name = raid_ctrl_url.replace(RAID_CTRL_URL + "/", "")

            #raids_ctrl[raid_ctrl_name] = [] # disk
            metrics["raid_controller"].push(raid_ctrl_name)

        final_metrics = {}
        print(metrics)
        """ merge dicts """
        for group in metrics:
            print(group)
            #final_metrics = dict(group.items() + final_metrics.item())

        print(final_metrics)
        return metrics

    """ Method called by generate_lastest() prometheud fct """
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
