import os
from BaseCollector import BaseCollector
from prometheus_client.core import GaugeMetricFamily
from tools.get_metrics import get_metric


class HostSystemCollector(BaseCollector):

    def __init__(self, resources, user, password):
        self._resources = resources
        self._user = user
        self._password = password
        self._statkeys = [{"name": "hardware_number_of_cpu_cores_info",
                         "statkey": "hardware|cpuinfo|numCpuCores)"},
                        {"name": "hardware_number_of_cpu_sockets_info",
                         "statkey": "cpu|numpackages"},
                        {"name": "memory_swap_used_kilobytes",
                         "statkey": "mem|swapused_average"},
                        {"name": "memory_useable_kilobytes",
                         "statkey": "mem|host_usable"},
                        {"name": "memory_usage_percentage",
                         "statkey": "mem|usage_average"},
                        {"name": "memory_balloon_kilobytes",
                         "statkey": "mem|vmmemctl_average"},
                        {"name": "memory_compressed_kilobytes",
                         "statkey": "mem|compressed_average"},
                        {"name": "memory_guest_active_kilobytes",
                         "statkey": "mem|active_average"},
                        {"name": "memory_consumed_kilobytes",
                         "statkey": "mem|consumed_average"},
                        {"name": "memory_capacity_available_to_vms_kilobytes",
                         "statkey": "mem|totalCapacity_average"},
                        {"name": "memory_total_capacity_kilobytes",
                         "statkey": "mem|host_provisioned"},
                        {"name": "summary_number_of_running_vms_kilobytes",
                         "statkey": "summary|number_running_vms"},
                        {"name": "network_packets_dropped_rx_number",
                         "statkey": "net|droppedRx_summation"},
                        {"name": "network_packets_dropped_tx_number",
                         "statkey": "net|droppedTx_summation"},
                        {"name": "network_packets_dropped_percentage",
                         "statkey": "net|droppedPct"}]

    def collect(self):
        metric_list = []
        g = GaugeMetricFamily('HostSystemCollector', os.environ["TARGET"],
                              labels=['name', 'statkey'])
        for cluster in self._resources.datacenter[0].clusters:
            for host in cluster.hosts:
                for statkey in self._statkeys:
                    if os.environ['DEBUG'] == '1':
                        print(host.name, "--add statkey:", statkey["name"])
                    value = get_metric(host.uuid, statkey["statkey"])
                    if value is None:
                        g.add_metric(labels=[host.name, statkey["name"]],
                                     value="0.0")
                    else:
                        g.add_metric(labels=[host.name, statkey["name"]],
                                     value=value)
                        metric_list.append(g)
        return metric_list

