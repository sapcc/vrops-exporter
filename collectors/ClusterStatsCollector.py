from collectors.StatsCollector import StatsCollector


class ClusterStatsCollector(StatsCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'cluster'
        self.label_names = ['vccluster', 'vcenter', 'datacenter']

    def get_resource_uuids(self):
        return self.get_clusters_by_target()

    def set_labels(self, resource_id, project_ids):
        return [self.clusters[resource_id]['name'],
                self.clusters[resource_id]['vcenter'],
                self.clusters[resource_id]['parent_dc_name'].lower()] if resource_id else []
