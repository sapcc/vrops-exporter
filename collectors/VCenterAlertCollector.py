from collectors.AlertCollector import AlertCollector


class VCenterAlertCollector(AlertCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'vcenter'
        self.label_names = [self.vrops_entity_name, 'datacenter']

    def get_resource_uuids(self):
        return self.get_vcenters_by_target()

    def set_labels(self, resource_id, project_ids):
        return [self.vcenters[resource_id]['name'],
                self.vcenters[resource_id]['kind_dc_name'].lower()] if resource_id else []

    def set_resourcekind(self):
        return []

    def set_uuids(self):
        return self.get_vcenters_by_target()
