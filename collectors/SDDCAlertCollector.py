from collectors.AlertCollector import AlertCollector


class SDDCAlertCollector(AlertCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'sddc'
        self.label_names = [self.vrops_entity_name, "target"]
        self.resourcekind = []
        self.adapterkind = ["SDDCHealthAdapter"]

    def get_resource_uuids(self):
        return self.get_sddc_objects_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.sddc_objects[resource_id]['name'],
                self.sddc_objects[resource_id]['target']] if resource_id in self.sddc_objects else []
