from BaseCollector import BaseCollector
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.core import InfoMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead
from threading import Thread
import os


class ClusterPropertiesCollector(BaseCollector):
    def __init__(self):
        self.wait_for_inventory_data()
        self.property_yaml = YamlRead('collectors/property.yaml').run()
        self.name = self.__class__.__name__
        # self.post_registered_collector(self.name, self.g.name, self.i.name + '_info')

    def describe(self):
        yield GaugeMetricFamily('vrops_cluster_properties', 'testtest')
        yield InfoMetricFamily('vrops_cluster', 'testtest')

    def collect(self):
        g = GaugeMetricFamily('vrops_cluster_properties', 'testtest',
                              labels=['datacenter', 'vccluster', 'propkey'])
        i = InfoMetricFamily('vrops_cluster', 'testtest',
                             labels=['datacenter', 'vccluster'])
        if os.environ['DEBUG'] >= '1':
            print('ClusterPropertiesCollector starts with collecting the metrics')

        thread_list = list()
        for target in self.get_clusters_by_target():
            t = Thread(target=self.do_metrics, args=(target, g, i))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        yield g
        yield i

    def do_metrics(self, target, g, i):
        token = self.get_target_tokens()
        token = token[target]

        if not token:
            print("skipping " + target + " in " + self.name + ", no token")

        uuids = self.target_clusters[target]
        if 'number_metrics' in self.property_yaml[self.name]:
            for property_pair in self.property_yaml[self.name]['number_metrics']:
                property_label = property_pair['label']
                propkey = property_pair['property']
                values = Resources.get_latest_number_properties_multiple(target, token, uuids, propkey)
                if not values:
                    continue
                for value_entry in values:
                    if 'data' not in value_entry:
                        continue
                    data = value_entry['data']
                    cluster_id = value_entry['resourceId']
                    g.add_metric(
                        labels=[self.clusters[cluster_id]['parent_dc_name'], self.clusters[cluster_id]['name'],
                                property_label],
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
                    if 'data' not in value_entry:
                        continue
                    data = value_entry['data']
                    cluster_id = value_entry['resourceId']
                    latest_state = value_entry['latest_state']
                    g.add_metric(
                        labels=[self.clusters[cluster_id]['parent_dc_name'], self.clusters[cluster_id]['name'],
                                property_label + ": " + latest_state],
                        value=data)

        if 'info_metrics' in self.property_yaml[self.name]:
            for property_pair in self.property_yaml[self.name]['info_metrics']:
                property_label = property_pair['label']
                propkey = property_pair['property']
                values = Resources.get_latest_info_properties_multiple(target, token, uuids, propkey)
                if not values:
                    continue
                for value_entry in values:
                    if 'data' not in value_entry:
                        continue
                    cluster_id = value_entry['resourceId']
                    info_value = value_entry['data']
                    i.add_metric(
                        labels=[self.clusters[cluster_id]['parent_dc_name'], self.clusters[cluster_id]['name']],
                        value={property_label: info_value})
