from BaseCollector import BaseCollector
import os, time
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead


class HostSystemCollector(BaseCollector):
    def __init__(self):
        self.iteration = 0
        while not self.iteration:
            time.sleep(5)
            self.get_iteration()
            print("waiting for initial iteration")
        print("done: initial query")
        self.statkey_yaml = YamlRead('collectors/statkey.yaml').run()

    def collect(self):
        if os.environ['DEBUG'] == '1':
            print('HostSystemCollector ist start collecting metrics')

        g = GaugeMetricFamily('vrops_hostsystem', 'testtext', labels=['datacenter', 'cluster', 'hostsystem', 'statkey'])

        for hs in self.get_hosts():
            target = self.hosts[hs]['target']
            for statkey in self.statkey_yaml["HostSystemCollector"]:
                r = Resources()
                print("looking at " + str(self.hosts[hs]))
                value = r.get_latest_stat(target=target, token=self.hosts[hs]['token'], uuid=self.hosts[hs]['uuid'], key=statkey["statkey"])
                if value is None:
                    value = "0"
                if os.environ['DEBUG'] == '1':
                    print(self.hosts[hs]['name'], "--add statkey:", statkey["label"], str(value))
                g.add_metric(labels=[self.hosts[hs]['datacenter'], self.hosts[hs]['parent_cluster_name'],
                                     self.hosts[hs]['name'], statkey["label"]], value=value)
        yield g
