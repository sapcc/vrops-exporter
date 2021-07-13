from BaseCollector import BaseCollector
from prometheus_client.core import GaugeMetricFamily
import logging

logger = logging.getLogger('vrops-exporter')


class AlertCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.alertdefinitions = self.get_alertdefinitions()["alertDefinitions"]
        self.symptomdefinitions = self.get_symptomdefinitions()["symptomDefinitions"]
        self.recommendations = self.get_recommendations()["recommendations"]
        self.resourcekind = list()
        self.use_resource_uuids = False

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

        # # Mapping uuids to names
        # self.get_resource_uuids()

        alert_config = self.read_collector_config()['alerts']

        alert_metric = self.generate_alert_metrics(label_names=self.label_names)
        project_ids = self.get_project_ids_by_target() if self.project_ids else []
        alerts, api_responding, api_response_time = \
            self.vrops.get_alerts(self.target, token,
                                  resourcekinds=self.resourcekind,
                                  resourceIds=self.get_resource_uuids() if self.use_resource_uuids else [],
                                  alert_criticality=alert_config.get('alertCriticality'),
                                  active_only=alert_config.get('activeOnly'))
        yield self.create_api_response_code_metric(self.name, api_responding)
        yield self.create_api_response_time_metric(self.name, api_response_time)

        if not alerts:
            logger.warning(f'No alerts in the response for {self.name}. API code: {api_responding}')
            return

        alert_labels = self.generate_alert_label_values(alerts)

        for resource in alerts:
            resource_id = resource.get('resourceId')
            labels = self.get_labels(resource_id, project_ids)
            if not labels:
                continue
            labels.extend([resource['alertDefinitionName'],
                           resource['alertLevel'],
                           resource['status'],
                           resource["alertImpact"],
                           alert_labels.get("symptom_name", "n/a"),
                           alert_labels.get('symptom_state', "n/a"),
                           alert_labels.get("recommendation", "n/a")])
            alert_metric.add_metric(labels=labels, value=1)

        yield alert_metric

    def generate_alert_label_values(self, alerts):
        alert_labels = dict()
        for resource in alerts:
            for alert in self.alertdefinitions:
                if alert['id'] == resource['alertDefinitionId']:
                    symptomdefinition_ids = alert.get("states", [])[0].get("base-symptom-set", {}).get(
                        "symptomDefinitionIds", [])
                    for symptom_id in symptomdefinition_ids:
                        for symptomdefinition_id in self.symptomdefinitions:
                            if symptom_id == symptomdefinition_id['id']:
                                alert_labels["symptom_name"] = symptomdefinition_id['name']
                                alert_labels['symptom_state'] = str(symptomdefinition_id['state'])
                    recommendation_ids = alert.get("states", [])[0].get("recommendationPriorityMap", {})
                    for recommendation in recommendation_ids:
                        for rd in self.recommendations:
                            if recommendation == rd["id"]:
                                alert_labels["recommendation"] = self.remove_html_tags(rd["description"])
        return alert_labels
