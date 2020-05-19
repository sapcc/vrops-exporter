from BaseCollector import BaseCollector
import os
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead
from threading import Thread


class VCenterStatsCollector(BaseCollector):
    def __init__(self):
        self.wait_for_inventory_data()
        self.statkey_yaml = YamlRead('collectors/statkey.yaml').run()
        # self.post_registered_collector(self.__class__.__name__, self.g.name)

    def describe(self):
        yield GaugeMetricFamily('vrops_vcenter_stats', 'testtext')

    def collect(self):
        g = GaugeMetricFamily('vrops_vcenter_stats', 'testtext', labels=['vcenter', 'statkey'])
        if os.environ['DEBUG'] >= '1':
            print('VCenterStatsCollector starts with collecting the metrics')

        # make one big request per stat id with all resource id's in its belly
        thread_list = list()
        for vc in self.get_vcenters():
            target = self.vcenters[vc]['target']
            t = Thread(target=self.do_metrics, args=(target, g))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        yield g

    def do_metrics(self, target, g):
        token = self.get_target_tokens()
        token = token[target]
        if not token:
            print("skipping " + target + " in , no token")

        for vc in self.get_vcenters():
            uuid = self.vcenters[vc]['uuid']
            target_vc = self.vcenters[vc]['name']

        for statkey_pair in self.statkey_yaml["VCenterStatsCollector"]:
            statkey_label = statkey_pair['label']
            statkey = statkey_pair['statkey']
            values = Resources.get_latest_stat(target, token, uuid, statkey)
            if not values:
                print("skipping statkey " + str(statkey) + " in VCenterStatsCollector, no return")
                continue

            try:
                metric_value = int(values)
                g.add_metric(labels=[target_vc, statkey_label], value=metric_value)

            except (ValueError, TypeError):
                info = values
                metric_value = 0
                g.add_metric(labels=[target_vc, statkey_label + ":" + info], value=metric_value)
