from BaseCollector import BaseCollector
import os, time
from prometheus_client.core import GaugeMetricFamily


class SampleCollector(BaseCollector):
    def __init__(self):
        self.iteration = 0
        while not self.iteration:
            time.sleep(5)
            self.get_iteration()
            print("waiting for initial iteration")
        print("done: initial query")

    def collect(self):
        if os.environ['DEBUG'] >= '1':
            print('SampleCollector is collecting...')

        g = GaugeMetricFamily('vrops_inventory_collection_iteration', 'actual run of resource collection',
                              labels=['vcenter'])
        for vc in self.get_vcenters():
            self.get_iteration()

            g.add_metric(labels=[self.vcenters[vc]['name']], value=int(self.iteration))
        yield g
