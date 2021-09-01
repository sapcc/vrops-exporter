from collectors.StatsCollector import StatsCollector


class HostSystemStatsCollector(StatsCollector):
    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'hostsystem'
        self.label_names = [self.vrops_entity_name, 'vcenter', 'datacenter', 'vccluster', 'internal_name']

    def get_resource_uuids(self):
        return self.get_hosts_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.hosts[resource_id]['name'],
                self.hosts[resource_id]['vcenter'],
                self.hosts[resource_id]['datacenter'].lower(),
                self.hosts[resource_id]['parent_cluster_name'],
                self.hosts[resource_id]['internal_name']] if resource_id in self.hosts else []
