from collectors.StatsCollector import StatsCollector


class VCenterStatsCollector(StatsCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'vcenter'
        self.label_names = [self.vrops_entity_name, 'datacenter']

    def get_resource_uuids(self):
        return self.get_vcenters_by_target()

    def set_labels(self, resource_id, project_ids):
        return [self.vcenters[resource_id]['name'],
                self.vcenters[resource_id]['kind_dc_name'].lower()] if resource_id else []
