from BaseCollector import BaseCollector
import os, time
from prometheus_client.core import GaugeMetricFamily


class SampleCollector(BaseCollector):
    def __init__(self):
        self.iteration = 0
        while not self.iteration:
            time.sleep(2)
            self.get_iteration()
            if os.environ['DEBUG']:
                print("waiting for iteration")
        if os.environ['DEBUG']:
            print("done waiting for iteration")

    def collect(self):
        if os.environ['DEBUG'] == '1':
            print('have some debug code in here')

        g = GaugeMetricFamily('vrops_inventory_collection_iteration', 'actual run of resource collection', labels= ['vcenter'])
        for vc in self.get_vcenters():
            self.get_iteration()
            g.add_metric(labels=[self.vcenters[vc]['name']], value=int(self.iteration))
        yield g
