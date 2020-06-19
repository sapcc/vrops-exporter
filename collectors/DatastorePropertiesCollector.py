from BaseCollector import BaseCollector
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.core import InfoMetricFamily
from tools.Resources import Resources
from tools.helper import yaml_read
from threading import Thread
import os


class DatastorePropertiesCollector(BaseCollector):
    def __init__(self):
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__

    def describe(self):
        yield GaugeMetricFamily('vrops_datastore_properties', 'testtest')
        yield InfoMetricFamily('vrops_datastore', 'testtest')

    def collect(self):
        g = GaugeMetricFamily('vrops_datastore_properties', 'testtext',
                              labels=['datacenter', 'vccluster', 'hostsystem', 'datastore', 'propkey'])
        i = InfoMetricFamily('vrops_datastore', 'testtest',
                             labels=['datacenter', 'vccluster', 'hostsystem', 'datastore'])
        if os.environ['DEBUG'] >= '1':
            print(self.__class__.__name__ + " starts with collecting the metrics")

        thread_list = list()
        for target in self.get_datastores_by_target():
            t = Thread(target=self.do_metrics, args=(target, g, i))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        yield g

    def do_metrics(self, target, g, i):
        token = self.get_target_tokens()
        token = token[target]
        if not token:
            print("skipping " + target + " in " + self.__class__.__name__ + " , no token")

        uuids = self.target_datastores[target]
        property_yaml = self.read_collector_config()['properties']
        if 'number_metrics' in property_yaml[self.name]:
            for property_pair in property_yaml[self.name]['number_metrics']:
                property_label = property_pair['label']
                propkey = property_pair['property']
                values = Resources.get_latest_number_properties_multiple(target, token, uuids, propkey)
                if not values:
                    continue
                for value_entry in values:
                    if 'data' not in value_entry:
                        print("skipping propkey" + str(propkey) + " in " + self.__class__.__name__ + " , no return")
                        continue
                    data = value_entry['data']
                    datastore_id = value_entry['resourceId']
                    g.add_metric(labels=[self.datastores[datastore_id]['datacenter'].lower(),
                                 self.datastores[datastore_id]['cluster'],
                                 self.datastores[datastore_id]['parent_host_name'],
                                 self.datastores[datastore_id]['name'],
                                 property_label], value=data)

        if 'enum_metrics' in property_yaml[self.name]:
            for property_pair in property_yaml[self.name]['enum_metrics']:
                property_label = property_pair['label']
                propkey = property_pair['property']
                expected_state = property_pair['expected']
                values = Resources.get_latest_enum_properties_multiple(target, token, uuids, propkey, expected_state)
                if not values:
                    continue
                for value_entry in values:
                    if 'data' not in value_entry:
                        print("skipping propkey" + str(propkey) + " in " + self.__class__.__name__ + " , no return")
                        continue
                    data = value_entry['data']
                    datastore_id = value_entry['resourceId']
                    latest_state = value_entry['latest_state']
                    g.add_metric(labels=[self.datastores[datastore_id]['datacenter'].lower(),
                                 self.datastores[datastore_id]['cluster'],
                                 self.datastores[datastore_id]['parent_host_name'],
                                 self.datastores[datastore_id]['name'],
                                 property_label + ": " + latest_state],
                                 value=data)

        if 'info_metrics' in property_yaml[self.name]:
            for property_pair in property_yaml[self.name]['info_metrics']:
                property_label = property_pair['label']
                propkey = property_pair['property']
                values = Resources.get_latest_info_properties_multiple(target, token, uuids, propkey)
                if not values:
                    continue
                for value_entry in values:
                    if 'data' not in value_entry:
                        print("skipping propkey" + str(propkey) + " in " + self.__class__.__name__ + " , no return")
                        continue
                    datastore_id = value_entry['resourceId']
                    info_value = value_entry['data']
                    i.add_metric(labels=[self.datastores[datastore_id]['datacenter'].lower(),
                                 self.datastores[datastore_id]['cluster'],
                                 self.datastores[datastore_id]['parent_host_name'],
                                 self.datastores[datastore_id]['name']],
                                 value={property_label: info_value})

