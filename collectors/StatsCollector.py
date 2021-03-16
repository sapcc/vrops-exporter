from BaseCollector import BaseCollector
import logging

logger = logging.getLogger('vrops-exporter')


class StatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()

    def get_uuids(self):
        raise NotImplementedError("Please Implement this method")

    def set_labels(self, resource_id: str, project_ids: list):
        raise NotImplementedError("Please Implement this method")

    def collect(self):
        logger.info(f'{self.name} starts with collecting the metrics')

        token = self.get_target_tokens()
        token = token.setdefault(self.target, '')
        if not token:
            logger.warning(f'skipping {self.target} in {self.name}, no token')
            return

        uuids = self.get_uuids()
        metrics = self.generate_metrics(label_names=self.label_names)
        project_ids = self.get_project_ids_by_target() if self.project_ids else []
        values, api_responding = self.vrops.get_latest_stats_multiple(self.target,
                                                                      token,
                                                                      uuids,
                                                                      [m for m in metrics],
                                                                      self.name)
        yield self.create_api_response_metric(self.name, api_responding)

        if not values:
            logger.warning(f'No values in the response for {self.name}. API code: {api_responding}')
            return

        no_match_in_config = set()
        values_received = set()

        for resource in values:
            resource_id = resource.get('resourceId')
            labels = self.set_labels(resource_id, project_ids)

            for value_entry in resource.get('stat-list', {}).get('stat', []):
                statkey = value_entry.get('statKey', {}).get('key')
                values_received.add(statkey)

                metric_data = value_entry.get('data', [None])[0]
                if statkey in metrics and metric_data is not None:
                    metrics[statkey]['gauge'].add_metric(labels=labels, value=metric_data)
                else:
                    no_match_in_config.add(statkey)

        if list(no_match_in_config):
            logger.warning(f'Skipped keys, due to no match with config in {self.name}: {list(no_match_in_config)} '
                           f'<-- compare with collector_config')

        metrics_without_values = [m for m in metrics if m not in values_received]
        if metrics_without_values:
            logger.warning(f'No values for keys in {self.name}: {metrics_without_values}')

        for metric in metrics:
            yield metrics[metric]['gauge']
