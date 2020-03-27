from BaseCollector import BaseCollector
import os
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead


class VMStatsCollector(BaseCollector):
    def __init__(self):
        self.wait_for_inventory_data()
        self.statkey_yaml = YamlRead('collectors/statkey.yaml').run()
        self.g = GaugeMetricFamily('vrops_vms_stats', 'testtext', labels=['vccluster', 'datacenter', 'virtualmachine', 'hostsystem', 'statkey'])
        self.post_registered_collector(self.__class__.__name__, self.g.name)

    def describe(self):
        yield self.g

    def collect(self):
        if os.environ['DEBUG'] >= '1':
            print('VMStatsCollector starts with collecting the metrics')

       # #make one big request per stat id with all resource id's in its belly
        for target in self.get_vms_by_target():
            token = self.get_target_tokens()
            token = token[target]
            if not token:
                print("skipping " + target + " in VMStatsCollector, no token")

            uuids = self.target_vms[target]
            for statkey_pair in self.statkey_yaml["VMStatsCollector"]:
                statkey_label = statkey_pair['label']
                statkey = statkey_pair['statkey']
                values = Resources.get_latest_stat_multiple(target, token, uuids, statkey)
                if not values:
                    print("skipping statkey " + str(statkey) + " in VMStatsCollector, no return")
                    continue
                for value_entry in values:
                    #there is just one, because we are querying latest only
                    metric_value = value_entry['stat-list']['stat'][0]['data'][0]
                    vm_id = value_entry['resourceId']
                    self.g.add_metric(labels=[self.vms[vm_id]['cluster'], self.vms[vm_id]['datacenter'],
                                self.vms[vm_id]['name'], self.vms[vm_id]['parent_host_name'], statkey_label], value=metric_value)
        self.post_metrics(self.g.name)
        yield self.g
