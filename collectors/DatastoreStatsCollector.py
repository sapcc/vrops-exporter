from BaseCollector import BaseCollector
import os, time
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead


class DatastoreStatsCollector(BaseCollector):
    def __init__(self):
        self.iteration = 0
        while not self.iteration:
            time.sleep(5)
            self.get_iteration()
            print("waiting for initial iteration")
        print("done: initial query")
        self.statkey_yaml = YamlRead('collectors/statkey.yaml').run()

    def collect(self):

        if len(self.get_datastores()) >= 1:
            print('DatastoreStatsCollector starts with collecting the metrics')
        else:
            print("There are no Datastores in the inventory")
            return False

        g = GaugeMetricFamily('vrops_datastore_stats', 'testtext', labels=['datacenter', 'cluster', 'hostsystem',
                                                                            'datastore', 'statkey'])

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
                    g.add_metric(labels=[self.datastores[datastore_id]['datacenter'],
                                         self.datastores[datastore_id]['cluster'],
                                         self.datastores[datastore_id]['parent_host_name'],
                                         self.datastores[datastore_id]['name'],
                                         statkey_label], value=metric_value)
        yield g
