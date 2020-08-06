from BaseCollector import BaseCollector
from tools.Resources import Resources
from threading import Thread
import os


class VMPropertiesCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__
        self.vrops_entity_name = 'virtualmachine'
        # self.post_registered_collector(self.name, self.g.name, self.i.name + '_info')

    def collect(self):
        gauges = self.generate_gauges('property', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'datacenter', 'vccluster', 'hostsystem', 'project'])
        infos = self.generate_infos(self.name, self.vrops_entity_name,
                                    [self.vrops_entity_name, 'datacenter', 'vccluster', 'hostsystem', 'project'])
        states = self.generate_states(self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'datacenter', 'vccluster', 'hostsystem', 'state'
                                       'project'])
        if not gauges:
            return

        project_ids = self.get_project_ids_by_target()

        if os.environ['DEBUG'] >= '1':
            print(self.name, 'starts with collecting the metrics')

        thread_list = list()
        for target in self.get_vms_by_target():
            project_ids_target = project_ids[target]
            t = Thread(target=self.do_metrics, args=(target, gauges, infos, states, project_ids_target))
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

    def do_metrics(self, target, gauges, infos, states, project_ids):
        token = self.get_target_tokens()
        token = token[target]

        if not token:
            print("skipping", target, "in", self.name, ", no token")

        uuids = self.target_vms[target]
        for metric_suffix in gauges:
            propkey = gauges[metric_suffix]['property']
            values = Resources.get_latest_number_properties_multiple(target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'data' not in value_entry:
                    continue
                metric_value = value_entry['data']
                vm_id = value_entry['resourceId']
                project_id = "internal"
                if project_ids:
                    for vm_id_project_mapping in project_ids:
                        if vm_id in vm_id_project_mapping:
                            project_id = vm_id_project_mapping[vm_id]
                gauges[metric_suffix]['gauge'].add_metric(
                    labels=[self.vms[vm_id]['name'],
                            self.vms[vm_id]['datacenter'].lower(),
                            self.vms[vm_id]['cluster'],
                            self.vms[vm_id]['parent_host_name'],
                            project_id],
                    value=metric_value)

        for metric_suffix in states:
            propkey = states[metric_suffix]['property']
            values = Resources.get_latest_enum_properties_multiple(target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'value' not in value_entry:
                    continue
                data = (1 if states[metric_suffix]['expected'] == value_entry['value'] else 0)
                vm_id = value_entry['resourceId']
                project_id = "internal"
                if project_ids:
                    for vm_id_project_mapping in project_ids:
                        if vm_id in vm_id_project_mapping:
                            project_id = vm_id_project_mapping[vm_id]
                states[metric_suffix]['state'].add_metric(
                    labels=[self.vms[vm_id]['name'],
                            self.vms[vm_id]['datacenter'].lower(),
                            self.vms[vm_id]['cluster'],
                            self.vms[vm_id]['parent_host_name'],
                            value_entry['value'],
                            project_id],
                    value=data)

        for metric_suffix in infos:
            propkey = infos[metric_suffix]['property']
            values = Resources.get_latest_info_properties_multiple(target, token, uuids, propkey)
            if not values:
                continue
            for value_entry in values:
                if 'data' not in value_entry:
                    continue
                vm_id = value_entry['resourceId']
                project_id = "internal"
                if project_ids:
                    for vm_id_project_mapping in project_ids:
                        if vm_id in vm_id_project_mapping:
                            project_id = vm_id_project_mapping[vm_id]
                info_value = value_entry['data']
                infos[metric_suffix]['info'].add_metric(
                    labels=[self.vms[vm_id]['name'],
                            self.vms[vm_id]['datacenter'].lower(),
                            self.vms[vm_id]['cluster'],
                            self.vms[vm_id]['parent_host_name'],
                            project_id],
                    value={metric_suffix: info_value})