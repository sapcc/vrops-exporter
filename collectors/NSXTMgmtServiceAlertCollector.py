from collectors.AlertCollector import AlertCollector


class NSXTMgmtServiceAlertCollector(AlertCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'nsxt_mgmt_service'
        self.label_names = ['nsxt_mgmt_service', 'nsxt_adapter']
        self.resourcekind = ["ManagementService"]

    def get_resource_uuids(self):
        return self.get_nsxt_mgmt_service_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.nsxt_mgmt_service[resource_id]['name'],
                self.nsxt_mgmt_service[resource_id]['nsxt_adapter_name']] if resource_id else []