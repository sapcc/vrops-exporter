from BaseCollector import BaseCollector

from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
import logging

logger = logging.getLogger('vrops-exporter')


class InventoryCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.name = self.__class__.__name__
        self.wait_for_inventory_data()

    def collect(self):
        logger.info(f'{self.name} starts with collecting the metrics')

        gauge = GaugeMetricFamily('vrops_inventory_resources_total', 'vrops_inventory',
                                  labels=["target", "resourcekind"])

        vcenters = len(self.get_vcenters(self.target))
        gauge.add_metric(labels=[self.target, "vcenter"], value=vcenters)

        datacenters = len(self.get_datacenters(self.target))
        gauge.add_metric(labels=[self.target, "datacenter"], value=datacenters)

        vccluster = len(self.get_clusters(self.target))
        gauge.add_metric(labels=[self.target, "vccluster"], value=vccluster)

        hosts = len(self.get_hosts(self.target))
        gauge.add_metric(labels=[self.target, "hosts"], value=hosts)

        datastores = len(self.get_datastores(self.target))
        gauge.add_metric(labels=[self.target, "datastores"], value=datastores)

        vms = len(self.get_vms(self.target))
        gauge.add_metric(labels=[self.target, "virtualmachines"], value=vms)

        yield gauge

        counter = CounterMetricFamily('vrops_inventory_iteration', 'vrops_inventory', labels=["target"])
        iteration = self.get_iteration()
        counter.add_metric(labels=[self.target], value=iteration)

        yield counter

        collection_time = self.get_collection_times()[self.target]
        time = GaugeMetricFamily('vrops_inventory_collection_time_seconds', 'vrops_inventory', labels=["target"])
        time.add_metric(labels=[self.target], value=collection_time)

        yield time
