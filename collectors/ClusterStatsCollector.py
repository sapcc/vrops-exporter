from BaseCollector import BaseCollector
import os, time, json
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead
from threading import Thread


class ClusterStatsCollector(BaseCollector):
    def __init__(self):
        self.wait_for_inventory_data()
        self.statkey_yaml = YamlRead('collectors/statkey.yaml').run()
        self.name = self.__class__.__name__
        # self.post_registered_collector(self.name, g.name)

    def describe(self):
        yield GaugeMetricFamily('vrops_cluster_stats', 'testtest')

    def collect(self):
        g = GaugeMetricFamily('vrops_cluster_stats', 'testtest',
                              labels=['datacenter', 'vccluster', 'statkey'])
        if os.environ['DEBUG'] >= '1':
            print('ClusterStatsCollector starts with collecting the metrics')

        thread_list = list()
        for target in self.get_clusters_by_target():
            t = Thread(target=self.do_metrics, args=(target,g))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        yield g

    def do_metrics(self, target, g):
        token = self.get_target_tokens()
        token = token[target]

        if not token:
            print("skipping " + target + " in " + self.name + ", no token")

        uuids = self.target_clusters[target]
        for statkey_pair in self.statkey_yaml["ClusterStatsCollector"]:
            statkey_label = statkey_pair['label']
            statkey = statkey_pair['statkey']
            values = Resources.get_latest_stat_multiple(target, token, uuids, statkey)
            if not values:
                print("skipping statkey " + str(statkey) + " in ClusterStatsCollector, no return")
                continue
            for value_entry in values:
                #data = value_entry['data']
                metric_value = value_entry['stat-list']['stat'][0]['data'][0]
                cluster_id = value_entry['resourceId']
                g.add_metric(
                        labels=[self.clusters[cluster_id]['parent_dc_name'], self.clusters[cluster_id]['name'],
                                 statkey_label],
                        value=metric_value)
