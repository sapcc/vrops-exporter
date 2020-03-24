from BaseCollector import BaseCollector
import os, time
from prometheus_client.core import GaugeMetricFamily
from tools.Resources import Resources
from tools.YamlRead import YamlRead


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
                              labels=['datacenter', 'vcenter', 'propkey'])

        for vc in self.get_vcenters():
            target = self.vcenters[vc]['target']
            target_vc = self.vcenters[vc]['name']
            token = self.vcenters[vc]['token']
            vc_uuid = self.vcenters[vc]['uuid']
            for cl in self.get_clusters():
                if self.clusters[cl]['vcenter'] == target_vc:
                    dc_name = self.clusters[cl]['parent_dc_name']

            for property_pair in self.property_yaml["VcenterPropertiesCollector"]['info_metrics']:
                property_label = property_pair['label']
                propkey = property_pair['property']

                vc_values = Resources.get_property(target, token, vc_uuid, propkey)

                if not vc_values:
                    continue
                try:
                    info_value = int(vc_values)
                    g.add_metric(labels=[dc_name, target_vc,
                                         property_label], value=info_value)
                except (ValueError, TypeError):
                    info = vc_values
                    info_value = 0
                    g.add_metric(labels=[dc_name, target_vc,
                                         property_label + ": " + info], value=info_value)


            yield g