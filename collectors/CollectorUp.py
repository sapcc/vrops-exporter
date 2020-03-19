import os, http.client
from prometheus_client.core import GaugeMetricFamily


def get_collector_up_information(port):
    c = http.client.HTTPConnection("localhost:" + str(port))
    c.request("GET", "/")
    r = c.getresponse()
    if r.status != 200:
        return False
    data = r.read().decode()
    data_array = data.split('\n')
    metrics = set()
    for entry in data_array:
        if entry.startswith('#'):
            continue
        if entry.startswith('python_gc'):
            continue
        if entry.startswith('process_'):
            continue
        if entry.startswith('python_info'):
            continue
        split_entry = entry.split("{")
        if len(split_entry) != 2:
            continue
        metrics.add(split_entry[0])
    return list(metrics)


class CollectorUp:
    def __init__(self, collectors, metrics=None):
        self.collectors = collectors
        self.metrics = metrics

    def desc_func(self):
        return 'vrops_collector_up'

    def collect(self):
        if os.environ['DEBUG'] >= '1':
            print("Creating collector_up metrics")

        g = GaugeMetricFamily('vrops_collector_up', 'testtext', labels=['collector'])

        collector_list = []
        for collector in self.collectors:
            collector_list.append(collector.desc_func())

        if not self.metrics:
            for metric in collector_list:
                g.add_metric(labels=[metric], value=0)
        else:
            for metric in collector_list:
                if metric in self.metrics:
                    g.add_metric(labels=[metric], value=1)
                else:
                    g.add_metric(labels=[metric], value=0)

        yield g
