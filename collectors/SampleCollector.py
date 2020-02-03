from BaseCollector import BaseCollector
import os
from prometheus_client.core import GaugeMetricFamily


class SampleCollector(BaseCollector):

    def collect(self):
        if self.iteration == 0:
            time.sleep(10)
            print("Sleeping for 10")
            return
        if os.environ['DEBUG'] == '1':
            print('have some debug code in here')

        g = GaugeMetricFamily('vrops_inventory_collection_iteration', 'actual run of resource collection', labels= ['vcenter'])
        for vc in self.vcenters:
            g.add_metric(labels=[vc['name']], value=self.iteration)
        yield g
