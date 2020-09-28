from BaseCollector import BaseCollector
from tools.vrops import Vrops
import os


class ClusterStatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'cluster'
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__

    def collect(self):
        gauges = self.generate_gauges('stats', self.name, self.vrops_entity_name,
                                      ['vcenter', 'vccluster', 'datacenter'])
        if not gauges:
            return

        if os.environ['DEBUG'] >= '1':
            print(self.name, 'starts with collecting the metrics')

        token = self.get_target_tokens()
        token = token[self.target]
        if not token:
            print("skipping " + self.target + " in " + self.name + ", no token")

        uuids = self.get_clusters_by_target()
        for metric_suffix in gauges:
            statkey = gauges[metric_suffix]['statkey']
            values = Vrops.get_latest_stat_multiple(self.target, token, uuids, statkey)
            if not values:
                print("skipping statkey " + str(statkey) + " in", self.name, ", no return")
                continue

            for value_entry in values:
                metric_value = value_entry['stat-list']['stat'][0]['data']
                if metric_value:
                    metric_value = metric_value[0]
                    cluster_id = value_entry['resourceId']
                    gauges[metric_suffix]['gauge'].add_metric(
                            labels=[self.clusters[cluster_id]['vcenter'],
                                    self.clusters[cluster_id]['name'],
                                    self.clusters[cluster_id]['parent_dc_name'].lower()],
                            value=metric_value)

        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']
