from collectors.PropertiesCollector import PropertiesCollector


class NSXTMmgtNodePropertiesCollector(PropertiesCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'nsxt_mgmt_node'
        self.label_names = ['nsxt_mgmt_cluster', 'nsxt_adapter', 'nsxt_mgmt_node']

    def get_resource_uuids(self):
        return self.get_nsxt_mgmt_nodes_by_target()

    def set_labels(self, resource_id, project_ids):
        return [self.nsxt_mgmt_nodes[resource_id]['mgmt_cluster_name'],
                self.nsxt_mgmt_nodes[resource_id]['nsxt_adapter_name'],
                self.nsxt_mgmt_nodes[resource_id]['name']] if resource_id else []
