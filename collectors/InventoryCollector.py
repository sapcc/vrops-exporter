from BaseCollector import BaseCollector

from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
import logging

logger = logging.getLogger('vrops-exporter')


class InventoryCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.name = self.__class__.__name__

    def describe(self):
        for resourcekind in self.get_amount_resources()[self.target]:
            yield GaugeMetricFamily(f'vrops_inventory_{resourcekind}', f'Amount of {resourcekind} in inventory')
        yield CounterMetricFamily('vrops_inventory_iteration', 'vrops_inventory')
        yield GaugeMetricFamily('vrops_inventory_collection_time_seconds', 'vrops_inventory')
        yield GaugeMetricFamily('vrops_api_response', 'vrops-exporter')

    def collect(self):
        logger.info(f'{self.name} starts with collecting the metrics')

        target_tokens = self.get_target_tokens()
        if not target_tokens:
            return

        for target, token in self.target_tokens.items():
            for gauge_metric in self.amount_inventory_resources(target):
                yield gauge_metric
            yield self.iteration_metric(target)
            yield self.api_response_metric(target)
            yield self.collection_time_metric(target)

    def amount_inventory_resources(self, target):
        gauges = list()
        for resourcekind, amount in self.get_amount_resources()[target].items():
            gauge = GaugeMetricFamily(f'vrops_inventory_{resourcekind}', f'Amount of {resourcekind} in inventory',
                                      labels=["target"])
            gauge.add_metric(labels=[target], value=amount)
            gauges.append(gauge)
        return gauges

    def iteration_metric(self, target):
        iteration_gauge = CounterMetricFamily('vrops_inventory_iteration', 'vrops_inventory', labels=["target"])
        iteration = self.get_iteration()
        if not iteration:
            return iteration_gauge
        iteration_gauge.add_metric(labels=[target], value=iteration)
        return iteration_gauge

    def api_response_metric(self, target):
        api_response_gauge = GaugeMetricFamily('vrops_api_response', 'vrops-exporter',
                                               labels=['target', 'class', 'get_request'])
        status_code_dict = self.get_inventory_api_responses()[target]
        if not status_code_dict:
            return api_response_gauge
        for get_request, status_code in status_code_dict.items():
            api_response_gauge.add_metric(labels=[target, self.name.lower(), get_request],
                                          value=status_code)
        return api_response_gauge

    def collection_time_metric(self, target):
        collection_time_gauge = GaugeMetricFamily('vrops_inventory_collection_time_seconds', 'vrops_inventory',
                                                  labels=["target"])
        collection_time = self.get_collection_times()[target]
        if not collection_time:
            return collection_time_gauge
        collection_time_gauge.add_metric(labels=[target], value=collection_time)
        return collection_time_gauge
