from BaseCollector import BaseCollector
import os, time
from prometheus_client.core import GaugeMetricFamily


class SampleCollector(BaseCollector):
    def __init__(self):
        if os.environ.get('INVENTORY', None):
            self.wait_for_inventory_data()
            # self.post_registered_collector(self.__class__.__name__, g.name)
        else:
            print("No InventoryService in ENV. Cannot start {}".format(self.__class__.__name__))


    def describe(self):
        yield GaugeMetricFamily('vrops_inventory_collection_iteration', 'actual run of resource collection')

    def collect(self):
        g = GaugeMetricFamily('vrops_inventory_collection_iteration', 'actual run of resource collection',
                              labels=['vcenter'])
        if os.environ['DEBUG'] >= '1':
            print('SampleCollector is collecting...')

        for vc in self.get_vcenters():
            self.get_iteration()

            g.add_metric(labels=[self.vcenters[vc]['name']], value=int(self.iteration))
        # self.post_metrics(g.name)
        yield g
