from collectors.AlertCollector import AlertCollector


class NSXTMgmtClusterAlertCollector(AlertCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'nsxt_mgmt_cluster'
        self.label_names = ['nsxt_mgmt_cluster', 'nsxt_adapter', 'target']
        self.resourcekind = ["ManagementCluster"]

    def get_resource_uuids(self):
        return self.get_nsxt_mgmt_cluster_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.nsxt_mgmt_cluster[resource_id]['name'],
                self.nsxt_mgmt_cluster[resource_id]['nsxt_adapter_name'],
                self.nsxt_mgmt_cluster[resource_id]['target']] if resource_id in self.nsxt_mgmt_cluster else []
