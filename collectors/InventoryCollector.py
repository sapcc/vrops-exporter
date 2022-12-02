from BaseCollector import BaseCollector

from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
import logging

logger = logging.getLogger('vrops-exporter')


class InventoryCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.name = self.__class__.__name__

    def describe(self):
        for resourcekind in self.get_amount_resources().get(self.target, "empty"):
            yield GaugeMetricFamily(f'vrops_inventory_{resourcekind}', f'Amount of {resourcekind} in inventory')
        yield CounterMetricFamily('vrops_inventory_iteration', 'vrops_inventory')
        yield GaugeMetricFamily('vrops_inventory_collection_time_seconds', 'vrops_inventory')
        yield GaugeMetricFamily('vrops_api_response', 'vrops_inventory')
        yield GaugeMetricFamily('vrops_inventory_target', 'vrops_inventory')

    def collect(self):
        logger.info(f'{self.name} starts with collecting the metrics')

        for gauge_metric in self.amount_inventory_resources(self.target):
            yield gauge_metric
        yield self.iteration_metric(self.target)
        yield self.api_response_metric(self.target)
        yield self.collection_time_metric(self.target)
        yield self.inventory_targets_info(self.target)

        # If Atlas is used for target discovery
        yield self.atlas_http_sd_endpoint_probe()

    def amount_inventory_resources(self, target):
        gauges = list()
        for resourcekind, amount in self.get_amount_resources().get(target, {"empty": 0}).items():
            if resourcekind == "empty":
                logger.warning(f'InventoryBuilder could not capture resources for {target}')
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
        api_response_gauge = GaugeMetricFamily('vrops_api_response', 'vrops_inventory',
                                               labels=['target', 'class', 'get_request'])
        status_code_dict = self.get_inventory_api_responses()[target]
        if not status_code_dict:
            return api_response_gauge
        for get_request, status_code in status_code_dict.items():
            api_response_gauge.add_metric(labels=[target, self.name.lower(), get_request],
                                          value=status_code)
        return api_response_gauge

    def atlas_http_sd_endpoint_probe(self):
        atlas_response_gauge = GaugeMetricFamily('atlas_sd_response', 'vrops_inventory',
                                                 labels=['atlas_path'])
        if atlas_endpoint_response := self.get_inventory_api_responses().get('atlas'):
            for atlas_path, response_code in atlas_endpoint_response.items():
                atlas_response_gauge.add_metric(labels=[atlas_path], value=response_code)
        return atlas_response_gauge

    def collection_time_metric(self, target):
        collection_time_gauge = GaugeMetricFamily('vrops_inventory_collection_time_seconds', 'vrops_inventory',
                                                  labels=["target"])
        collection_time = self.get_collection_times()[target]
        if not collection_time:
            return collection_time_gauge
        collection_time_gauge.add_metric(labels=[target], value=collection_time)
        return collection_time_gauge

    def inventory_targets_info(self, target):
        inventory_target_info = GaugeMetricFamily('vrops_inventory_target', 'vrops_inventory',
                                                  labels=["target"])
        inventory_target_info.add_metric(labels=[target], value=1)
        return inventory_target_info
