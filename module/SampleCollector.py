from BaseCollector import BaseCollector
import os
from prometheus_client.core import GaugeMetricFamily


class SampleCollector(BaseCollector):

    def __init__(self, resources, target, user, password):
        self._resources = resources
        self._target = target
        self._user = user
        self._password = password

    def collect(self):
        metric_list = list()

        if os.environ['DEBUG'] == '1':
            print('have some debug code in here')

        entityname = "vmentityname"

        g = GaugeMetricFamily('vrops_ressource_gauge', 'Gauge Collector for vRops',
                              labels=['target', 'entityname'])
        g.add_metric(labels=[self._target, entityname], value=1)

        metric_list.append(g)
        return metric_list
