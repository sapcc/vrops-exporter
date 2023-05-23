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

        for metric in (self.amount_inventory_resources(self.target) +
                       self.api_response_metric(self.target) +
                       self.vrops_node_service_states(self.target)):
            yield metric
        yield self.iteration_metric(self.target)
        yield self.collection_time_metric(self.target)
        yield self.inventory_targets_info(self.target)

    def amount_inventory_resources(self, target):
        gauges = list()
        for resourcekind, amount in self.get_amount_resources().get(target, {"empty": 0}).items():
            if resourcekind == "empty":
                logger.warning(
                    f'InventoryBuilder could not capture resources for {target}')
            gauge = GaugeMetricFamily(f'vrops_inventory_{resourcekind}', f'Amount of {resourcekind} in inventory',
                                      labels=["target"])
            gauge.add_metric(labels=[target], value=amount)
            gauges.append(gauge)
        return gauges

    def iteration_metric(self, target):
        iteration_gauge = CounterMetricFamily(
            'vrops_inventory_iteration', 'vrops_inventory', labels=["target"])
        iteration = self.get_iteration()
        if not iteration:
            return iteration_gauge
        iteration_gauge.add_metric(labels=[target], value=iteration)
        return iteration_gauge

    def api_response_metric(self, target):
        api_response_gauge = GaugeMetricFamily('vrops_api_response',
                                               'vrops_inventory',
                                               labels=["target",
                                                       "class",
                                                       "get_request"])
        api_response_time_gauge = GaugeMetricFamily('vrops_api_response_time_seconds',
                                                    'vrops_inventory',
                                                    labels=["target",
                                                            "class",
                                                            "get_request"])

        status_code_dict, time_dict = self.get_inventory_api_responses()
        if not status_code_dict[target]:
            return api_response_gauge
        if not time_dict[target]:
            return api_response_time_gauge
        for get_request, status_code in status_code_dict[target].items():
            api_response_gauge.add_metric(labels=[target, self.name.lower(), get_request],
                                          value=status_code)
        for get_request, response_time in time_dict[target].items():
            api_response_time_gauge.add_metric(labels=[target, self.name.lower(), get_request],
                                               value=response_time)
        return [api_response_gauge, api_response_time_gauge]

    def collection_time_metric(self, target):
        collection_time_gauge = GaugeMetricFamily('vrops_inventory_collection_time_seconds', 'vrops_inventory',
                                                  labels=["target"])
        collection_time = self.get_collection_times()[target]
        if not collection_time:
            return collection_time_gauge
        collection_time_gauge.add_metric(
            labels=[target], value=collection_time)
        return collection_time_gauge

    def inventory_targets_info(self, target):
        inventory_target_info = GaugeMetricFamily('vrops_inventory_target', 'vrops_inventory',
                                                  labels=["target"])
        inventory_target_info.add_metric(labels=[target], value=1)
        return inventory_target_info

    def vrops_node_service_states(self, target):
        vrops_node_service_health = GaugeMetricFamily('vrops_node_service_health',
                                                      'vrops_inventory',
                                                      labels=["target",
                                                              "name",
                                                              "health",
                                                              "details"])
        vrops_node_service_uptime = GaugeMetricFamily('vrops_node_service_uptime',
                                                      'vrops_inventory',
                                                      labels=["target",
                                                              "name"])
        vrops_node_service_start_time = GaugeMetricFamily('vrops_node_service_start_time',
                                                          'vrops_inventory',
                                                          labels=["target",
                                                                  "name"])
        service_states = self.get_service_states().get("service")
        if not service_states:
            return [vrops_node_service_health, vrops_node_service_uptime, vrops_node_service_start_time]

        for service in service_states:
            vrops_node_service_health.add_metric(labels=[target,
                                                         service.get("name", "N/A").lower(),
                                                         service.get("health", "N/A").lower(),
                                                         service.get("details", "N/A").lower()],
                                                 value=1 if service.get("health").lower() == "ok" else 0)
            vrops_node_service_uptime.add_metric(labels=[target,
                                                         service.get("name", "N/A").lower()],
                                                 value=service.get("uptime", 0))
            vrops_node_service_start_time.add_metric(labels=[target,
                                                             service.get("name", "N/A").lower()],
                                                     value=service.get("startedOn", 0))
        return [vrops_node_service_health, vrops_node_service_uptime, vrops_node_service_start_time]
