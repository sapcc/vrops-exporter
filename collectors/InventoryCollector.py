from BaseCollector import BaseCollector

from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
from tools.http_status_codes import responses
import logging

logger = logging.getLogger('vrops-exporter')


class InventoryCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.name = self.__class__.__name__
        self.wait_for_inventory_data()

    def collect(self):
        logger.info(f'{self.name} starts with collecting the metrics')

        for target, token in self.get_target_tokens().items():
            gauge = GaugeMetricFamily('vrops_inventory_resources_total', 'vrops_inventory',
                                      labels=["target", "resourcekind"])

            vcenters = len(self.get_vcenters(target))
            gauge.add_metric(labels=[target, "vcenter"], value=vcenters)

            datacenters = len(self.get_datacenters(self.target))
            gauge.add_metric(labels=[target, "datacenter"], value=datacenters)

            vccluster = len(self.get_clusters(self.target))
            gauge.add_metric(labels=[target, "vccluster"], value=vccluster)

            hosts = len(self.get_hosts(self.target))
            gauge.add_metric(labels=[target, "hosts"], value=hosts)

            datastores = len(self.get_datastores(self.target))
            gauge.add_metric(labels=[target, "datastores"], value=datastores)

            vms = len(self.get_vms(target))
            gauge.add_metric(labels=[target, "virtualmachines"], value=vms)

            yield gauge

            counter = CounterMetricFamily('vrops_inventory_iteration', 'vrops_inventory', labels=["target"])
            iteration = self.get_iteration()
            counter.add_metric(labels=[target], value=iteration)

            yield counter

            collection_time = self.get_collection_times()[target]
            time = GaugeMetricFamily('vrops_inventory_collection_time_seconds', 'vrops_inventory', labels=["target"])
            time.add_metric(labels=[target], value=collection_time)

            yield time

            status_code = self.get_inventory_api_response()
            api_response = GaugeMetricFamily('vrops_api_response', 'vrops-exporter',
                                             labels=['target', 'class', 'message'])
            api_response.add_metric(labels=[target, self.name.lower(), responses()[status_code][0]],
                                    value=status_code)
            yield api_response
