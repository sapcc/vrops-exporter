from BaseCollector import BaseCollector
import os, time
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead


class DatastoreStatsCollector(BaseCollector):
    def __init__(self):
        self.wait_for_inventory_data()
        self.statkey_yaml = YamlRead('collectors/statkey.yaml').run()
        self.g = GaugeMetricFamily('vrops_datastore_stats', 'testtext', labels=['datacenter', 'vccluster', 'hostsystem', 'datastore', 'statkey'])
        self.post_registered_collector(self.__class__.__name__, self.g.name)

    def describe(self):
        yield self.g

    def collect(self):
        if os.environ['DEBUG'] >= '1':
            print(self.__class__.__name__ + " starts with collecting the metrics")

        #make one big request per stat id with all resource id's in its belly
        for target in self.get_datastores_by_target():
            token = self.get_target_tokens()
            token = token[target]
            if not token:
                print("skipping " + target + " in " + self.__class__.__name__ + " , no token")

            uuids = self.target_datastores[target]
            for statkey_pair in self.statkey_yaml[self.__class__.__name__]:
                statkey_label = statkey_pair['label']
                statkey = statkey_pair['statkey']
                values = Resources.get_latest_stat_multiple(target, token, uuids, statkey)
                if not values:
                    print("skipping statkey " + str(statkey) + " in " + self.__class__.__name__ + " , no return")
                    continue
                for value_entry in values:
                    #there is just one, because we are querying latest only
                    metric_value = value_entry['stat-list']['stat'][0]['data'][0]
                    datastore_id = value_entry['resourceId']
                    self.g.add_metric(labels=[self.datastores[datastore_id]['datacenter'],
                                         self.datastores[datastore_id]['cluster'],
                                         self.datastores[datastore_id]['parent_host_name'],
                                         self.datastores[datastore_id]['name'],
                                         statkey_label], value=metric_value)
        self.post_metrics(self.g.name)
        yield self.g
