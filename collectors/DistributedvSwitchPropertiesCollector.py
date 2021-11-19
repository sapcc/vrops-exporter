from collectors.PropertiesCollector import PropertiesCollector


class DistributedvSwitchPropertiesCollector(PropertiesCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'distributed_virtual_switch'
        self.label_names = [self.vrops_entity_name, 'vcenter', 'datacenter']

    def get_resource_uuids(self):
        return self.get_dvs_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.dvs[resource_id]['name'],
                self.dvs[resource_id]['vcenter'],
                self.dvs[resource_id]['parent_dc_name'].lower()] if resource_id in self.dvs else []
