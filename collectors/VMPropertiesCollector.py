from BaseCollector import BaseCollector
from tools.Vrops import Vrops
import logging

logger = logging.getLogger('vrops-exporter')


class VMPropertiesCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__
        self.vrops_entity_name = 'virtualmachine'

    def collect(self):
        logger.info(f' {self.name} starts with collecting the metrics')

        token = self.get_target_tokens()
        token = token.setdefault(self.target, None)

        if not token:
            logger.warning(f'skipping {self.target} in {self.name}, no token')
            return

        http_response_code, http_gauge = self.create_http_response_metric(self.target, token, self.name)
        logger.debug(f'HTTP response code in {self.name} for {self.target}: {http_response_code}')
        yield http_gauge

        if http_response_code > 200:
            logger.critical(f'HTTP response code in {self.name} for {self.target}: {http_response_code}, no return')
            return

        gauges = self.generate_gauges('property', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'vcenter', 'datacenter', 'vccluster', 'hostsystem',
                                       'project'])
        infos = self.generate_infos(self.name, self.vrops_entity_name,
                                    [self.vrops_entity_name, 'vcenter', 'datacenter', 'vccluster', 'hostsystem',
                                     'project'])
        states = self.generate_states(self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'vcenter', 'datacenter', 'vccluster', 'hostsystem',
                                       'state', 'project'])

        project_ids = self.get_project_ids_by_target()

        uuids = self.get_vms_by_target()
        for metric_suffix in gauges:
            propkey = gauges[metric_suffix]['property']
            values = Vrops.get_latest_number_properties_multiple(self.target, token, uuids, propkey, self.name)
            if not values:
                logging.warning(f'Skipping {propkey}, no values in respond')
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
                            self.vms[vm_id]['vcenter'],
                            self.vms[vm_id]['datacenter'].lower(),
                            self.vms[vm_id]['cluster'],
                            self.vms[vm_id]['parent_host_name'],
                            project_id],
                    value=metric_value)

        for metric_suffix in states:
            propkey = states[metric_suffix]['property']
            values = Vrops.get_latest_enum_properties_multiple(self.target, token, uuids, propkey, self.name)
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
                            self.vms[vm_id]['vcenter'],
                            self.vms[vm_id]['datacenter'].lower(),
                            self.vms[vm_id]['cluster'],
                            self.vms[vm_id]['parent_host_name'],
                            value_entry['value'],
                            project_id],
                    value=data)

        for metric_suffix in infos:
            propkey = infos[metric_suffix]['property']
            values = Vrops.get_latest_info_properties_multiple(self.target, token, uuids, propkey, self.name)
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
                            self.vms[vm_id]['vcenter'],
                            self.vms[vm_id]['datacenter'].lower(),
                            self.vms[vm_id]['cluster'],
                            self.vms[vm_id]['parent_host_name'],
                            project_id],
                    value={metric_suffix: info_value})

        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']
        for metric_suffix in infos:
            yield infos[metric_suffix]['info']
        for metric_suffix in states:
            yield states[metric_suffix]['state']
