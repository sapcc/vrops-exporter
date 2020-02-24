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
        self.token = self.get_token()
        self.target = self.get_target()
        self.statkeys = list()
        statkey_yaml = YamlRead('collectors/statkey.yaml').run()
        for metric in statkey_yaml["HostSystemCollector"]:
            stat = dict()
            stat['label'] = metric["label"]
            stat['statkey'] = metric["statkey"]
            self.statkeys.append(stat)

    def collect(self):
        if os.environ['DEBUG'] == '1':
            print('HostSystemCollector ist start collecting metrics')
            print("Target: " + str(self.target))
            print("Token: " + str(self.token))

        g = GaugeMetricFamily('vrops_hostsystem', str(self.target), labels=['datacenter', 'cluster',
                                                                            'hostsystem', 'statkey'])
        for hs in self.get_hosts():
            for statkey in self.statkeys:
                r = Resources()
                value = r.get_latest_stat(self, target=self.target, token=self.token, uuid=self.hosts[hs]['uuid'],
                                    key=statkey["statkey"])
                if value is None:
                    value = "0"
                if os.environ['DEBUG'] == '1':
                    print(self.hosts[hs]['name'], "--add statkey:", statkey["label"], str(value))
                g.add_metric(labels=[self.hosts[hs]['datacenter'], self.hosts[hs]['parent_cluster_name'],
                                     self.hosts[hs]['name'], statkey["label"]], value=value)
        yield g
