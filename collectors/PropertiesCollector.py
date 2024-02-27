from BaseCollector import BaseCollector
import logging

logger = logging.getLogger('vrops-exporter')


class PropertiesCollector(BaseCollector):

    def get_resource_uuids(self):
        raise NotImplementedError("Please Implement this method")

    def unlock_nested_values(self, s, m):
        raise NotImplementedError("Please Implement this method")

    def get_labels(self, resource_id: str, project_ids: list):
        raise NotImplementedError("Please Implement this method")

    def collect(self):
        self.collect_running = True
        logger.info(f'{self.name} starts with collecting the metrics')
        if self.nested_value_metric_keys:
            logger.info(f'Found nested metric values for: {self.name}, keys: {self.nested_value_metric_keys}')

        token = self.get_target_tokens()
        token = token.setdefault(self.target, '')
        if not token:
            logger.warning(f'skipping {self.target} in {self.name}, no token')
            return

        uuids = self.get_resource_uuids()
        if not uuids:
            logger.warning(f'skipping {self.target} in {self.name}, no resources')
            return

        metrics = self.generate_metrics(label_names=self.label_names)
        project_ids = self.get_project_ids_by_target() if self.project_ids else []
        values, api_responding, response_time = self.vrops.get_latest_properties_multiple(self.target,
                                                                                          token,
                                                                                          uuids,
                                                                                          [m for m in metrics],
                                                                                          self.name)
        yield self.create_api_response_code_metric(self.name, api_responding)
        yield self.create_api_response_time_metric(self.name, response_time)
        yield self.number_of_metrics_to_collect(self.name, len(metrics))
        yield self.number_of_resources(self.name, len(uuids))

        if not values:
            logger.warning(f'No values in the response for {self.name}. API code: {api_responding}')
            return

        values_received = set()
        no_match_in_config = list()

        for resource in values:
            resource_id = resource.get('resourceId')

            for value_entry in resource.get('property-contents', {}).get('property-content', []):
                labels = self.get_labels(resource_id, project_ids)
                if not labels:
                    continue

                statkey = value_entry.get('statKey')
                values_received.add(statkey)

                metric_data = value_entry.get('data', [False])[0]
                metric_value = value_entry.get('values', [False])[0]

                if statkey in self.nested_value_metric_keys:

                    add_labels, add_label_value_list, add_value = self.unlock_nested_values(statkey, metric_value)

                    if not add_labels:
                        metric_suffix = metrics[statkey]['metric_suffix']
                        self.add_metric_labels(metrics[statkey]['gauge'], [metric_suffix])
                        metrics[statkey]['gauge'].add_metric(labels=labels+[metric_suffix], value=0)
                        continue

                    self.add_metric_labels(metrics[statkey]['gauge'], add_labels)

                    for add_label_value in add_label_value_list:
                        metrics[statkey]['gauge'].add_metric(labels=labels+add_label_value, value=add_value)
                    continue

                if statkey in metrics:
                    # enum metrics
                    if metrics[statkey]['expected']:
                        self.add_metric_labels(metrics[statkey]['gauge'], ['state'])

                        state = metric_value if metric_value else 'n/a'
                        labels.append(state)
                        value = 1 if metric_value == metrics[statkey]['expected'] else 0
                        metrics[statkey]['gauge'].add_metric(labels=labels, value=value)

                    # string values
                    elif metric_value:
                        metric_suffix = metrics[statkey]['metric_suffix']
                        self.add_metric_labels(metrics[statkey]['gauge'], [metric_suffix])

                        labels.append(metric_value)
                        metrics[statkey]['gauge'].add_metric(labels=labels, value=1)

                    # float values
                    else:
                        metrics[statkey]['gauge'].add_metric(labels=labels, value=metric_data)
                else:
                    no_match_in_config.append([statkey, metric_data, labels])

        # no match in config, bring into the right format
        created_metrics = self.generate_metrics_enriched_by_api(no_match_in_config, label_names=self.label_names)

        for metric in metrics:
            yield self.number_of_metric_samples_generated(self.name, metrics[metric]['gauge'].name,
                                                          len(metrics[metric]['gauge'].samples))
            yield metrics[metric]['gauge']
        for metric in created_metrics:
            yield self.number_of_metric_samples_generated(self.name, created_metrics[metric].name,
                                                          len(created_metrics[metric].samples))
            logger.info(f'Created metrics enriched by API in {self.name}: {created_metrics[metric].name}')
            yield created_metrics[metric]
        self.collect_running = False
