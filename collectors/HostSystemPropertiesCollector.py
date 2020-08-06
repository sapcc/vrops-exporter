from BaseCollector import BaseCollector
from tools.Resources import Resources
from threading import Thread
import os


class HostSystemPropertiesCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__
        self.vrops_entity_name = 'hostsystem'
        # self.post_registered_collector(self.name, self.g.name, self.i.name + '_info')

    def collect(self):
        gauges = self.generate_gauges('property', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'datacenter', 'vccluster'])
        infos = self.generate_infos(self.name, self.vrops_entity_name,
                                    [self.vrops_entity_name, 'datacenter', 'vccluster'])
        states = self.generate_states(self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'datacenter', 'vccluster', 'state'])

        if os.environ['DEBUG'] >= '1':
            print(self.name, 'starts with collecting the metrics')

        thread_list = list()
        for target in self.get_hosts_by_target():
            t = Thread(target=self.do_metrics, args=(target, gauges, infos, states))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        # self.post_metrics(self.g.name)
        # self.post_metrics(self.i.name + '_info')
        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']
        for metric_suffix in infos:
            yield infos[metric_suffix]['info']
        for metric_suffix in states:
            yield states[metric_suffix]['state']

    def do_metrics(self, target, gauges, infos, states):
        token = self.get_target_tokens()
        token = token[target]

        if not token:
            print("skipping", target, "in", self.name, ", no token")

        uuids = self.target_hosts[target]
        for metric_suffix in gauges:
            propkey = gauges[metric_suffix]['property']
            values = Resources.get_latest_number_properties_multiple(target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'data' not in value_entry:
                    continue
                metric_value = value_entry['data']
                host_id = value_entry['resourceId']
                gauges[metric_suffix]['gauge'].add_metric(
                    labels=[self.hosts[host_id]['name'],
                            self.hosts[host_id]['datacenter'].lower(),
                            self.hosts[host_id]['parent_cluster_name']],
                    value=metric_value)

        for metric_suffix in states:
            propkey = states[metric_suffix]['property']
            values = Resources.get_latest_enum_properties_multiple(target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'value' not in value_entry:
                    continue
                metric_value = (1 if states[metric_suffix]['expected'] == value_entry['value'] else 0)
                host_id = value_entry['resourceId']
                states[metric_suffix]['state'].add_metric(
                    labels=[self.hosts[host_id]['name'],
                            self.hosts[host_id]['datacenter'].lower(),
                            self.hosts[host_id]['parent_cluster_name'], value_entry['value']],
                    value=metric_value)

        for metric_suffix in infos:
            propkey = infos[metric_suffix]['property']
            values = Resources.get_latest_info_properties_multiple(target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'data' not in value_entry:
                    continue
                host_id = value_entry['resourceId']
                info_value = value_entry['data']
                infos[metric_suffix]['info'].add_metric(
                    labels=[self.hosts[host_id]['name'],
                            self.hosts[host_id]['datacenter'].lower(),
                            self.hosts[host_id]['parent_cluster_name']],
                    value={metric_suffix: info_value})