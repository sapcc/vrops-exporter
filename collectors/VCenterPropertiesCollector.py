from BaseCollector import BaseCollector
from tools.Resources import Resources
from threading import Thread
import os


class VCenterPropertiesCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__
        self.vrops_entity_name = 'vcenter'
        # self.post_registered_collector(self.name, self.g.name, self.i.name + '_info')

    def collect(self):
        gauges = self.generate_gauges('property', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name])
        infos = self.generate_infos(self.name, self.vrops_entity_name,
                                    [self.vrops_entity_name])
        states = self.generate_states(self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'state'])

        if os.environ['DEBUG'] >= '1':
            print(self.name, 'starts with collecting the metrics')

        token = self.get_target_tokens()
        token = token[self.target]
        if not token:
            print("skipping", self.target, "in", self.name, ", no token")

        vc = self.get_vcenters(self.target)
        uuid = [vc[uuid]['uuid'] for uuid in vc][0]
        for metric_suffix in gauges:
            propkey = gauges[metric_suffix]['property']
            metric_value = Resources.get_property(self.target, token, uuid, propkey)
            if not metric_value:
                continue
            gauges[metric_suffix]['gauge'].add_metric(
                labels=[self.vcenters[uuid]['name']],
                value=metric_value)

        for metric_suffix in states:
            propkey = states[metric_suffix]['property']
            value = Resources.get_property(self.target, token, uuid, propkey)
            if not value:
                continue
            metric_value = (1 if states[metric_suffix]['expected'] == value else 0)
            states[metric_suffix]['state'].add_metric(
                labels=[self.vcenters[uuid]['name'],
                        value],
                value=metric_value)

        for metric_suffix in infos:
            propkey = infos[metric_suffix]['property']
            info_value = Resources.get_property(self.target, token, uuid, propkey)
            if not info_value:
                continue
            infos[metric_suffix]['info'].add_metric(
                labels=[self.vcenters[uuid]['name']],
                value={metric_suffix: info_value})

        # self.post_metrics(self.g.name)
        # self.post_metrics(self.i.name + '_info')
        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']
        for metric_suffix in infos:
            yield infos[metric_suffix]['info']
        for metric_suffix in states:
            yield states[metric_suffix]['state']
