from BaseCollector import BaseCollector

from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
import logging

logger = logging.getLogger('vrops-exporter')


class InventoryCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.name = self.__class__.__name__
        self.resourcekinds = ["vcenters", "datacenters", "clusters", "hosts", "datastores", "vms"]

    def describe(self):
        for resourcekind in self.resourcekinds:
            yield GaugeMetricFamily(f'vrops_inventory_{resourcekind}', f'Amount of {resourcekind} in inventory')
        yield CounterMetricFamily('vrops_inventory_iteration', 'vrops_inventory')
        yield GaugeMetricFamily('vrops_inventory_collection_time_seconds', 'vrops_inventory')
        yield GaugeMetricFamily('vrops_api_response', 'vrops-exporter')

    def collect(self):
        logger.info(f'{self.name} starts with collecting the metrics')

        for target, token in self.get_target_tokens().items():
            for resourcekind in self.resourcekinds:
                gauge = GaugeMetricFamily(f'vrops_inventory_{resourcekind}', f'Amount of {resourcekind} in inventory',
                                          labels=["target"])

                type_method = getattr(BaseCollector, f'get_{resourcekind}')
                amount = len(type_method(self, target))
                gauge.add_metric(labels=[target], value=amount)
                yield gauge

            counter = CounterMetricFamily('vrops_inventory_iteration', 'vrops_inventory', labels=["target"])
            iteration = self.get_iteration()
            counter.add_metric(labels=[target], value=iteration)

            yield counter

            collection_time = self.get_collection_times()[target]
            time = GaugeMetricFamily('vrops_inventory_collection_time_seconds', 'vrops_inventory', labels=["target"])
            time.add_metric(labels=[target], value=collection_time)

            yield time

            status_code = self.get_inventory_api_responses()[target]
            api_response = GaugeMetricFamily('vrops_api_response', 'vrops-exporter',
                                             labels=['target', 'class'])
            api_response.add_metric(labels=[target, self.name.lower()],
                                    value=status_code)
            yield api_response
