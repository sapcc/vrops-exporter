from collectors.PropertiesCollector import PropertiesCollector


class VCenterPropertiesCollector(PropertiesCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'vcenter'
        self.label_names = [self.vrops_entity_name, 'datacenter']

    def get_resource_uuids(self):
        return self.get_vcenters_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.vcenters[resource_id]['name'],
                self.vcenters[resource_id]['kind_dc_name'].lower()] if resource_id in self.vcenters else []
