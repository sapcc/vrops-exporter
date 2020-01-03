from BaseCollector import BaseCollector
from prometheus_client.core import GaugeMetricFamily
from random import randint


class HostSystemCollector(BaseCollector):

    def __init__(self, resources, target, user, password):
        self._resources = resources
        self._target = target
        self._user = user
        self._password = password

    def collect(self):

        metric_list = []

        g = GaugeMetricFamily('vrops_resource_gauge', 'HostSystemCollector',
                              labels=['target', 'name', 'uuid'])

        for cluster in self._resources.datacenter[0].cluster:
            for host in cluster.hosts:
                g.add_metric(labels=[self._target, host.name, host.uuid], value=randint(1, 632))

        metric_list.append(g)

        return metric_list
