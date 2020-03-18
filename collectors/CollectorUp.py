exp import os
from prometheus_client.core import GaugeMetricFamily


class CollectorUp:
    def __init__(self, collectors, metrics=None):
        self.collectors = list()
        for collector in collectors:
            self.collectors.append(collector[0])
        self.metrics = metrics

    def collect(self):
        if os.environ['DEBUG'] >= '1':
            print("Creating collector_up metrics")

        g = GaugeMetricFamily('vrops_collector_up', 'testtext', labels=['collector'])

        if not self.metrics:
            for metric in self.collectors:
                g.add_metric(labels=[metric], value=0)
        else:
            for metric in self.collectors:
                if metric in self.metrics:
                    g.add_metric(labels=[metric], value=1)
                else:
                    g.add_metric(labels=[metric], value=0)

        yield g
