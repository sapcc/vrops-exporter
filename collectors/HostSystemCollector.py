from BaseCollector import BaseCollector
import os, time, json
from pathlib import Path
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources


class HostSystemCollector(BaseCollector, Resources):
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
        try:
            folder = Path("collectors/")
            with open(folder / "metrics.json") as json_file:
                for metric in json.load(json_file)['HostSystemCollector']:
                    stat = dict()
                    stat['name'] = metric['name']
                    stat['statkey'] = metric['statkey']
                    self.statkeys.append(stat)
        except FileNotFoundError:
            raise FileNotFoundError("metrics.json does not exist!")

    def collect(self):
        if os.environ['DEBUG'] == '1':
            print('HostSystemCollector ist start collecting metrics')
            print("Target: " + str(self.target))
            print("Token: " + str(self.token))

        g = GaugeMetricFamily('vrops_hostsystem', str(self.target), labels=['datacenter', 'cluster',
                                                                            'hostsystem', 'statkey'])
        for hs in self.get_hosts():
            for statkey in self.statkeys:
                value = Resources.get_metric(self, target=self.target, token=self.token, uuid=self.hosts[hs]['uuid'],
                                             key=statkey["statkey"])
                if os.environ['DEBUG'] == '1':
                    print(self.hosts[hs]['name'], "--add statkey:", statkey["name"], str(value))
                if value is not None:
                    g.add_metric(labels=[self.hosts[hs]['datacenter'], self.hosts[hs]['parent_cluster_name'],
                                         self.hosts[hs]['name'], statkey["name"]], value=value)
                else:
                    g.add_metric(labels=[self.hosts[hs]['datacenter'], self.hosts[hs]['parent_cluster_name'],
                                         self.hosts[hs]['name'], statkey["name"]], value="0.0")
                yield g
