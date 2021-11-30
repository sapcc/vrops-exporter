from collectors.StatsCollector import StatsCollector


class VcopsSelfMonitoringStatsCollector(StatsCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'self_object'
        self.label_names = [self.vrops_entity_name, 'target']

    def get_resource_uuids(self):
        return self.get_vcops_self_monitoring_objects_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.vcops_self_monitoring_objects[resource_id]['name'],
                self.vcops_self_monitoring_objects[resource_id]['target']] if \
            resource_id in self.vcops_self_monitoring_objects else []
