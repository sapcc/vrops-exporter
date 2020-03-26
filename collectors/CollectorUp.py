import os
from prometheus_client.core import GaugeMetricFamily
from BaseCollector import BaseCollector


class CollectorUp(BaseCollector):
    def __init__(self):
        self.g = GaugeMetricFamily('vrops_collector_up', 'testtext', labels=['collector', 'metrics'])
        self.post_registered_collector(self.__class__.__name__, self.g.name)

    def describe(self):
        yield self.g

    def collect(self):
        if os.environ['DEBUG'] >= '1':
            print("Creating collector_up metrics")
        self.post_metrics(self.g.name)

        metrics = []
        for m in self.get_metrics()['metrics']:
            metrics.append(m['metric_name'])

        for collector in self.get_registered_collectors()['collectors registered']:
            for metric_name in collector['metrics']:
                if metric_name in metrics:
                    self.g.add_metric(labels=[collector['collector'], metric_name], value=1)
                else:
                    self.g.add_metric(labels=[collector['collector'], metric_name], value=0)
        self.delete_metrics()
        yield self.g
