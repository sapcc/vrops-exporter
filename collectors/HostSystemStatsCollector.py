from BaseCollector import BaseCollector
from tools.Resources import Resources
from threading import Thread
import os


class HostSystemStatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.metric_name = 'hostsystem'
        self.wait_for_inventory_data()
        # self.post_registered_collector(self.__class__.__name__, self.g.name)

    def collect(self):
        gauges = self.generate_gauges('metric', self.__class__.__name__, [self.metric_name,
                                      'datacenter', 'cluster', 'hostsystem'])
        if not gauges:
            return

        if os.environ['DEBUG'] >= '1':
            print(self.__class__.__name__, 'starts with collecting the metrics')

        thread_list = list()
        for target in self.get_hosts_by_target():
            t = Thread(target=self.do_metrics, args=(target, gauges,))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        for label in gauges:
            yield gauges[label]['gauge']

    def do_metrics(self, target, gauges):
        token = self.get_target_tokens()
        token = token[target]
        if not token:
            print("skipping ", target, "in", self.__class__.__name__, ", no token")

        uuids = self.target_hosts[target]
        for label in gauges:
            statkey = gauges[label]['statkey']
            values = Resources.get_latest_stat_multiple(target, token, uuids, statkey)
            if not values:
                print("skipping statkey " + str(statkey) + " in HostSystemStatsCollector, no return")
                continue
            for value_entry in values:
                # there is just one, because we are querying latest only
                metric_value = value_entry['stat-list']['stat'][0]['data'][0]
                host_id = value_entry['resourceId']
                gauges[label]['gauge'].add_metric(
                    labels=[self.hosts[host_id]['datacenter'].lower(), self.hosts[host_id]['parent_cluster_name'],
                            self.hosts[host_id]['name']], value=metric_value)
