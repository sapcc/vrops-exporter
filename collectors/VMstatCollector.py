from BaseCollector import BaseCollector
import os, time
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead


class VMstatCollector(BaseCollector):
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
            print('VMstatCollector starts with collecting the metrics')

        g = GaugeMetricFamily('vrops_vms_stats', 'testtext', labels=['virtualmachine', 'statkey'])

        #make one big request per stat id with all resource id's in its belly
        for target in self.get_vms_by_target():
            token = self.get_target_tokens()
            token = token[target]
            if not token:
                print("skipping " + target + " in VMstatCollector, no token")

            uuids = self.target_vms[target]
            for statkey_pair in self.statkey_yaml["VMstatCollector"]:
                statkey_label = statkey_pair['label']
                statkey = statkey_pair['statkey']
                values = Resources.get_latest_stat_multiple(target, token, uuids, statkey)
                if not values:
                    print("skipping statkey " + str(statkey) + " in VMstatCollector, no return")
                    continue
                for value_entry in values:
                    #there is just one, because we are querying latest only
                    metric_value = value_entry['stat-list']['stat'][0]['data'][0]
                    vm_id = value_entry['resourceId']
                    g.add_metric(labels=[self.vms[vm_id]['name'], statkey_label], value=metric_value)
        yield g

