from BaseCollector import BaseCollector
from tools.Resources import Resources
from threading import Thread
import os


class VMStatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'virtualmachine'
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__
        # self.post_registered_collector(self.name, g.name)

    def collect(self):
        gauges = self.generate_gauges('metric', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'datacenter', 'vccluster', 'hostsystem', 'project'])
        if not gauges:
            return
        project_ids = self.get_project_ids_by_target()

        if os.environ['DEBUG'] >= '1':
            print(self.name, 'starts with collecting the metrics')

        thread_list = list()
        for target in self.get_vms_by_target():
            project_ids_target = project_ids[target]
            t = Thread(target=self.do_metrics, args=(target, gauges, project_ids_target))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']

    def do_metrics(self, target, gauges, project_ids):
        token = self.get_target_tokens()
        token = token[target]
        if not token:
            print("skipping " + target + " in " + self.name + ", no token")
        uuids = self.target_vms[target]

        for metric_suffix in gauges:
            statkey = gauges[metric_suffix]['statkey']
            values = Resources.get_latest_stat_multiple(target, token, uuids, statkey)
            if os.environ['DEBUG'] >= '1':
                print(target, statkey)
                print("amount uuids", str(len(uuids)))
                print("fetched     ", str(len(values)))
            if not values:
                print("skipping statkey " + str(statkey) + " in", self.name, ", no return")
                continue

            for value_entry in values:
                metric_value = value_entry['stat-list']['stat'][0]['data'][0]
                if metric_value:
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
