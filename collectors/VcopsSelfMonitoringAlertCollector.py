from collectors.AlertCollector import AlertCollector


class VcopsSelfMonitoringAlertCollector(AlertCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'self_object'
        self.label_names = [self.vrops_entity_name, "target"]
        self.resourcekind = []
        self.adapterkind = ["vCenter Operations Adapter"]

    def get_resource_uuids(self):
        return self.get_vcops_objects_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.vcops_objects[resource_id]['name'],
                self.vcops_objects[resource_id]['target']] if resource_id in self.vcops_objects else []
