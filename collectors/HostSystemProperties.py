from BaseCollector import BaseCollector
import os, time, json
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead


class HostSystemProperties(BaseCollector):
    def __init__(self):
        self.iteration = 0
        while not self.iteration:
            time.sleep(5)
            self.get_iteration()
            print("waiting for initial iteration")
        print("done: initial query")
        self.property_yaml = YamlRead('collectors/property.yaml').run()

    def collect(self):
        if os.environ['DEBUG'] >= '1':
            print('HostSystemProperties ist start collecting metrics')

        g = GaugeMetricFamily('vrops_hostsystem', 'properties',
                              labels=['datacenter', 'cluster', 'hostsystem', 'propkey'])

        # make one big request per stat id with all resource id's in its belly
        for target in self.get_hosts_by_target():
            token = self.get_target_tokens()
            token = token[target]

            if not token:
                print("skipping " + target + " in HostSystemProperties, no token")

            uuids = self.target_hosts[target]
            for property_pair in self.property_yaml["HostSystemProperties"]:
                property_label = property_pair['label']
                propkey = property_pair['property']
                values = Resources.get_latest_properties_multiple(target, token, uuids, propkey)
                if not values:
                    print("skipping propkey " + str(propkey) + " in HostSystemProperties, no return")
                    continue

                for value_entry in values:
                    if 'values' in value_entry['property-contents']['property-content'][0]:
                        property_value = value_entry['property-contents']['property-content'][0]['values'][0]
                    else:
                        property_value = value_entry['property-contents']['property-content'][0]['data'][0]
                    host_id = value_entry['resourceId']
                    g.add_metric(
                        labels=[self.hosts[host_id]['datacenter'], self.hosts[host_id]['parent_cluster_name'],
                                self.hosts[host_id]['name'], property_label],
                        value=property_value)
        yield g

    def get_hosts_by_target(self):
        self.target_hosts = dict()
        host_dict = self.get_hosts()
        for uuid in host_dict:
            host = host_dict[uuid]
            if host['target'] not in self.target_hosts.keys():
                self.target_hosts[host['target']] = list()
            self.target_hosts[host['target']].append(uuid)
        return self.target_hosts
