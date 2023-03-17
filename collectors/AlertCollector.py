from BaseCollector import BaseCollector
from prometheus_client.core import InfoMetricFamily
import logging
import time

logger = logging.getLogger('vrops-exporter')


class AlertCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.resourcekind = list()
        self.adapterkind = list()
        self.alert_entry_cache = dict()

    def get_resource_uuids(self):
        raise NotImplementedError("Please Implement this method")

    def get_labels(self, resource_id: str, project_ids: list):
        raise NotImplementedError("Please Implement this method")

    def describe(self):
        yield InfoMetricFamily(f'vrops_{self.vrops_entity_name}_alert', 'vrops-exporter', )

    def collect(self):
        logger.info(f'{self.name} starts with collecting the alerts')

        token = self.get_target_tokens()
        token = token.setdefault(self.target, '')
        if not token:
            logger.warning(f'skipping {self.target} in {self.name}, no token')
            return

        # Mapping uuids to names
        self.get_resource_uuids()
        alert_config = self.read_collector_config()['alerts']

        alert_metric = self.generate_alert_metrics(
            label_names=self.label_names)
        project_ids = self.get_project_ids_by_target() if self.project_ids else []
        alerts, api_responding, api_response_time = \
            self.vrops.get_alerts(self.target, token,
                                  resourcekinds=self.resourcekind,
                                  alert_criticality=[
                                      a for a in alert_config.get('alertCriticality')],
                                  active_only=alert_config.get('activeOnly'),
                                  adapterkinds=self.adapterkind if self.adapterkind else [])

        yield self.create_api_response_code_metric(self.name, api_responding)
        yield self.create_api_response_time_metric(self.name, api_response_time)

        if not alerts:
            logger.warning(
                f'No alerts in the response for {self.name}. API code: {api_responding}')
            return

        for alert in alerts:
            resource_id = alert.get('resourceId')
            labels = self.get_labels(resource_id, project_ids)
            if not labels:
                continue
            alert_labels = self.generate_alert_label_values(alert)
            if alert_labels:
                labels.extend([alert['alertDefinitionName'],
                               alert['alertLevel'],
                               alert['status'],
                               alert["alertImpact"]])
                alert_metric.add_metric(labels=labels, value=alert_labels)
        yield alert_metric

    def generate_alert_label_values(self, alert):
        alert_id = alert.get('alertDefinitionId', {})
        alert_labels = dict()
        alert_entry = self.alert_entry_cache.get(
            alert_id) if alert_id in self.alert_entry_cache else self.get_alertdefinition(alert_id)
        if not alert_entry:
            return {}
        self.alert_entry_cache[alert_id] = alert_entry
        alert_labels['description'] = alert_entry.get('description', "n/a")
        for i, symptom in enumerate(alert_entry.get('symptoms', [])):
            alert_labels[f'symptom_{i+1}_name'] = symptom.get('name', "n/a")
            alert_labels[f'symptom_{i+1}_data'] = str(
                symptom.get('state', 'n/a'))
        for i, recommendation in enumerate(alert_entry.get('recommendations', [])):
            alert_labels[f'recommendation_{i+1}'] = recommendation.get(
                'description', 'n/a')
        return alert_labels
