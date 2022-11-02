from collectors.PropertiesCollector import PropertiesCollector


class VMPropertiesCollector(PropertiesCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'virtualmachine'
        self.label_names = [self.vrops_entity_name, 'vcenter', 'datacenter', 'vccluster', 'hostsystem',
                            'internal_name', 'instance_uuid', 'project']
        self.project_ids = True

    def get_resource_uuids(self):
        return self.get_vms_by_target()

    def get_labels(self, resource_id, project_ids):
        project_id = [vm_id_project_mapping[resource_id] for vm_id_project_mapping in project_ids if
                      resource_id in vm_id_project_mapping] if resource_id in self.vms else []
        project_id = project_id[0] if project_id else 'internal'

        return [self.vms[resource_id]['name'],
                self.vms[resource_id]['vcenter'],
                self.vms[resource_id]['datacenter'].lower(),
                self.vms[resource_id]['cluster'],
                self.vms[resource_id]['parent_host_name'],
                self.vms[resource_id]['internal_name'],
                self.vms[resource_id]['instance_uuid'],
                project_id] if resource_id else [] if resource_id in self.vms else []
