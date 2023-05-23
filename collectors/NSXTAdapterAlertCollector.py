from collectors.AlertCollector import AlertCollector


class NSXTAdapterAlertCollector(AlertCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'nsxt_adapter'
        self.label_names = [self.vrops_entity_name, 'target']
        self.resourcekind = ["NSXTAdapterInstance"]

    def get_resource_uuids(self):
        return self.get_nsxt_adapter_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.nsxt_adapter[resource_id]['name'],
                self.nsxt_adapter[resource_id]['target']] if resource_id in self.nsxt_adapter else []
