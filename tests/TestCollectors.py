import sys
import os
import unittest
import random
import http.client
from unittest.mock import MagicMock
from threading import Thread
import time

sys.path.append('.')

from exporter import run_prometheus_server
from tools.YamlRead import YamlRead
from tools.Resources import Resources
from InventoryBuilder import InventoryBuilder


class TestCollectors(unittest.TestCase):
    def test_environment(self):
        self.assertTrue(os.getenv('USER'), 'no dummy USER set')
        self.assertTrue(os.getenv('PASSWORD'), 'no dummy PASSWORD set')

    def test_collector_metrics(self):
        metrics_yaml = YamlRead('tests/metrics.yaml').run()
        print(metrics_yaml)

        # every collector got to be tested in here
        random_prometheus_port = random.randrange(9000, 9700, 1)
        print("chosen testport: " + str(random_prometheus_port))
        for collector in metrics_yaml.keys():
            print("\nTesting " + collector)

            InventoryBuilder.get_token = MagicMock(return_value="2ed214d523-235f-h283-4566-6sf356124fd62::f234234-234")
            InventoryBuilder.get_adapter = MagicMock(return_value=[{'name': "vcenter1", 'uuid': '5628-9ba1-55e84701'}])
            # test tool get_resources to create resource objects

            Resources.get_datacenter = MagicMock(return_value=[{'name': 'datacenter1', 'uuid': '5628-9ba1-55e847050814'},
                                                 {'name': 'datacenter2', 'uuid': '5628-9ba1-55e847050814'}])
            Resources.get_cluster = MagicMock(return_value=[{'name': 'cluster1', 'uuid': '3628-93a1-56e84634050814'},
                                              {'name': 'cluster2', 'uuid': '5628-9ba1-55e847050814'}])
            Resources.get_hosts = MagicMock(return_value=[{'name': 'hostsystem1', 'uuid': '3628-93a1-56e84634050814'},
                                            {'name': 'hostsystem2', 'uuid': '5628-9ba1-55e847050814'}])
            Resources.get_vmfolders = MagicMock(return_value=[{'name': 'vmfolder1', 'uuid': '3628-93a1-56e84634050814'},
                                                {'name': 'vmfolder2', 'uuid': '5628-9ba1-55e847050814'}])
            Resources.get_virtualmachines = MagicMock(return_value=[{'name': 'vm1', 'uuid': '3628-93a1-56e8463404'},
                                                      {'name': 'vm2', 'uuid': '5628-9ba1-55e847050814'}])
            Resources.get_resources = MagicMock(return_value=[{'name': 'resource1', 'uuid': '3628-93a1-56e8463404'},
                                                {'name': 'resource2', 'uuid': '5628-9ba1-55e847050814'}])
            Resources.get_metric = MagicMock(return_value=1.0)

            thread = Thread(target=InventoryBuilder, args=('./tests/test.json',))
            thread.daemon = True
            thread.start()

            # start prometheus server to provide metrics later on
            thread = Thread(target=run_prometheus_server, args=(random_prometheus_port,))
            thread.daemon = True
            thread.start()
            # give grandpa thread some time to get prometheus started and run a couple intervals of InventoryBuilder
            time.sleep(10)

            c = http.client.HTTPConnection("localhost:" + str(random_prometheus_port))
            c.request("GET", "/")
            r = c.getresponse()

            self.assertEqual(r.status, 200, "HTTP server return code should be 200")
            self.assertEqual(r.reason, "OK", "HTTP status should be OK")

            data = r.read().decode()
            data_array = data.split('\n')
            metrics = list()
            for entry in data_array:
                if entry.startswith('#'):
                    continue
                if entry.startswith('python_gc'):
                    continue
                if entry.startswith('process_'):
                    continue
                if entry.startswith('python_info'):
                    continue
                split_entry = entry.split()
                if len(split_entry) != 2:
                    continue
                metrics.append(split_entry[0])

            metrics_yaml_list = metrics_yaml[collector]['metrics']
            self.assertTrue(metrics_yaml_list, msg=collector + " has no metrics defined, FIX IT!")
            self.assertTrue(metrics, msg=collector + " is not producing any metrics at all, how should I continue?")
            # check if all metrics from yaml are here
            supersetdifference = set(metrics_yaml_list).difference(metrics)
            self.assertTrue(set(metrics).issuperset(metrics_yaml_list),
                            msg=collector + ": missing metrics from yaml:\n" + "\n".join(supersetdifference))

            # check if there are more metrics being produced and they are not listed in metrics.yaml?!
            issubsetdifference = set(metrics).difference(metrics_yaml_list)
            self.assertTrue(set(metrics).issubset(metrics_yaml_list),
                            msg=collector + ": metric not covered by testcase, probably missing in yaml\n" + "\n".join(
                                issubsetdifference))
            thread.join(timeout=0)
            # we don't want to have any port locks if prometheus server thread is not shutting down
            random_prometheus_port += 1


if __name__ == '__main__':
    unittest.main()
