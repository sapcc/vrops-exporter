import sys
import os
import unittest
import random
import http.client
from unittest.mock import MagicMock
from threading import Thread
from vrops_exporter import run_prometheus_server
from tools.YamlRead import YamlRead
from VropsCollector import VropsCollector

sys.path.append('../vrops-exporter')
sys.path.append('../vrops-exporter/tools')
sys.path.append('../vrops-exporter/modules')


class TestCollectors(unittest.TestCase):
    USER = os.getenv('USER')
    PASSWORD = os.getenv('PASSWORD')
    # PORT        = int(os.getenv('PORT'))
    TARGET = os.getenv('TARGET')

    def test_collector_metrics(self):
        metrics_yaml = YamlRead('tests/metrics.yaml').run()
        print(metrics_yaml)
        # every collector got to be tested in here
        random_prometheus_port = random.randrange(9000, 9700, 1)
        for collector in metrics_yaml.keys():
            print()  # nicer output
            print("Testing " + collector)
            VropsCollector.get_modules = MagicMock(return_value=('/vrops-exporter/module', [collector]))

            # start prometheus server to provide metrics later on
            thread = Thread(target=run_prometheus_server, args=(random_prometheus_port,))
            thread.daemon = True
            thread.start()

            c = http.client.HTTPConnection("localhost:" + str(random_prometheus_port))
            c.request("GET", "/?target=testhost.test")
            r = c.getresponse()

            self.assertEqual(r.status, 200, "HTTP server return code should be 200")
            self.assertEqual(r.reason, "OK", "HTTP status should be OK")

            data = r.read().decode()
            data_array = data.split('\n')
            metrics = list()
            for entry in data_array:
                if entry.startswith('#'):
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
