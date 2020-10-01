from abc import ABC, abstractmethod
import requests
import time
import os
from tools.helper import yaml_read
from tools.Vrops import Vrops
from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily, UnknownMetricFamily


class BaseCollector(ABC):

    def __init__(self):
        self.vrops_entity_name = 'base'
        if os.environ['TARGET'] in self.get_target_tokens():
            self.target = os.environ['TARGET']
        else:
            print(os.environ['TARGET'], "has no resources in inventory")

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

    def get_target_tokens(self):
        request = requests.get(url="http://" + os.environ['INVENTORY'] + "/target_tokens")
        self.target_tokens = request.json()
        return self.target_tokens

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
        token = self.get_target_tokens()
        token = token[self.target]
        uuids = self.get_vms_by_target()
        project_ids = Vrops.get_project_ids(self.target, token, uuids)
        return project_ids

    def wait_for_inventory_data(self):
        iteration = 0
        while not iteration:
            time.sleep(5)
            iteration = self.get_iteration()
            if os.environ['DEBUG'] >= '1':
                print("waiting for initial iteration: " + type(self).__name__)
        print("done: initial query " + type(self).__name__)
        return

    def generate_gauges(self, metric_type, calling_class, vrops_entity_name, labelnames):
        if not isinstance(labelnames, list):
            print("Can't generate Gauges without label list, called from", calling_class)
            return {}
        # switching between metric and property types
        if metric_type == 'stats':
            statkey_yaml = self.read_collector_config()['statkeys']
            gauges = dict()
            for statkey_pair in statkey_yaml[calling_class]:
                statkey_suffix = statkey_pair['metric_suffix']
                gauges[statkey_suffix] = {
                    'gauge': GaugeMetricFamily('vrops_' + vrops_entity_name + '_' + statkey_suffix.lower(),
                                               'vrops-exporter', labels=labelnames),
                    'statkey': statkey_pair['statkey']
                }
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

        if os.environ['DEBUG'] >= '1':
            print("No Gauge metric type generated, from", calling_class)
        return {}

    def generate_infos(self, calling_class, vrops_entity_name, labelnames):
        if not isinstance(labelnames, list):
            print("Can't generate Gauges without label list, called from", calling_class)
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

        if os.environ['DEBUG'] >= '1':
            print("No Info metric type generated, from", calling_class)
        return {}

    def generate_states(self, calling_class, vrops_entity_name, labelnames):
        if not isinstance(labelnames, list):
            print("Can't generate Gauges without label list, called from", calling_class)
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

        if os.environ['DEBUG'] >= '1':
            print("No Enum metric type generated, from", calling_class)
        return {}

    def describe(self):
        if 'Stats' in self.__class__.__name__:
            statkey_yaml = self.read_collector_config()['statkeys']
            for statkey_pair in statkey_yaml[self.__class__.__name__]:
                statkey_suffix = statkey_pair['metric_suffix']
                yield GaugeMetricFamily('vrops_' + self.vrops_entity_name + '_' + statkey_suffix.lower(),
                                        'vrops-exporter')
        if 'Properties' in self.__class__.__name__:
            properties_yaml = self.read_collector_config()['properties']
            if 'number_metrics' in properties_yaml[self.__class__.__name__]:
                for num in properties_yaml[self.__class__.__name__]['number_metrics']:
                    yield GaugeMetricFamily('vrops_' + self.vrops_entity_name + '_' + num['metric_suffix'].lower(),
                                            'vrops-exporter')
            if 'enum_metrics' in properties_yaml[self.__class__.__name__]:
                for enum in properties_yaml[self.__class__.__name__]['enum_metrics']:
                    yield UnknownMetricFamily('vrops_' + self.vrops_entity_name + '_' + enum['metric_suffix'].lower(),
                                              'vrops-exporter')
            if 'info_metrics' in properties_yaml[self.__class__.__name__]:
                for info in properties_yaml[self.__class__.__name__]['info_metrics']:
                    yield InfoMetricFamily('vrops_' + self.vrops_entity_name + '_' + info['metric_suffix'].lower(),
                                           'vrops-exporter')
