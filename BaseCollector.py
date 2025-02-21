from abc import ABC, abstractmethod
import requests
import time
import os
import re
import logging
from tools.helper import yaml_read
from tools.Vrops import Vrops
from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily

logger = logging.getLogger('vrops-exporter')


class BaseCollector(ABC):

    def __init__(self):
        self.vrops_entity_name = 'base'
        while os.environ['TARGET'] not in self.get_vrops_target():
            logger.critical(f'Cannot start exporter. Missing inventory pod for {os.environ["TARGET"]}, retry in 60s')
            time.sleep(60)
        self.target = os.environ.get('TARGET')
        self.vrops = Vrops()
        self.name = self.__class__.__name__
        self.label_names = []
        self.project_ids = []
        self.collect_running = False
        self.nested_value_metric_keys = []

    @abstractmethod
    def collect(self):
        pass

    def read_collector_config(self):
        config_file = yaml_read(os.environ['COLLECTOR_CONFIG'])
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

    def get_SDRS_cluster(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/storagepod/{}".format(current_iteration)
        request = requests.get(url)
        self.sdrs_clusters = request.json() if request else {}
        return self.sdrs_clusters

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

    def get_distributed_vswitches(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/dvs/{}".format(current_iteration)
        request = requests.get(url)
        self.dvs = request.json() if request else {}
        return self.dvs

    def get_nsxt_adapter(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/nsxt_adapter/{}".format(current_iteration)
        request = requests.get(url)
        self.nsxt_adapter = request.json() if request else {}
        return self.nsxt_adapter

    def get_nsxt_mgmt_cluster(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/nsxt_mgmt_cluster/{}".format(current_iteration)
        request = requests.get(url)
        self.nsxt_mgmt_cluster = request.json() if request else {}
        return self.nsxt_mgmt_cluster

    def get_nsxt_mgmt_nodes(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/nsxt_mgmt_nodes/{}".format(current_iteration)
        request = requests.get(url)
        self.nsxt_mgmt_nodes = request.json() if request else {}
        return self.nsxt_mgmt_nodes

    def get_nsxt_mgmt_service(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/nsxt_mgmt_service/{}".format(current_iteration)
        request = requests.get(url)
        self.nsxt_mgmt_service = request.json() if request else {}
        return self.nsxt_mgmt_service

    def get_nsxt_transport_nodes(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/nsxt_transport_nodes/{}".format(current_iteration)
        request = requests.get(url)
        self.nsxt_transport_nodes = request.json() if request else {}
        return self.nsxt_transport_nodes

    def get_nsxt_logical_switches(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/nsxt_logical_switches/{}".format(current_iteration)
        request = requests.get(url)
        self.nsxt_logical_switches = request.json() if request else {}
        return self.nsxt_logical_switches

    def get_vcops_objects(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/vcops_objects/{}".format(
            current_iteration)
        request = requests.get(url)
        self.vcops_objects = request.json() if request else {}
        return self.vcops_objects

    def get_sddc_objects(self, target):
        self.wait_for_inventory_data()
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/sddc_objects/{}".format(
            current_iteration)
        request = requests.get(url)
        self.sddc_objects = request.json() if request else {}
        return self.sddc_objects

    def get_alertdefinition(self, alert_id):
        request = requests.get(url="http://" + os.environ['INVENTORY'] + "/alertdefinitions/{}".format(alert_id))
        self.alertdefinition = request.json() if request else {}
        return self.alertdefinition

    def get_iteration(self):
        self.iteration = self.do_request(url="http://" + os.environ['INVENTORY'] + "/iteration")
        return self.iteration

    def get_amount_resources(self):
        self.wait_for_inventory_data()
        self.amount_resources = self.do_request(url="http://" + os.environ['INVENTORY'] + "/amount_resources")
        return self.amount_resources

    def get_collection_times(self):
        self.wait_for_inventory_data()
        self.collection_times = self.do_request(url="http://" + os.environ['INVENTORY'] + "/collection_times")
        return self.collection_times

    def get_inventory_api_responses(self):
        self.wait_for_inventory_data()
        self.api_responses = self.do_request(url="http://" + os.environ['INVENTORY'] + "/api_response_codes")
        self.api_reponse_times = self.do_request(url="http://" + os.environ['INVENTORY'] + "/api_response_times")
        return self.api_responses, self.api_reponse_times

    def get_service_states(self):
        self.wait_for_inventory_data()
        self.service_states = self.do_request(url="http://" + os.environ['INVENTORY'] + "/service_states")
        return self.service_states

    def get_target_tokens(self):
        self.target_tokens = self.do_request(url="http://" + os.environ['INVENTORY'] + "/target_tokens")
        return self.target_tokens

    def get_vrops_target(self):
        vrops_target = self.do_request(url="http://" + os.environ['INVENTORY'] + "/target")
        return vrops_target

    def do_request(self, url):
        try:
            request = requests.get(url, timeout=60)
            response = request.json() if request else {}
            return response
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            logger.critical(f'Connection error to inventory: {os.environ["INVENTORY"]} - Error: {e}')
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

    def get_SDRS_clusters_by_target(self):
        SDRS_clusters_dict = self.get_SDRS_cluster(self.target)
        self.target_SDRS_clusters = [SDRS_clusters_dict[uuid]['uuid'] for uuid in SDRS_clusters_dict]
        return self.target_SDRS_clusters

    def get_datastores_by_target(self):
        datastore_dict = self.get_datastores(self.target)
        self.target_datastores = [datastore_dict[uuid]['uuid'] for uuid in datastore_dict]
        return self.target_datastores

    def get_vms_by_target(self):
        vms_dict = self.get_vms(self.target)
        self.target_vms = [vms_dict[uuid]['uuid'] for uuid in vms_dict]
        return self.target_vms

    def get_dvs_by_target(self):
        dvs_dict = self.get_distributed_vswitches(self.target)
        self.target_dvs = [dvs_dict[uuid]['uuid'] for uuid in dvs_dict]
        return self.target_dvs

    def get_nsxt_adapter_by_target(self):
        nsxt_adapter_dict = self.get_nsxt_adapter(self.target)
        self.target_nsxt_adapter = [nsxt_adapter_dict[uuid]['uuid'] for uuid in nsxt_adapter_dict]
        return self.target_nsxt_adapter

    def get_nsxt_mgmt_cluster_by_target(self):
        nsxt_mgmt_cluster_dict = self.get_nsxt_mgmt_cluster(self.target)
        self.target_nsxt_mgmt_cluster = [nsxt_mgmt_cluster_dict[uuid]['uuid'] for uuid in nsxt_mgmt_cluster_dict]
        return self.target_nsxt_mgmt_cluster

    def get_nsxt_mgmt_nodes_by_target(self):
        nsxt_mgmt_nodes_dict = self.get_nsxt_mgmt_nodes(self.target)
        self.target_nsxt_mgmt_nodes = [nsxt_mgmt_nodes_dict[uuid]['uuid'] for uuid in nsxt_mgmt_nodes_dict]
        return self.target_nsxt_mgmt_nodes

    def get_nsxt_mgmt_service_by_target(self):
        nsxt_mgmt_service_dict = self.get_nsxt_mgmt_service(self.target)
        self.target_nsxt_mgmt_service = [nsxt_mgmt_service_dict[uuid]['uuid'] for uuid in nsxt_mgmt_service_dict]
        return self.target_nsxt_mgmt_service

    def get_nsxt_transport_nodes_by_target(self):
        nsxt_transport_nodes_dict = self.get_nsxt_transport_nodes(self.target)
        self.target_nsxt_transport_nodes = [nsxt_transport_nodes_dict[uuid]['uuid'] for uuid in
                                            nsxt_transport_nodes_dict]
        return self.target_nsxt_transport_nodes

    def get_nsxt_logical_switches_by_target(self):
        nsxt_logical_switches_dict = self.get_nsxt_logical_switches(self.target)
        self.target_nsxt_logical_switches = [nsxt_logical_switches_dict[uuid]['uuid'] for uuid in
                                             nsxt_logical_switches_dict]
        return self.target_nsxt_logical_switches

    def get_vcops_objects_by_target(self):
        vcops_objects_dict = self.get_vcops_objects(self.target)
        self.target_vcops_objects = [vcops_objects_dict[uuid]['uuid'] for uuid in
                                     vcops_objects_dict]
        return self.target_vcops_objects

    def get_sddc_objects_by_target(self):
        sddc_objects_dict = self.get_sddc_objects(self.target)
        self.target_sddc_objects = [sddc_objects_dict[uuid]['uuid'] for uuid in
                                    sddc_objects_dict]
        return self.target_sddc_objects

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

    def create_api_response_time_metric(self, collector: str, response_time: float) -> GaugeMetricFamily:
        gauge = GaugeMetricFamily('vrops_api_response_time_seconds', 'vrops-exporter',
                                  labels=['target', 'class'])
        gauge.add_metric(labels=[self.target, collector.lower()], value=response_time)
        return gauge

    def number_of_metric_samples_generated(self, collector: str, metric_name: str,
                                           number_of_metric_samples_generated: int) -> GaugeMetricFamily:
        gauge = GaugeMetricFamily('vrops_collector_metric_samples_generated_number', 'vrops-exporter',
                                  labels=['target', 'class', 'metric_name'])
        gauge.add_metric(labels=[self.target, collector.lower(), metric_name], value=number_of_metric_samples_generated)
        return gauge

    def number_of_metrics_to_collect(self, collector: str, number_of_metrics: int) -> GaugeMetricFamily:
        gauge = GaugeMetricFamily('vrops_collector_metrics_number', 'vrops-exporter',
                                  labels=['target', 'class'])
        gauge.add_metric(labels=[self.target, collector.lower()], value=number_of_metrics)
        return gauge

    def number_of_resources(self, collector: str, number_of_resources: int) -> GaugeMetricFamily:
        gauge = GaugeMetricFamily('vrops_collector_resources_number', 'vrops-exporter',
                                  labels=['target', 'class'])
        gauge.add_metric(labels=[self.target, collector.lower()], value=number_of_resources)
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

    def generate_alert_metrics(self, label_names: list) -> InfoMetricFamily:
        if 'alert_name' not in label_names:
            label_names.extend(['alert_name', 'alert_level', 'status', 'alert_impact'])
        alert_metric = InfoMetricFamily(f'vrops_{self.vrops_entity_name}_alert', 'vrops-exporter',
                                        labels=label_names)
        return alert_metric

    def add_metric_labels(self, metric_object: GaugeMetricFamily, labels):
        if labels[0] not in metric_object._labelnames:
            for label in labels:
                metric_object._labelnames += (label,)
        return

    def describe(self):
        collector_config = self.read_collector_config()
        for metric in collector_config[self.name]:
            metric_suffix = metric['metric_suffix']
            yield GaugeMetricFamily(f'vrops_{self.vrops_entity_name}_{metric_suffix.lower()}', 'vrops-exporter')
