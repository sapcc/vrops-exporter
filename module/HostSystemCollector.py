from BaseCollector import BaseCollector
from prometheus_client.core import GaugeMetricFamily
from tools.get_metrics import get_metrics


class HostSystemCollector(BaseCollector):

    def __init__(self, resources, target, user, password):
        self._resources = resources
        self._target = target
        self._user = user
        self._password = password

    def collect(self):

        statkeys = [{"name": "Hardware|CPU Information|Number of CPUs (Cores)",
                     "statkey": "hardware|cpuinfo|numCpuCores)"},
                    {"name": "CPU|Number of CPU Sockets",
                     "statkey": "cpu|numpackages"},
                    {"name": "Memory|Swap Used (KB)",
                     "statkey": "mem|swapused_average"},
                    {"name": "Memory|Usable Memory (KB)",
                     "statkey": "mem|host_usable"},
                    {"name": "Memory|Usage (%)",
                     "statkey": "mem|usage_average"},
                    {"name": "Memory|Balloon (KB)",
                     "statkey": "mem|vmmemctl_average"},
                    {"name": "Memory|Compressed (KB)",
                     "statkey": "mem|compressed_average"},
                    {"name": "Memory|Guest Active (KB)",
                     "statkey": "mem|active_average"},
                    {"name": "Memory|Consumed (KB)",
                     "statkey": "mem|consumed_average"},
                    {"name": "Memory|Capacity Available to VMs (KB)",
                     "statkey": "mem|totalCapacity_average"},
                    {"name": "Memory|Total Capacity (KB)",
                     "statkey": "mem|host_provisioned"},
                    {"name": "Summary|Number of Running VMs",
                     "statkey": "summary|number_running_vms"},
                    {"name": "Network|Packets Dropped",
                     "statkey": "net|droppedRx_summation"},
                    {"name": "Network|Transmitted Packets Dropped",
                     "statkey": "net|droppedTx_summation"},
                    {"name": "Network|Packets Dropped (%)",
                     "statkey": "net|droppedPct"},]
        metric_list = []

        g = GaugeMetricFamily('vrops_resource_gauge', 'HostSystemCollector',
                              labels=['target', 'name', 'uuid'])

        for cluster in self._resources.datacenter[0].clusters:
            for host in cluster.hosts:
                for statkey in statkeys:
                    get_metrics(self._target, host.name, host.uuid, statkey["statkey"])
                    g.add_metric(labels=[self._target, host.name, host.uuid,  ], value=)

        metric_list.append(g)

        return metric_list
