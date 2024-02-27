from collectors.StatsCollector import StatsCollector


class SDRSStatsCollector(StatsCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'storagepod' 
        self.label_names = [self.vrops_entity_name, 'vcenter', 'datacenter']

    def get_resource_uuids(self):
        return self.get_SDRS_clusters_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.sdrs_clusters[resource_id]['name'],
                self.sdrs_clusters[resource_id]['vcenter'],
                self.sdrs_clusters[resource_id]['parent_dc_name'].lower()] if resource_id in self.sdrs_clusters else []
