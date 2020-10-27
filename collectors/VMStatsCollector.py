from BaseCollector import BaseCollector
from tools.Vrops import Vrops
import os


class VMStatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'virtualmachine'
        self.rubric = os.environ['RUBRIC']
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__

    def collect(self):
        gauges = self.generate_gauges('stats', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'vcenter', 'datacenter', 'vccluster', 'hostsystem',
                                       'project'], rubric=self.rubric)
        project_ids = self.get_project_ids_by_target()

        if os.environ['DEBUG'] >= '1':
            print(self.name, 'starts with collecting the metrics')

        token = self.get_target_tokens()
        token = token[self.target]

        if not token:
            print("skipping " + self.target + " in " + self.name + ", no token")

        uuids = self.get_vms_by_target()
        for metric_suffix in gauges:
            statkey = gauges[metric_suffix]['statkey']
            values = Vrops.get_latest_stat_multiple(self.target, token, uuids, statkey)
            if os.environ['DEBUG'] >= '1':
                print(self.target, statkey)
                print("amount uuids", str(len(uuids)))
                print("fetched     ", str(len(values)))
            if not values:
                print("skipping statkey " + str(statkey) + " in", self.name, ", no return")
                continue

            for value_entry in values:
                metric_value = value_entry['stat-list']['stat'][0]['data']
                if metric_value:
                    metric_value = metric_value[0]
                    vm_id = value_entry['resourceId']
                    project_id = "internal"
                    if project_ids:
                        for vm_id_project_mapping in project_ids:
                            if vm_id in vm_id_project_mapping:
                                project_id = vm_id_project_mapping[vm_id]
                    gauges[metric_suffix]['gauge'].add_metric(
                        labels=[self.vms[vm_id]['name'],
                                self.vms[vm_id]['vcenter'],
                                self.vms[vm_id]['datacenter'].lower(),
                                self.vms[vm_id]['cluster'],
                                self.vms[vm_id]['parent_host_name'],
                                project_id],
                        value=metric_value)

        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']
