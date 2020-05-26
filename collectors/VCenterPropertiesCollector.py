from BaseCollector import BaseCollector
import os
from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead
from threading import Thread


class VCenterPropertiesCollector(BaseCollector):
    def __init__(self):
        self.wait_for_inventory_data()
        self.property_yaml = YamlRead('collectors/property.yaml').run()
        self.name = self.__class__.__name__
        # self.post_registered_collector(self.name, self.g.name, self.i.name + '_info')

    def describe(self):
        yield GaugeMetricFamily('vrops_vcenter_properties', 'testtest')
        yield InfoMetricFamily('vrops_vcenter', 'testtest')

    def collect(self):
        g = GaugeMetricFamily('vrops_vcenter_properties', 'testtest',
                              labels=['vcenter', 'propkey'])
        i = InfoMetricFamily('vrops_vcenter', 'testtest',
                                  labels=['vcenter'])
        if os.environ['DEBUG'] >= '1':
            print('VCenterPropertiesCollector starts with collecting the metrics')

        thread_list = list()
        for vc in self.get_vcenters():
            target = self.vcenters[vc]['target']
            t = Thread(target=self.do_metrics, args=(target, g, i))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        yield g
        yield i

    def do_metrics(self, target, g, i):
        token = self.get_target_tokens()
        token = token[target]
        if not token:
            print("skipping " + target + " in , no token")

        for vc in self.get_vcenters():
            uuid = self.vcenters[vc]['uuid']
            target_vc = self.vcenters[vc]['name']
            if 'info_metrics' in self.property_yaml[self.name]:
                for property_pair in self.property_yaml["VCenterPropertiesCollector"]['info_metrics']:
                    property_label = property_pair['label']
                    propkey = property_pair['property']

                    values = Resources.get_property(target, token, uuid, propkey)

                    if not values:
                        continue
                    info_value = str(values)
                    i.add_metric(labels=[target_vc], value={property_label: info_value})
