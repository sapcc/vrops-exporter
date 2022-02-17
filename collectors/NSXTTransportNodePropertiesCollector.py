from collectors.PropertiesCollector import PropertiesCollector


class NSXTTransportNodePropertiesCollector(PropertiesCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'nsxt_transport_node'
        self.label_names = ['nsxt_mgmt_cluster', 'nsxt_adapter', 'nsxt_transport_zone', 'nsxt_transport_node', 'target']

    def get_resource_uuids(self):
        return self.get_nsxt_transport_nodes_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.nsxt_transport_nodes[resource_id]['mgmt_cluster_name'],
                self.nsxt_transport_nodes[resource_id]['nsxt_adapter_name'],
                self.nsxt_transport_nodes[resource_id]['transport_zone_name'],
                self.nsxt_transport_nodes[resource_id]['name'],
                self.nsxt_transport_nodes[resource_id]['target']] if resource_id in self.nsxt_transport_nodes else []
