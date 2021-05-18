from collectors.PropertiesCollector import PropertiesCollector


class NSXTMmgtClusterPropertiesCollector(PropertiesCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'nsxt'
        self.label_names = ['nsxt_mgmt_cluster', 'nsxt_adapter']

    def get_resource_uuids(self):
        return self.get_nsxt_mgmt_cluster_by_target()

    def set_labels(self, resource_id, project_ids):
        return [self.nsxt_mgmt_cluster[resource_id]['name'],
                self.nsxt_mgmt_cluster[resource_id]['nsxt_adapter_name']] if resource_id else []