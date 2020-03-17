from BaseCollector import BaseCollector
import os, time, json
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead
from pprint import pprint


class VcenterPropertiesCollector(BaseCollector):
    def __init__(self):
        self.iteration = 0
        while not self.iteration:
            time.sleep(5)
            self.get_iteration()
            print("waiting for initial iteration")
        print("done: initial query")
        self.property_yaml = YamlRead('collectors/property.yaml').run()

    def collect(self):
        if os.environ['DEBUG'] >= '1':
            print('vCenterPropertiesCollector starts with collecting the properties')

        g = GaugeMetricFamily('vrops_vcenter_properties', 'testtest',
                              labels=['vcenter', 'propkey'])

        for vc in self.get_vcenters():

            target = self.vcenters[vc]['target']
            token = self.vcenters[vc]['token']
            vc_uuid = self.vcenters[vc]['uuid']

            for property_pair in self.property_yaml["VCenterPropertiesCollector"]['info_metrics']:
                property_label = property_pair['label']
                propkey = property_pair['property']

                vc_values = Resources.get_property(target, token, vc_uuid, propkey)
                print(vc_values)
                g.add_metric(labels=[self.vcenters[vc]['name'], property_label], value="{}".format(vc_values))

                if not vc_values:
                    continue
                for value_entry in vc_values:
                    print(value_entry)
                    try:
                        info_value = int(value_entry)
                        g.add_metric(labels=[self.vcenters[vc]['name'], property_label], value=info_value)
                    except (ValueError, TypeError):
                        info = vc_values
                        info_value = 0
                        g.add_metric(labels=[self.vcenters[vc]['name'],
                                     property_label + ": " + info], value=info_value)


            yield g