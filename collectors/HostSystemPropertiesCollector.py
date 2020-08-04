from BaseCollector import BaseCollector
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.core import InfoMetricFamily
from tools.Resources import Resources
from tools.helper import yaml_read
from threading import Thread
import os


class HostSystemPropertiesCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.metric_name = 'hostsystem'
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__
        # self.post_registered_collector(self.name, self.g.name, self.i.name + '_info')

    def collect(self):
        gauges = self.generate_gauges('property', self.name, [self.metric_name, 'datacenter', 'vccluster'])
        infos = self.generate_infos(self.name, [self.metric_name, 'datacenter', 'vccluster'])
        states = self.generate_states(self.name, [self.metric_name, 'datacenter', 'vccluster'])

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
        for label in gauges:
            yield gauges[label]['gauge']
        for label in infos:
            yield infos[label]['info']
        for label in states:
            yield states[label]['state']

    def do_metrics(self, target, gauges, infos, states):
        token = self.get_target_tokens()
        token = token[target]

        if not token:
            print("skipping", target, "in", self.name, ", no token")

        uuids = self.target_hosts[target]
        for label in gauges:
            propkey = gauges[label]['property']
            values = Resources.get_latest_number_properties_multiple(target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'data' not in value_entry:
                    continue
                data = value_entry['data']
                host_id = value_entry['resourceId']
                gauges[label]['gauge'].add_metric(
                    labels=[self.hosts[host_id]['name'], self.hosts[host_id]['datacenter'].lower(),
                            self.hosts[host_id]['parent_cluster_name']],
                    value=data)

        for label in states:
            propkey = states[label]['property']
            values = Resources.get_latest_enum_properties_multiple(target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'value' not in value_entry:
                    continue
                data = {state: False for state in states[label]['states']}
                if value_entry['value'] in data:
                    data[value_entry['value']] = True
                print(data)
                host_id = value_entry['resourceId']
                states[label]['state'].add_metric(
                    labels=[self.hosts[host_id]['name'], self.hosts[host_id]['datacenter'].lower(),
                            self.hosts[host_id]['parent_cluster_name']],
                    value=data)

        for label in infos:
            propkey = infos[label]['property']
            values = Resources.get_latest_info_properties_multiple(target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'data' not in value_entry:
                    continue
                host_id = value_entry['resourceId']
                info_value = value_entry['data']
                infos[label]['info'].add_metric(
                    labels=[self.hosts[host_id]['name'], self.hosts[host_id]['datacenter'].lower(),
                            self.hosts[host_id]['parent_cluster_name']],
                    value={infos[label]['property']: info_value})
