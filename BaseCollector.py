from abc import ABC, abstractmethod
import requests
import time
import os
import re
import logging
from tools.helper import yaml_read
from tools.Vrops import Vrops
from prometheus_client.core import GaugeMetricFamily

logger = logging.getLogger('vrops-exporter')


class BaseCollector(ABC):

    def __init__(self):
        self.vrops_entity_name = 'base'
        while os.environ['TARGET'] not in self.get_target_tokens():
            logger.critical('Cannot start exporter without valid target!')
            logger.critical(f'{os.environ["TARGET"]} is not in vrops_list from inventory')
            logger.critical(
                f'The following vrops are known from inventory: {[t for t in self.target_tokens]}, retrying in 60s')
            time.sleep(60)
        self.target = os.environ.get('TARGET')
        self.vrops = Vrops()
        self.name = self.__class__.__name__
        self.label_names = []
        self.project_ids = []

    @abstractmethod
    def collect(self):
        pass

    def read_collector_config(self):
        config_file = yaml_read(os.environ['CONFIG'])
        return config_file

    def get_vcenters(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/vcenters/{}".format(current_iteration)
        request = requests.get(url)
        self.vcenters = request.json() if request else {}
        return self.vcenters

    def get_datacenters(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/datacenters/{}".format(current_iteration)
        request = requests.get(url)
        self.datacenters = request.json() if request else {}
        return self.datacenters

    def get_clusters(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/clusters/{}".format(current_iteration)
        request = requests.get(url)
        self.clusters = request.json() if request else {}
        return self.clusters

    def get_hosts(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/hosts/{}".format(current_iteration)
        request = requests.get(url)
        self.hosts = request.json() if request else {}
        return self.hosts

    def get_datastores(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/datastores/{}".format(current_iteration)
        request = requests.get(url)
        self.datastores = request.json() if request else {}
        return self.datastores

    def get_vms(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/vms/{}".format(current_iteration)
        request = requests.get(url)
        self.vms = request.json() if request else {}
        return self.vms

    def get_nsxt_mgmt_cluster(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/nsxt_mgmt_cluster/{}".format(current_iteration)
        request = requests.get(url)
        self.nsxt_mgmt_cluster = request.json() if request else {}
        return self.nsxt_mgmt_cluster

    def get_iteration(self):
        request = requests.get(url="http://" + os.environ['INVENTORY'] + "/iteration")
        self.iteration = request.json() if request else {}
        return self.iteration

    def get_collection_times(self):
        self.wait_for_inventory_data()
        request = requests.get(url="http://" + os.environ['INVENTORY'] + "/collection_times")
        self.collection_times = request.json() if request else {}
        return self.collection_times

    def get_inventory_api_responses(self):
        self.wait_for_inventory_data()
        request = requests.get(url="http://" + os.environ['INVENTORY'] + "/api_response_codes")
        self.api_responses = request.json() if request else {}
        return self.api_responses

    def get_target_tokens(self):
        try:
            request = requests.get(url="http://" + os.environ['INVENTORY'] + "/target_tokens")
            self.target_tokens = request.json() if request else {}
            return self.target_tokens
        except requests.exceptions.ConnectionError as e:
            logger.critical(f'No connection to inventory: {os.environ["INVENTORY"]} - Error: {e}')
            return {}

    def get_vcenters_by_target(self):
        vcenter_dict = self.get_vcenters(self.target)
        self.target_vcenters = [vcenter_dict[uuid]['uuid'] for uuid in vcenter_dict]
        return self.target_vcenters

    def get_clusters_by_target(self):
        cluster_dict = self.get_clusters(self.target)
        self.target_clusters = [cluster_dict[uuid]['uuid'] for uuid in cluster_dict]
        return self.target_clusters

    def get_hosts_by_target(self):
        host_dict = self.get_hosts(self.target)
        self.target_hosts = [host_dict[uuid]['uuid'] for uuid in host_dict]
        return self.target_hosts

    def get_datastores_by_target(self):
        datastore_dict = self.get_datastores(self.target)
        self.target_datastores = [datastore_dict[uuid]['uuid'] for uuid in datastore_dict]
        return self.target_datastores

    def get_vms_by_target(self):
        vms_dict = self.get_vms(self.target)
        self.target_vms = [vms_dict[uuid]['uuid'] for uuid in vms_dict]
        return self.target_vms

    def get_nsxt_mgmt_cluster_by_target(self):
        nsxt_resources_dict = self.get_nsxt_mgmt_cluster(self.target)
        self.target_nsxt_mgmt_cluster = [nsxt_resources_dict[uuid]['uuid'] for uuid in nsxt_resources_dict]
        return self.target_nsxt_mgmt_cluster

    def get_project_ids_by_target(self):
        try:
            token = self.get_target_tokens()
            token = token[self.target]
            uuids = self.get_vms_by_target()
            project_ids = Vrops.get_project_ids(self.target, token, uuids, self.name)
            return project_ids
        except requests.exceptions.ConnectionError as e:
            logger.critical(f'No connection to inventory: {os.environ["INVENTORY"]} - Error: {e}')
            return []

    def wait_for_inventory_data(self):
        iteration = self.get_iteration()
        while not iteration:
            time.sleep(5)
            iteration = self.get_iteration()
            logger.debug(f'Waiting for initial iteration: {self.name}')
        return

    def create_api_response_code_metric(self, collector: str, api_responding: int) -> GaugeMetricFamily:
        gauge = GaugeMetricFamily('vrops_api_response', 'vrops-exporter', labels=['target', 'class'])
        gauge.add_metric(labels=[self.target, collector.lower()], value=api_responding)

        if api_responding > 200:
            logger.critical(f'API response {api_responding} [{collector}, {self.target}], no return')
            return gauge
        return gauge

    def create_api_response_time_metric(self, collector: str, response_time: float) -> GaugeMetricFamily:
        gauge = GaugeMetricFamily('vrops_api_response_time_seconds', 'vrops-exporter',
                                  labels=['target', 'class'])
        gauge.add_metric(labels=[self.target, collector.lower()], value=response_time)
        return gauge

    def generate_metrics(self, label_names: list) -> dict:
        collector_config = self.read_collector_config()
        metrics = {m['key']: {'metric_suffix': m['metric_suffix'],
                              'key': m['key'],
                              'expected': m.setdefault('expected', None),
                              'gauge': GaugeMetricFamily(f'vrops_{self.vrops_entity_name}_{m["metric_suffix"].lower()}',
                                                         'vrops-exporter', labels=label_names)
                              } for m in collector_config.get(self.name, {})}
        if not metrics:
            logger.error(f'Cannot find {self.name} in collector_config')
        return metrics

    def generate_metrics_enriched_by_api(self, no_match_in_config: list, label_names: list) -> dict:
        gauges = dict()
        for statkey in no_match_in_config:
            new_metric_suffix = re.sub("[^0-9a-zA-Z]+", "_", statkey[0])
            value = statkey[1]
            labels = statkey[2]
            if new_metric_suffix not in gauges:
                gauges[new_metric_suffix] = GaugeMetricFamily(
                    f'vrops_{self.vrops_entity_name}_{new_metric_suffix.lower()}', 'vrops-exporter', labels=label_names)
            gauges[new_metric_suffix].add_metric(labels=labels, value=value)
        return gauges

    def describe(self):
        collector_config = self.read_collector_config()
        for metric in collector_config[self.name]:
            metric_suffix = metric['metric_suffix']
            yield GaugeMetricFamily(f'vrops_{self.vrops_entity_name}_{metric_suffix.lower()}', 'vrops-exporter')
