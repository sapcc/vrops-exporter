from BaseCollector import BaseCollector
from tools.Vrops import Vrops
import logging

logger = logging.getLogger('vrops-exporter')


class VMStatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'virtualmachine'
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__
        self.rubricated = True

    def collect(self):
        logger.info(f' {self.name} starts with collecting the metrics')

        token = self.get_target_tokens()
        token = token.setdefault(self.target, None)

        if not token:
            logger.warning(f'skipping {self.target} in {self.name}, no token')
            return

        if self.rubricated and not self.rubric:
            logger.warning(f'{self.name} has no rubric given. Considering all.')

        gauges = self.generate_gauges('stats', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'vcenter', 'datacenter', 'vccluster', 'hostsystem',
                                       'project'], rubric=self.rubric)
        project_ids = self.get_project_ids_by_target()

        uuids = self.get_vms_by_target()
        for metric_suffix in gauges:
            statkey = gauges[metric_suffix]['statkey']
            values = Vrops.get_latest_stat_multiple(self.target, token, uuids, statkey, self.name)
            if not values:
                logger.warning(f'Skipping statkey: {statkey} in {self.name} , no return')
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
