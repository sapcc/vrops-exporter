from collectors.PropertiesCollector import PropertiesCollector


class DatastorePropertiesCollector(PropertiesCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'datastore'
        self.label_names = [self.vrops_entity_name, 'vcenter', 'type', 'datacenter', 'storagepod']

    def get_resource_uuids(self):
        return self.get_datastores_by_target()

    def get_labels(self, resource_id, project_ids):
        label_values = [self.datastores[resource_id]['name'],
                        self.datastores[resource_id]['vcenter'],
                        self.datastores[resource_id]['type'],
                        self.datastores[resource_id]['parent_dc_name'].lower()] if resource_id in self.datastores else []

        if sc_name := self.datastores[resource_id].get('storage_cluster_name'):
            label_values.append(sc_name)
        else:
            label_values.append("none")

        return label_values
