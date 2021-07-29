from collectors.StatsCollector import StatsCollector


class DatastoreStatsCollector(StatsCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'datastore'
        self.label_names = [self.vrops_entity_name, 'vcenter', 'type', 'datacenter']

    def get_resource_uuids(self):
        return self.get_datastores_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.datastores[resource_id]['name'],
                self.datastores[resource_id]['vcenter'],
                self.datastores[resource_id]['type'],
                self.datastores[resource_id]['parent_dc_name'].lower()] if resource_id in self.datastores else []
