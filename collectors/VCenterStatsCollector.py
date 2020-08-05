from BaseCollector import BaseCollector
import os
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead
from threading import Thread


class VCenterStatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.metric_name = 'vcenter'
        self.wait_for_inventory_data()
        # self.post_registered_collector(self.__class__.__name__, self.g.name)

    # def describe(self):
        # statkey_yaml = self.read_collector_config()['statkeys']
        # for statkey_pair in statkey_yaml[self.__class__.__name__]:
            # statkey_label = statkey_pair['label']
            # TODO: check if restart is needed in case of new metrics
            # yield GaugeMetricFamily('vrops_vcenter_' + statkey_label,'testtext')

    def collect(self):
        gauges = self.generate_gauges('metric', self.__class__.__name__, self.metric_name)
        if not gauges:
            return

        if os.environ['DEBUG'] >= '1':
            print(self.__class__.__name__, 'starts with collecting the metrics')

        # make one big request per stat id with all resource id's in its belly
        thread_list = list()
        for vc in self.get_vcenters():
            target = self.vcenters[vc]['target']
            t = Thread(target=self.do_metrics, args=(target, gauges))
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
            print("skipping " + target + " in , no token")

        for vc in self.get_vcenters():
            uuid = self.vcenters[vc]['uuid']

            for label in gauges:
                statkey = gauges[label]['statkey']
                values = Resources.get_latest_stat(target, token, uuid, statkey)
                if not values:
                    print("skipping statkey " + str(statkey) + " in VCenterStatsCollector, no return")
                    continue
                metric_value = int(values)
                gauges[label]['gauge'].add_metric(labels=[self.vcenters[vc]['name']], value=metric_value)

