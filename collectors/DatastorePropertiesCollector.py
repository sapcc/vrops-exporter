from BaseCollector import BaseCollector
from tools.Vrops import Vrops
import os


class DatastorePropertiesCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__
        self.vrops_entity_name = 'datastore'

    def collect(self):
        gauges = self.generate_gauges('property', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'type', 'vcenter', 'datacenter', 'vccluster',
                                       'hostsystem'])
        infos = self.generate_infos(self.name, self.vrops_entity_name,
                                    [self.vrops_entity_name, 'type', 'vcenter', 'datacenter', 'vccluster',
                                     'hostsystem'])
        states = self.generate_states(self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'type', 'vcenter', 'datacenter', 'vccluster',
                                       'hostsystem', 'state'])

        if os.environ['DEBUG'] >= '1':
            print(self.name, 'starts with collecting the metrics')

        token = self.get_target_tokens()
        token = token[self.target]

        if not token:
            print("skipping", self.target, "in", self.name, ", no token")

        uuids = self.get_datastores_by_target()
        for label in gauges:
            propkey = gauges[label]['property']
            values = Vrops.get_latest_number_properties_multiple(self.target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'data' not in value_entry:
                    continue
                metric_value = value_entry['data']
                datastore_id = value_entry['resourceId']
                gauges[label]['gauge'].add_metric(
                    labels=[self.datastores[datastore_id]['name'],
                            self.datastores[datastore_id]['type'],
                            self.datastores[datastore_id]['vcenter'],
                            self.datastores[datastore_id]['datacenter'].lower(),
                            self.datastores[datastore_id]['cluster'],
                            self.datastores[datastore_id]['parent_host_name']],
                    value=metric_value)

        for label in states:
            propkey = states[label]['property']
            values = Vrops.get_latest_enum_properties_multiple(self.target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'value' not in value_entry:
                    continue
                metric_value = (1 if states[label]['expected'] == value_entry['value'] else 0)
                datastore_id = value_entry['resourceId']
                states[label]['state'].add_metric(
                    labels=[self.datastores[datastore_id]['name'],
                            self.datastores[datastore_id]['type'],
                            self.datastores[datastore_id]['vcenter'],
                            self.datastores[datastore_id]['datacenter'].lower(),
                            self.datastores[datastore_id]['cluster'],
                            self.datastores[datastore_id]['parent_host_name'],
                            value_entry['value']],
                    value=metric_value)

        for label in infos:
            propkey = infos[label]['property']
            values = Vrops.get_latest_info_properties_multiple(self.target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'data' not in value_entry:
                    continue
                datastore_id = value_entry['resourceId']
                info_value = value_entry['data']
                infos[label]['info'].add_metric(
                    labels=[self.datastores[datastore_id]['name'],
                            self.datastores[datastore_id]['type'],
                            self.datastores[datastore_id]['vcenter'],
                            self.datastores[datastore_id]['datacenter'].lower(),
                            self.datastores[datastore_id]['cluster'],
                            self.datastores[datastore_id]['parent_host_name']],
                    value={label: info_value})

        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']
        for metric_suffix in infos:
            yield infos[metric_suffix]['info']
        for metric_suffix in states:
            yield states[metric_suffix]['state']
