from BaseCollector import BaseCollector
import os, time
from prometheus_client.core import GaugeMetricFamily
from tools.get_metric import get_metric


class HostSystemCollector(BaseCollector):
    def __init__(self):
        self.iteration = 0
        while not self.iteration:
            time.sleep(5)
            self.get_iteration()
            print("waiting for initial iteration")
        print("done: initial query")
        self.token = self.get_token()
        self.target = self.get_target()
        self.statkeys = [{"name": "hardware_number_of_cpu_cores_info",
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
        if os.environ['DEBUG'] == '1':
            print('HostSystemCollector ist start collecting metrics')
            print("Target: " + str(self.target))
            print("Token: " + str(self.token))
        g = GaugeMetricFamily('vrops_hostsystem', str(self.target), labels=['cluster', 'hostsystem', 'statkey'])
        for hs in self.get_hosts():
            self.get_iteration()
            for statkey in self.statkeys:
                if os.environ['DEBUG'] == '1':
                    print(self.hosts[hs]['name'], "--add statkey:", statkey["name"])
                value = get_metric(target=self.target, token=self.token, uuid=self.hosts[hs]['uuid'],
                                   key=statkey["statkey"])
                if value is None:
                    g.add_metric(labels=[self.hosts[hs]['parent_cluster'], self.hosts[hs]['name'], statkey["name"]],
                                 value="0.0")
                    yield g
                else:
                    g.add_metric([self.hosts[hs]['parent_cluster'], self.hosts[hs]['name'], statkey["name"]],
                                 value=value)
                    yield g
