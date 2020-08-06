from BaseCollector import BaseCollector
import os
from tools.Resources import Resources
from threading import Thread


class VCenterStatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'vcenter'
        self.name = self.__class__.__name__
        self.wait_for_inventory_data()
        # self.post_registered_collector(self.__class__.__name__, self.g.name)

    def collect(self):
        gauges = self.generate_gauges('metric', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name])
        if not gauges:
            return

        if os.environ['DEBUG'] >= '1':
            print(self.name, 'starts with collecting the metrics')

        # make one big request per stat id with all resource id's in its belly
        thread_list = list()
        for vc in self.get_vcenters():
            target = self.vcenters[vc]['target']
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
            print("skipping " + target + " in", self.name, ", no token")

        for vc in self.get_vcenters():
            uuid = self.vcenters[vc]['uuid']

            for metric_suffix in gauges:
                statkey = gauges[metric_suffix]['statkey']
                values = Resources.get_latest_stat(target, token, uuid, statkey)
                if not values:
                    print("skipping statkey " + str(statkey) + " in", self.name, ", no return")
                    continue
                metric_value = float(values)
                gauges[metric_suffix]['gauge'].add_metric(labels=[self.vcenters[vc]['name']],
                                                          value=metric_value)

