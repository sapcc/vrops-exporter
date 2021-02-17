from abc import ABC, abstractmethod
import requests
import time
import os
import logging
from tools.helper import yaml_read
from tools.Vrops import Vrops
from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily, UnknownMetricFamily
from tools.http_status_codes import responses

logger = logging.getLogger('vrops-exporter')


class BaseCollector(ABC):

    def __init__(self):
        self.vrops_entity_name = 'base'
        while os.environ['TARGET'] not in self.get_target_tokens():
            logger.critical('Cannot start exporter without valid target!')
            logger.critical(f'{os.environ["TARGET"]} is not in vrops_list from inventory')
            logger.critical(f'The following vrops are known from inventory: {[t for t in self.target_tokens]}, retrying in 60s')
            time.sleep(60)
        self.target = os.environ.get('TARGET')
        self.collector = self.__class__.__name__

        # If metrics in collector-config are divided into rubrics
        self.rubricated = False
        self.rubric = os.environ.get('RUBRIC', None)

    @abstractmethod
    def collect(self):
        pass

    def read_collector_config(self):
        config_file = yaml_read(os.environ['CONFIG'])
        return config_file

    def get_vcenters(self, target):
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/vcenters/{}".format(current_iteration)
        request = requests.get(url)
        self.vcenters = request.json()
        return self.vcenters

    def get_datacenters(self, target):
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/datacenters/{}".format(current_iteration)
        request = requests.get(url)
        self.datacenters = request.json()
        return self.datacenters

    def get_clusters(self, target):
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/clusters/{}".format(current_iteration)
        request = requests.get(url)
        self.clusters = request.json()
        return self.clusters

    def get_hosts(self, target):
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/hosts/{}".format(current_iteration)
        request = requests.get(url)
        self.hosts = request.json()
        return self.hosts

    def get_datastores(self, target):
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/datastores/{}".format(current_iteration)
        request = requests.get(url)
        self.datastores = request.json()
        return self.datastores

    def get_vms(self, target):
        current_iteration = self.get_iteration()
        url = "http://" + os.environ['INVENTORY'] + "/" + target + "/vms/{}".format(current_iteration)
        request = requests.get(url)
        self.vms = request.json()
        return self.vms

    def get_iteration(self):
        request = requests.get(url="http://" + os.environ['INVENTORY'] + "/iteration")
        self.iteration = request.json()
        return self.iteration

    def get_collection_times(self):
        request = requests.get(url="http://" + os.environ['INVENTORY'] + "/collection_times")
        self.collection_times = request.json()
        return self.collection_times

    def get_inventory_api_responses(self):
        request = requests.get(url="http://" + os.environ['INVENTORY'] + "/api_response_codes")
        self.api_responses = request.json()
        return self.api_responses

    def get_target_tokens(self):
        try:
            request = requests.get(url="http://" + os.environ['INVENTORY'] + "/target_tokens")
            self.target_tokens = request.json()
            return self.target_tokens
        except requests.exceptions.ConnectionError as e:
            logger.critical(f'No connection to inventory: {os.environ["INVENTORY"]} - Error: {e}')
            return {}

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

    def get_project_ids_by_target(self):
        try:
            token = self.get_target_tokens()
            token = token[self.target]
            uuids = self.get_vms_by_target()
            project_ids = Vrops.get_project_ids(self.target, token, uuids, self.collector)
            return project_ids
        except requests.exceptions.ConnectionError as e:
            logger.critical(f'No connection to inventory: {os.environ["INVENTORY"]} - Error: {e}')
            return []

    def wait_for_inventory_data(self):
        iteration = 0
        while not iteration:
            time.sleep(5)
            iteration = self.get_iteration()
            logger.info(f'Waiting for initial iteration: {self.collector}')

        logger.info(f'-----Initial query done------: {self.collector}')
        return

    def create_http_response_metric(self, target, token, collector):
        api_responding = Vrops.get_http_response_code(target, token)
        gauge = GaugeMetricFamily('vrops_api_response', 'vrops-exporter', labels=['target', 'class', 'http_message'])
        gauge.add_metric(labels=[self.target, collector.lower(), responses()[api_responding][0]],
                         value=api_responding)

        if api_responding > 200:
            logger.critical(f'API response {api_responding} [{collector}, {self.target}], no return')
            return False, gauge
        return True, gauge

    def generate_gauges(self, metric_type, calling_class, vrops_entity_name, labelnames, rubric=None):
        if not isinstance(labelnames, list):
            logger.error(f'Cannot generate Gauges without label list, called from {calling_class}')
            return {}
        # switching between metric and property types
        if metric_type == 'stats':
            statkey_yaml = self.read_collector_config()['statkeys']
            rubrics = [r for r in statkey_yaml[calling_class]]
            gauges = dict()

            def iterate_over_metric_suffixes():
                statkey_suffix = statkey_pair['metric_suffix']
                gauges[statkey_suffix] = {
                    'gauge': GaugeMetricFamily('vrops_' + vrops_entity_name + '_' + statkey_suffix.lower(),
                                               'vrops-exporter', labels=labelnames),
                    'statkey': statkey_pair['statkey']
                }

            if self.rubricated and self.rubric:
                for statkey_pair in statkey_yaml[calling_class][rubric]:
                    iterate_over_metric_suffixes()
            if self.rubricated and not self.rubric:
                for r in rubrics:
                    for statkey_pair in statkey_yaml[calling_class][r]:
                        iterate_over_metric_suffixes()
            if not self.rubricated:
                for statkey_pair in statkey_yaml[calling_class]:
                    iterate_over_metric_suffixes()
            return gauges

        if metric_type == 'property':
            properties_yaml = self.read_collector_config()['properties']
            if 'number_metrics' in properties_yaml[calling_class]:
                gauges = dict()
                for property_pair in properties_yaml[calling_class]['number_metrics']:
                    property_suffix = property_pair['metric_suffix']
                    gauges[property_suffix] = {
                        'gauge': GaugeMetricFamily('vrops_' + vrops_entity_name + '_' + property_suffix.lower(),
                                                   'vrops-exporter', labels=labelnames),
                        'property': property_pair['property']
                    }
                return gauges

        logger.info(f'No gauge metric type generated, from {calling_class}')
        return {}

    def generate_infos(self, calling_class, vrops_entity_name, labelnames):
        if not isinstance(labelnames, list):
            logger.error(f'Cannot generate Gauges without label list, called from {calling_class}')
            return {}
        properties_yaml = self.read_collector_config()['properties']
        if 'info_metrics' in properties_yaml[calling_class]:
            infos = dict()
            for property_pair in properties_yaml[calling_class]['info_metrics']:
                property_suffix = property_pair['metric_suffix']
                infos[property_suffix] = {
                    'info': InfoMetricFamily('vrops_' + vrops_entity_name + '_' + property_suffix.lower(),
                                             'vrops-exporter', labels=labelnames),
                    'property': property_pair['property']
                }
            return infos

        logger.info(f'No info metric type generated, from {calling_class}')
        return {}

    def generate_states(self, calling_class, vrops_entity_name, labelnames):
        if not isinstance(labelnames, list):
            logger.error(f'Cannot generate Gauges without label list, called from {calling_class}')
            return {}
        properties_yaml = self.read_collector_config()['properties']
        if 'enum_metrics' in properties_yaml[calling_class]:
            states = dict()
            for property_pair in properties_yaml[calling_class]['enum_metrics']:
                property_suffix = property_pair['metric_suffix']
                states[property_suffix] = {
                    'state': UnknownMetricFamily('vrops_' + vrops_entity_name + '_' + property_suffix.lower(),
                                                 'vrops-exporter', labels=labelnames),
                    'property': property_pair['property'],
                    'expected': property_pair['expected']
                }
            return states

        logger.info(f'No enum metric type generated, from {calling_class}')
        return {}

    def describe(self):
        if 'Stats' in self.collector:
            statkey_yaml = self.read_collector_config()['statkeys']
            rubrics = [r for r in statkey_yaml[self.collector]]
            if self.rubricated and not self.rubric:
                logger.warning(f'{self.collector} is rubricated and has no rubric given. Considering all')
                logger.info(f'Rubrics to be considered: {rubrics}')
                for r in rubrics:
                    for statkey_pair in statkey_yaml[self.collector][r]:
                        statkey_suffix = statkey_pair.get('metric_suffix')
                        yield GaugeMetricFamily('vrops_' + self.vrops_entity_name + '_' + statkey_suffix.lower(),
                                                'vrops-exporter')
            if self.rubricated and self.rubric:
                logger.info(f'Rubric to be considered: {self.rubric}')
                for statkey_pair in statkey_yaml[self.collector][self.rubric]:
                    statkey_suffix = statkey_pair.get('metric_suffix')
                    yield GaugeMetricFamily('vrops_' + self.vrops_entity_name + '_' + statkey_suffix.lower(),
                                            'vrops-exporter')
            if not self.rubricated:
                for statkey_pair in statkey_yaml[self.collector]:
                    statkey_suffix = statkey_pair.get('metric_suffix')
                    yield GaugeMetricFamily('vrops_' + self.vrops_entity_name + '_' + statkey_suffix.lower(),
                                            'vrops-exporter')

        if 'Properties' in self.collector:
            properties_yaml = self.read_collector_config()['properties']
            if 'number_metrics' in properties_yaml[self.collector]:
                for num in properties_yaml[self.collector]['number_metrics']:
                    yield GaugeMetricFamily('vrops_' + self.vrops_entity_name + '_' + num['metric_suffix'].lower(),
                                            'vrops-exporter')
            if 'enum_metrics' in properties_yaml[self.collector]:
                for enum in properties_yaml[self.collector]['enum_metrics']:
                    yield UnknownMetricFamily('vrops_' + self.vrops_entity_name + '_' + enum['metric_suffix'].lower(),
                                              'vrops-exporter')
            if 'info_metrics' in properties_yaml[self.collector]:
                for info in properties_yaml[self.collector]['info_metrics']:
                    yield InfoMetricFamily('vrops_' + self.vrops_entity_name + '_' + info['metric_suffix'].lower(),
                                           'vrops-exporter')
