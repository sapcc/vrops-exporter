from BaseCollector import BaseCollector
import os, time, json
from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead


class HostSystemPropertiesCollector(BaseCollector):
    def __init__(self):
        self.wait_for_inventory_data()
        self.property_yaml = YamlRead('collectors/property.yaml').run()
        self.name = self.__class__.__name__
        # self.post_registered_collector(self.name, self.g.name, self.i.name + '_info')

    def describe(self):
        yield GaugeMetricFamily('vrops_hostsystem_properties', 'testtest')
        yield InfoMetricFamily("vrops_hostsystem", 'testtest')

    def collect(self):
        g = GaugeMetricFamily('vrops_hostsystem_properties', 'testtest',
                                   labels=['datacenter', 'vccluster', 'hostsystem', 'propkey'])
        i = InfoMetricFamily("vrops_hostsystem", 'testtest',
                                  labels=['datacenter', 'vccluster', 'hostsystem'])
        if os.environ['DEBUG'] >= '1':
            print(self.name, 'starts with collecting the metrics')

        for target in self.get_hosts_by_target():
            token = self.get_target_tokens()
            token = token[target]

            if not token:
                print("skipping", target, "in", self.name, ", no token")

            uuids = self.target_hosts[target]
            if 'number_metrics' in self.property_yaml[self.name]:
                for property_pair in self.property_yaml[self.name]['number_metrics']:
                    property_label = property_pair['label']
                    propkey = property_pair['property']
                    values = Resources.get_latest_number_properties_multiple(target, token, uuids, propkey)
                    if not values:
                        continue
                    for value_entry in values:
                        data = value_entry['data']
                        host_id = value_entry['resourceId']
                        g.add_metric(
                            labels=[self.hosts[host_id]['datacenter'], self.hosts[host_id]['parent_cluster_name'],
                                    self.hosts[host_id]['name'], property_label],
                            value=data)

            if 'enum_metrics' in self.property_yaml[self.name]:
                for property_pair in self.property_yaml[self.name]['enum_metrics']:
                    property_label = property_pair['label']
                    propkey = property_pair['property']
                    expected_state = property_pair['expected']
                    values = Resources.get_latest_enum_properties_multiple(target, token, uuids, propkey, expected_state)
                    if not values:
                        continue
                    for value_entry in values:
                        data = value_entry['data']
                        host_id = value_entry['resourceId']
                        latest_state = value_entry['latest_state']
                        g.add_metric(
                            labels=[self.hosts[host_id]['datacenter'], self.hosts[host_id]['parent_cluster_name'],
                                    self.hosts[host_id]['name'], property_label + ": " + latest_state],
                            value=data)

            if 'info_metrics' in self.property_yaml[self.name]:
                for property_pair in self.property_yaml[self.name]['info_metrics']:
                    property_label = property_pair['label']
                    propkey = property_pair['property']
                    values = Resources.get_latest_info_properties_multiple(target, token, uuids, propkey)
                    if not values:
                        continue
                    for value_entry in values:
                        host_id = value_entry['resourceId']
                        info_value = value_entry['data']
                        i.add_metric(
                            labels=[self.hosts[host_id]['datacenter'], self.hosts[host_id]['parent_cluster_name'],
                                    self.hosts[host_id]['name']],
                            value={property_label: info_value})

        # self.post_metrics(self.g.name)
        # self.post_metrics(self.i.name + '_info')
        yield g
        yield i


