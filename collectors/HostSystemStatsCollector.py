from BaseCollector import BaseCollector
import os, time
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead


class HostSystemStatsCollector(BaseCollector):
    def __init__(self):
        self.iteration = 0
        while not self.iteration:
            time.sleep(5)
            self.get_iteration()
            print("waiting for initial iteration")
        print("done: initial query")
        self.statkey_yaml = YamlRead('collectors/statkey.yaml').run()

    def collect(self):
        if os.environ['DEBUG'] >= '1':
            print('HostSystemStatsCollector ist start collecting metrics')

        g = GaugeMetricFamily('vrops_hostsystem_stats', 'testtext', labels=['datacenter', 'cluster', 'hostsystem', 'statkey'])

        #make one big request per stat id with all resource id's in its belly
        for target in self.get_hosts_by_target():
            token = self.get_target_tokens()
            token = token[target]
            if not token:
                print("skipping " + target + " in HostSystemStatsCollector, no token")

            uuids = self.target_hosts[target]
            for statkey_pair in self.statkey_yaml["HostSystemStatsCollector"]:
                statkey_label = statkey_pair['label']
                statkey = statkey_pair['statkey']
                values = Resources.get_latest_stat_multiple(target, token, uuids, statkey)
                if not values:
                    print("skipping statkey " + str(statkey) + " in HostSystemStatsCollector, no return")
                    continue
                for value_entry in values:
                    #there is just one, because we are querying latest only
                    metric_value = value_entry['stat-list']['stat'][0]['data'][0]
                    host_id = value_entry['resourceId']
                    g.add_metric(labels=[self.hosts[host_id]['datacenter'], self.hosts[host_id]['parent_cluster_name'],
                                     self.hosts[host_id]['name'], statkey_label], value=metric_value)
        yield g
