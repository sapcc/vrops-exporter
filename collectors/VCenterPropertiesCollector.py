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

        thread_list = list()
        for vc in self.get_vcenters():
            target = self.vcenters[vc]['target']
            t = Thread(target=self.do_metrics, args=(target, gauges, infos, states))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        # self.post_metrics(self.g.name)
        # self.post_metrics(self.i.name + '_info')
        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']
        for metric_suffix in infos:
            yield infos[metric_suffix]['info']
        for metric_suffix in states:
            yield states[metric_suffix]['state']

    def do_metrics(self, target, gauges, infos, states):
        token = self.get_target_tokens()
        token = token[target]
        if not token:
            print("skipping", target, "in", self.name, ", no token")

        for vc in self.get_vcenters():
            uuid = self.vcenters[vc]['uuid']

            for metric_suffix in gauges:
                propkey = gauges[metric_suffix]['property']
                metric_value = Resources.get_property(target, token, uuid, propkey)
                if not metric_value:
                    continue
                gauges[metric_suffix]['gauge'].add_metric(
                    labels=[self.vcenters[vc]['name']],
                    value=metric_value)

            for metric_suffix in states:
                propkey = states[metric_suffix]['property']
                value = Resources.get_property(target, token, uuid, propkey)
                if not value:
                    continue
                metric_value = (1 if states[metric_suffix]['expected'] == value else 0)
                states[metric_suffix]['state'].add_metric(
                    labels=[self.vcenters[vc]['name'],
                            value],
                    value=metric_value)

            for metric_suffix in infos:
                propkey = infos[metric_suffix]['property']
                info_value = Resources.get_property(target, token, uuid, propkey)
                if not info_value:
                    continue
                infos[metric_suffix]['info'].add_metric(
                    labels=[self.vcenters[vc]['name']],
                    value={metric_suffix: info_value})
