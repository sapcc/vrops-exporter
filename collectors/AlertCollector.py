from BaseCollector import BaseCollector
from prometheus_client.core import GaugeMetricFamily
import logging

logger = logging.getLogger('vrops-exporter')


class AlertCollector(BaseCollector):

    def get_resource_uuids(self):
        raise NotImplementedError("Please Implement this method")

    def set_uuids(self):
        return []

    def set_labels(self, resource_id: str, project_ids: list):
        raise NotImplementedError("Please Implement this method")

    def set_resourcekind(self):
        raise NotImplementedError("Please Implement this method")

    def describe(self):
        yield GaugeMetricFamily(f'vrops_{self.vrops_entity_name}_alert', 'vrops-exporter', )

    def collect(self):
        logger.info(f'{self.name} starts with collecting the alerts')

        token = self.get_target_tokens()
        token = token.setdefault(self.target, '')
        if not token:
            logger.warning(f'skipping {self.target} in {self.name}, no token')
            return

        self.get_resource_uuids()

        alert_metric = self.generate_alert_metrics(label_names=self.label_names)
        project_ids = self.get_project_ids_by_target() if self.project_ids else []
        alerts, api_responding, response_time = self.vrops.get_alerts(self.target, token,
                                                                      resourceIds=self.set_uuids(),
                                                                      resourcekinds=self.set_resourcekind(),
                                                                      alert_criticality=['CRITICAL', 'WARNING',
                                                                                         'IMMEDIATE'])

        if not alerts:
            logger.warning(f'No alerts in the response for {self.name}. API code: {api_responding}')
            return

        for resource in alerts:
            resource_id = resource.get('resourceId')
            labels = self.set_labels(resource_id, project_ids)
            if not labels:
                continue
            labels.extend([resource['alertDefinitionName'],
                           resource['alertLevel'],
                           resource['status'],
                           resource["alertImpact"]])
            alert_metric.add_metric(labels=labels, value=1)

        yield alert_metric
