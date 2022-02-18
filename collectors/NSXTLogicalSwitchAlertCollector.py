from collectors.AlertCollector import AlertCollector


class NSXTLogicalSwitchAlertCollector(AlertCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'nsxt_logical_switch'
        self.label_names = ['nsxt_mgmt_cluster', 'nsxt_adapter', self.vrops_entity_name, 'target']
        self.resourcekind = ["LogicalSwitch"]

    def get_resource_uuids(self):
        return self.get_nsxt_logical_switches_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.nsxt_logical_switches[resource_id]['mgmt_cluster_name'],
                self.nsxt_logical_switches[resource_id]['nsxt_adapter_name'],
                self.nsxt_logical_switches[resource_id]['name'],
                self.nsxt_logical_switches[resource_id]['target']] if resource_id in self.nsxt_logical_switches else []
