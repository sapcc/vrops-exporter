from collectors.StatsCollector import StatsCollector


class DatastoreStatsCollector(StatsCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'datastore'
        self.label_names = [self.vrops_entity_name, 'vcenter', 'type', 'datacenter', 'storagepod']

    def get_resource_uuids(self):
        return self.get_datastores_by_target()

    def get_labels(self, resource_id, project_ids):
        if 'storagepod' in self.label_names:
            self.label_names.pop()

        label_values = [self.datastores[resource_id]['name'],
                        self.datastores[resource_id]['vcenter'],
                        self.datastores[resource_id]['type'],
                        self.datastores[resource_id]['parent_dc_name'].lower()] if resource_id in self.datastores else []

        if sc_name := self.datastores[resource_id].get('storage_cluster_name'):
            self.label_names.append('storagepod')
            label_values.append(sc_name)

        return label_values
