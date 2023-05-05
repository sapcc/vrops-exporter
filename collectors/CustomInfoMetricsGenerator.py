from BaseCollector import BaseCollector

from prometheus_client.core import InfoMetricFamily
import logging

logger = logging.getLogger('vrops-exporter')


class CustomInfoMetricsGenerator(BaseCollector):

    def __init__(self):
        super().__init__()
        self.name = self.__class__.__name__

    def describe(self):
        custom_metrics = self.read_collector_config().get('CustomInfoMetricsGenerator')
        for entry in custom_metrics:
            yield InfoMetricFamily(entry['metric'], 'vrops-exporter')

    def collect(self):
        logger.info(f'{self.name} starts with collecting the metrics')

        custom_metrics = self.read_collector_config().get('CustomInfoMetricsGenerator')
        for entry in custom_metrics:
            custom_info_metric = InfoMetricFamily(entry['metric'], 'vrops-exporter', labels=['target'])
            custom_info_metric.add_metric(labels=[self.target], value=entry['values_dict'])
            yield custom_info_metric
