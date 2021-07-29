from BaseCollector import BaseCollector
from prometheus_client.core import GaugeMetricFamily
import logging
import time

logger = logging.getLogger('vrops-exporter')


class AlertCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.alertdefinitions = self.get_alertdefinitions()
        while not self.alertdefinitions:
            t = 60
            logger.critical(f'{self.name} could not get the alertdefinitions from inventory.'
                            f'Retrying in {t}s')
            time.sleep(t)
        self.resourcekind = list()

    def get_resource_uuids(self):
        raise NotImplementedError("Please Implement this method")

    def get_labels(self, resource_id: str, project_ids: list):
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

        # Mapping uuids to names
        self.get_resource_uuids()
        alert_config = self.read_collector_config()['alerts']

        alert_metric = self.generate_alert_metrics(label_names=self.label_names)
        project_ids = self.get_project_ids_by_target() if self.project_ids else []
        alerts, api_responding, api_response_time = \
            self.vrops.get_alerts(self.target, token,
                                  resourcekinds=self.resourcekind,
                                  alert_criticality=[a for a in alert_config.get('alertCriticality')],
                                  active_only=alert_config.get('activeOnly'))
        yield self.create_api_response_code_metric(self.name, api_responding)
        yield self.create_api_response_time_metric(self.name, api_response_time)

        if not alerts:
            logger.warning(f'No alerts in the response for {self.name}. API code: {api_responding}')
            return

        alert_labels = self.generate_alert_label_values(alerts)

        for resource in alerts:
            resource_id = resource.get('resourceId')
            label_names = alert_metric._labelnames
            labels = self.get_labels(resource_id, project_ids)
            if not labels:
                continue
            labels.extend([resource['alertDefinitionName'],
                           resource['alertLevel'],
                           resource['status'],
                           resource["alertImpact"]])
            for label_name, label_value in alert_labels.items():
                alert_metric._labelnames += (label_name,)
                labels.append(label_value)
            alert_metric.add_metric(labels=labels, value=1)
            alert_metric._labelnames = label_names
        yield alert_metric

    def generate_alert_label_values(self, alerts):
        alert_labels = dict()
        for resource in alerts:
            alert_entry = self.alertdefinitions.get(resource.get('alertDefinitionId', {}), {})
            alert_labels['description'] = alert_entry.get('description')
            for i, symptom in enumerate(alert_entry.get('symptoms', [])):
                alert_labels[f'symptom_{i+1}_name'] = symptom.get('name', "n/a")
                alert_labels[f'symptom_{i+1}_data'] = str(symptom.get('state', 'n/a'))
            for i, recommendation in enumerate(alert_entry.get('recommendations', [])):
                alert_labels[f'recommendation_{i+1}'] = recommendation.get('description', 'n/a')
        return alert_labels
