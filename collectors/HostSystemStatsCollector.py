from BaseCollector import BaseCollector
from tools.Resources import Resources
from threading import Thread
import os


class HostSystemStatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'hostsystem'
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__
        # self.post_registered_collector(self.name, g.name)

    def collect(self):
        gauges = self.generate_gauges('stats', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'datacenter', 'vccluster'])
        if not gauges:
            return

        if os.environ['DEBUG'] >= '1':
            print(self.name, 'starts with collecting the metrics')

        thread_list = list()
        for target in self.get_hosts_by_target():
            t = Thread(target=self.do_metrics, args=(target, gauges))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']

    def do_metrics(self, target, gauges):
        token = self.get_target_tokens()
        token = token[target]
        if not token:
            print("skipping " + target + " in " + self.name + ", no token")
        uuids = self.target_hosts[target]

        for metric_suffix in gauges:
            statkey = gauges[metric_suffix]['statkey']
            values = Resources.get_latest_stat_multiple(target, token, uuids, statkey)
            if not values:
                print("skipping statkey " + str(statkey) + " in", self.name, ", no return")
                continue

            for value_entry in values:
                metric_value = value_entry['stat-list']['stat'][0]['data']
                if metric_value:
                    metric_value = metric_value[0]
                    host_id = value_entry['resourceId']
                    gauges[metric_suffix]['gauge'].add_metric(
                        labels=[self.hosts[host_id]['name'],
                                self.hosts[host_id]['datacenter'].lower(),
                                self.hosts[host_id]['parent_cluster_name']],
                        value=metric_value)
