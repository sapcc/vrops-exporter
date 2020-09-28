from BaseCollector import BaseCollector
import os
from tools.vrops import Vrops



class VCenterStatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'vcenter'
        self.name = self.__class__.__name__
        self.wait_for_inventory_data()

    def collect(self):
        gauges = self.generate_gauges('stats', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name])

        if os.environ['DEBUG'] >= '1':
            print(self.name, 'starts with collecting the metrics')

        token = self.get_target_tokens()
        token = token[self.target]
        if not token:
            print("skipping " + self.target + " in", self.name, ", no token")

        vc = self.get_vcenters(self.target)
        uuid = [vc[uuid]['uuid'] for uuid in vc][0]
        for metric_suffix in gauges:
            statkey = gauges[metric_suffix]['statkey']
            values = Vrops.get_latest_stat(self.target, token, uuid, statkey)
            if not values:
                print("skipping statkey " + str(statkey) + " in", self.name, ", no return")
                continue
            metric_value = float(values)
            gauges[metric_suffix]['gauge'].add_metric(labels=[self.vcenters[uuid]['name']],
                                                      value=metric_value)

        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']

