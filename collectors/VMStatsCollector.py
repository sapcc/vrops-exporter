from BaseCollector import BaseCollector
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.helper import yaml_read
from threading import Thread
import os
import json


class VMStatsCollector(BaseCollector):
    def __init__(self):
        self.wait_for_inventory_data()
        self.statkey_yaml = yaml_read('collectors/statkey.yaml')
        # self.post_registered_collector(self.__class__.__name__, g.name)

    def describe(self):
        yield GaugeMetricFamily('vrops_vm_stats', 'testtext')

    def collect(self):
        g = GaugeMetricFamily('vrops_vm_stats', 'testtext',
                              labels=['vccluster', 'datacenter', 'virtualmachine', 'hostsystem', 'statkey'])
        if os.environ['DEBUG'] >= '1':
            print('VMStatsCollector starts with collecting the metrics')

        thread_list = list()
        for target in self.get_vms_by_target():
            t = Thread(target=self.do_metrics, args=(target, g))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        yield g

    def do_metrics(self, target, g):
        token = self.get_target_tokens()
        token = token[target]
        if not token:
            print("skipping " + target + " in VMStatsCollector, no token")

        uuids = self.target_vms[target]
        print(target)
        print("amount uuids",str(len(uuids)))
        with open('uuids','w') as f:
            json.dump(uuids,f)
        for statkey_pair in self.statkey_yaml["VMStatsCollector"]:
            statkey_label = statkey_pair['label']
            statkey = statkey_pair['statkey']
            values = Resources.get_latest_stat_multiple(target, token, uuids, statkey)
            print("fetched     ", str(len(values)))
            # with open('values_4vms','w') as f:
                # json.dump(values,f)
            if not values:
                print("skipping statkey " + str(statkey) + " in VMStatsCollector, no return")
                continue
            for value_entry in values:
                if 'resourceId' not in value_entry:
                    continue
                # there is just one, because we are querying latest only
                metric_value = value_entry['stat-list']['stat'][0]['data']
                if not metric_value:
                    continue
                vm_id = value_entry['resourceId']
                if vm_id not in self.vms:
                    continue
                g.add_metric(labels=[self.vms[vm_id]['cluster'], self.vms[vm_id]['datacenter'],
                             self.vms[vm_id]['name'], self.vms[vm_id]['parent_host_name'], statkey_label],
                             value=metric_value[0])
