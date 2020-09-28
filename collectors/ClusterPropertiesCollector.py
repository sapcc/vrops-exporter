from BaseCollector import BaseCollector
from tools.vrops import Vrops
import os


class ClusterPropertiesCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__
        self.vrops_entity_name = 'cluster'

    def collect(self):
        gauges = self.generate_gauges('property', self.name, self.vrops_entity_name,
                                      ['vcenter', 'vccluster', 'datacenter'])
        infos = self.generate_infos(self.name, self.vrops_entity_name,
                                    [self.vrops_entity_name, 'vcenter', 'datacenter'])
        states = self.generate_states(self.name, self.vrops_entity_name,
                                      ['vcenter', 'vccluster', 'datacenter', 'state'])

        if os.environ['DEBUG'] >= '1':
            print(self.name, 'starts with collecting the metrics')

        token = self.get_target_tokens()
        token = token[self.target]

        if not token:
            print("skipping", self.target, "in", self.name, ", no token")

        uuids = self.get_clusters_by_target()
        for metric_suffix in gauges:
            propkey = gauges[metric_suffix]['property']
            values = Vrops.get_latest_number_properties_multiple(self.target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'data' not in value_entry:
                    continue
                metric_value = value_entry['data']
                cluster_id = value_entry['resourceId']
                gauges[metric_suffix]['gauge'].add_metric(
                    labels=[self.clusters[cluster_id]['vcenter'],
                            self.clusters[cluster_id]['name'],
                            self.clusters[cluster_id]['parent_dc_name'].lower()],
                    value=metric_value)

        for metric_suffix in states:
            propkey = states[metric_suffix]['property']
            values = Vrops.get_latest_enum_properties_multiple(self.target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'value' not in value_entry:
                    continue
                metric_value = (1 if states[metric_suffix]['expected'] == value_entry['value'] else 0)
                cluster_id = value_entry['resourceId']
                states[metric_suffix]['state'].add_metric(
                    labels=[self.clusters[cluster_id]['vcenter'],
                            self.clusters[cluster_id]['name'],
                            self.clusters[cluster_id]['parent_dc_name'].lower(),
                            value_entry['value']],
                    value=metric_value)

        for metric_suffix in infos:
            propkey = infos[metric_suffix]['property']
            values = Vrops.get_latest_info_properties_multiple(self.target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'data' not in value_entry:
                    continue
                cluster_id = value_entry['resourceId']
                info_value = value_entry['data']
                infos[metric_suffix]['info'].add_metric(
                    labels=[self.clusters[cluster_id]['vcenter'],
                            self.clusters[cluster_id]['name'],
                            self.clusters[cluster_id]['parent_dc_name'].lower()],
                    value={metric_suffix: info_value})

        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']
        for metric_suffix in infos:
            yield infos[metric_suffix]['info']
        for metric_suffix in states:
            yield states[metric_suffix]['state']
