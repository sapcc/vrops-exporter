import os
from prometheus_client.core import GaugeMetricFamily
from BaseCollector import BaseCollector


class CollectorUp(BaseCollector):
    def __init__(self):
        self.g = GaugeMetricFamily('vrops_collector_up', 'testtext', labels=['collector'])
        self.post_registered_collector(self.__class__.__name__, self.g.name)

    def describe(self):
        yield self.g

    def collect(self):
        if os.environ['DEBUG'] >= '1':
            print("Creating collector_up metrics")
        self.post_metrics(self.g.name)
        collectors = []
        for c in self.get_registered_collectors()['collectors registered']:
            collectors.append(c['metric_name'])
        metrics = []
        for m in self.get_metrics()['metrics']:
            metrics.append(m['metric_name'])
        for collector in collectors:
            if collector in metrics:
                self.g.add_metric(labels=[collector], value=1)
            else:
                self.g.add_metric(labels=[collector], value=0)
        self.delete_metrics()
        yield self.g
