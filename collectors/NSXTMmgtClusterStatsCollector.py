from collectors.StatsCollector import StatsCollector


class NSXTMmgtClusterStatsCollector(StatsCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'nsxt'
        self.label_names = ['nsx_t_mgmt_cluster', 'nsx_t_adapter']

    def get_resource_uuids(self):
        return self.get_nsx_t_mgmt_cluster_by_target()

    def set_labels(self, resource_id, project_ids):
        return [self.nsx_t_mgmt_cluster[resource_id]['name'],
                self.nsx_t_mgmt_cluster[resource_id]['nsx_t_adapter_name']] if resource_id else []
