from BaseCollector import BaseCollector
import os, time
from prometheus_client.core import GaugeMetricFamily


class SampleCollector(BaseCollector):
    def __init__(self):
        self.wait_for_inventory_data()
        self.g = GaugeMetricFamily('vrops_inventory_collection_iteration', 'actual run of resource collection',
                              labels=['vcenter'])

    def describe(self):
        yield self.g

    def collect(self):
        if os.environ['DEBUG'] >= '1':
            print('SampleCollector is collecting...')

        for vc in self.get_vcenters():
            self.get_iteration()

            self.g.add_metric(labels=[self.vcenters[vc]['name']], value=int(self.iteration))
        yield self.g
