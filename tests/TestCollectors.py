import sys

sys.path.append('.')
from unittest.mock import MagicMock
from threading import Thread
from exporter import run_prometheus_server
from tools.helper import yaml_read
from tools.Vrops import Vrops
from InventoryBuilder import InventoryBuilder
from collectors.HostSystemStatsCollector import HostSystemStatsCollector
from collectors.HostSystemPropertiesCollector import HostSystemPropertiesCollector
from collectors.DatastoreStatsCollector import DatastoreStatsCollector
from collectors.DatastorePropertiesCollector import DatastorePropertiesCollector
from collectors.ClusterPropertiesCollector import ClusterPropertiesCollector
from collectors.VMStatsCollector import VMStatsCollector
from collectors.VMPropertiesCollector import VMPropertiesCollector
from collectors.ClusterStatsCollector import ClusterStatsCollector
from collectors.VCenterStatsCollector import VCenterStatsCollector
from collectors.VCenterPropertiesCollector import VCenterPropertiesCollector
from prometheus_client.core import REGISTRY
import unittest
import random
import http.client
import os
import time


class TestCollectors(unittest.TestCase):
    os.environ.setdefault('TARGET', 'testhost.test')

    def test_environment(self):
        self.assertTrue(os.getenv('USER'), 'no dummy USER set')
        self.assertTrue(os.getenv('PASSWORD'), 'no dummy PASSWORD set')
        self.assertTrue(os.getenv('CONFIG'), 'no collector CONFIG set')
        self.assertTrue(os.getenv('TARGET'), 'no target set')

    def test_collector_metrics(self):
        self.metrics_yaml = yaml_read('tests/metrics.yaml')
        # every collector got to be tested in here
        self.random_prometheus_port = random.randrange(9000, 9700, 1)
        print("chosen testport: " + str(self.random_prometheus_port))

        Vrops.get_token = MagicMock(return_value="2ed214d523-235f-h283-4566-6sf356124fd62::f234234-234")
        Vrops.get_adapter = MagicMock(return_value=("vcenter1", "3628-93a1-56e84634050814"))
        # test tool get_resources to create resource objects
        Vrops.get_http_response_code = MagicMock(return_value=200)

        Vrops.get_datacenter = MagicMock(return_value=[{'name': 'datacenter1', 'uuid': '3628-93a1-56e84634050814',
                                                        'resourcekind': 'Datacenter',
                                                        'parent': '3628-93a1-56e84634050814'},
                                                       {'name': 'datacenter2', 'uuid': '5628-9ba1-55e847050815',
                                                        'resourcekind': 'Datacenter',
                                                        'parent': '3628-93a1-56e84634050814'},
                                                       {'name': 'datacenter3', 'uuid': '7422-91h7-52s842060815',
                                                        'resourcekind': 'Datacenter',
                                                        'parent': '3628-93a1-56e84634050814'}])
        Vrops.get_vccluster = MagicMock(return_value=[{'name': 'cluster1', 'uuid': '3628-93a1-56e84634050814',
                                                       'resourcekind': 'ClusterComputeResource',
                                                       'parent': '7422-91h7-52s842060815'},
                                                      {'name': 'cluster2', 'uuid': '5628-9ba1-55e847050815',
                                                       'resourcekind': 'ClusterComputeResource',
                                                       'parent': '7422-91h7-52s842060815'},
                                                      {'name': 'cluster3', 'uuid': '7422-91h7-52s842060815',
                                                       'resourcekind': 'ClusterComputeResource',
                                                       'parent': '7422-91h7-52s842060815'}])
        Vrops.get_hosts = MagicMock(return_value=[{'name': 'hostsystem1', 'uuid': '3628-93a1-56e84634050814',
                                                   'resourcekind': 'HostSystem',
                                                   'parent': '7422-91h7-52s842060815'},
                                                  {'name': 'hostsystem2', 'uuid': '5628-9ba1-55e847050815',
                                                   'resourcekind': 'HostSystem',
                                                   'parent': '7422-91h7-52s842060815'},
                                                  {'name': 'hostsystem3', 'uuid': '7422-91h7-52s842060815',
                                                   'resourcekind': 'HostSystem',
                                                   'parent': '7422-91h7-52s842060815'}])
        Vrops.get_vms_and_ds = MagicMock(return_value=[{'name': 'vm1', 'uuid': '3628-93a1-56e84634050814',
                                                        'resourcekind': 'VirtualMachine',
                                                        'parent': '7422-91h7-52s842060815'},
                                                       {'name': 'vm2', 'uuid': '5628-9ba1-55e847050815',
                                                        'resourcekind': 'VirtualMachine',
                                                        'parent': '7422-91h7-52s842060815'},
                                                       {'name': 'vm3', 'uuid': '7422-91h7-52s842060815',
                                                        'resourcekind': 'VirtualMachine',
                                                        'parent': '7422-91h7-52s842060815'},
                                                       {'name': 'vmfs_vc-w-0_p_ssd_bb091_001',
                                                        'uuid': '3628-93a1-56e84634050814',
                                                        'resourcekind': 'Datastore',
                                                        'parent': '7422-91h7-52s842060815'},
                                                       {'name': 'eph-bb112-1', 'uuid': '5628-9ba1-55e847050815',
                                                        'resourcekind': 'Datastore',
                                                        'parent': '7422-91h7-52s842060815'},
                                                       {'name': 'B121_Management_DS03',
                                                        'uuid': '7422-91h7-52s842060815',
                                                        'resourcekind': 'Datastore',
                                                        'parent': '7422-91h7-52s842060815'}])
        Vrops.get_latest_stat = MagicMock(return_value=1)
        Vrops.get_property = MagicMock(return_value="test_property")
        Vrops.get_project_ids = MagicMock(return_value=[{"3628-93a1-56e84634050814": "0815"},
                                                        {"7422-91h7-52s842060815": "0815"},
                                                        {"5628-9ba1-55e847050815": "internal"}])
        thread = Thread(target=InventoryBuilder, args=('./tests/test.json', 8000, 180, 300))
        thread.daemon = True
        thread.start()

        for collector in self.metrics_yaml.keys():
            print("\nTesting " + collector)
            if self.metrics_yaml[collector]['rubrics']:
                for rubric in self.metrics_yaml[collector]['metrics']:
                    os.environ['RUBRIC'] = rubric
                    print("Testing rubric:", rubric)
                    self.collector_testrun(collector, rubric)
            else:
                self.collector_testrun(collector)

    def collector_testrun(self, collector, rubric=None):
        if 'Stats' in collector:
            # mocking all values from yaml
            statkey_yaml = yaml_read(os.environ['CONFIG'])['statkeys']
            multiple_metrics_generated = list()

            def append_metrics(statkey_pair):
                multiple_metrics_generated.append({"resourceId": "3628-93a1-56e84634050814", "stat-list": {"stat": [
                    {"timestamps": [1582797716394], "statKey": {"key": statkey_pair['statkey']}, "data": [88.0]}]}})
                multiple_metrics_generated.append({"resourceId": "5628-9ba1-55e847050815", "stat-list": {"stat": [
                    {"timestamps": [1582797716394], "statKey": {"key": statkey_pair['statkey']}, "data": [44.0]}]}})
                multiple_metrics_generated.append({"resourceId": "7422-91h7-52s842060815", "stat-list": {"stat": [
                    {"timestamps": [1582797716394], "statKey": {"key": statkey_pair['statkey']}, "data": [55.0]}]}})

            if rubric:
                for statkey_pair in statkey_yaml[collector][rubric]:
                    append_metrics(statkey_pair)
            else:
                for statkey_pair in statkey_yaml[collector]:
                    append_metrics(statkey_pair)
            Vrops.get_latest_stat_multiple = MagicMock(return_value=multiple_metrics_generated)

        if "Properties" in collector:
            propkey_yaml = yaml_read(os.environ['CONFIG'])['properties']
            multiple_enum_properties_generated = list()
            if 'enum_metrics' in propkey_yaml[collector]:
                for propkey_pair in propkey_yaml[collector]['enum_metrics']:
                    multiple_enum_properties_generated.append({'resourceId': '3628-93a1-56e84634050814',
                                                               'propkey': propkey_pair['property'],
                                                               'value': "test_enum_property"})
                    multiple_enum_properties_generated.append({'resourceId': "5628-9ba1-55e847050815",
                                                               'propkey': propkey_pair['property'],
                                                               'value': "test_enum_property"})
                    multiple_enum_properties_generated.append({'resourceId': "7422-91h7-52s842060815",
                                                               'propkey': propkey_pair['property'],
                                                               'value': "test_enum_property"})
            Vrops.get_latest_enum_properties_multiple = MagicMock(
                return_value=multiple_enum_properties_generated)

            multiple_number_properties_generated = list()
            if 'number_metrics' in propkey_yaml[collector]:
                for propkey_pair in propkey_yaml[collector]['number_metrics']:
                    multiple_number_properties_generated.append({'resourceId': '3628-93a1-56e84634050814',
                                                                 'propkey': propkey_pair['property'],
                                                                 'data': 19.54})
                    multiple_number_properties_generated.append({'resourceId': "5628-9ba1-55e847050815",
                                                                 'propkey': propkey_pair['property'],
                                                                 'data': '6.5'})
                    multiple_number_properties_generated.append({'resourceId': "7422-91h7-52s842060815",
                                                                 'propkey': propkey_pair['property'],
                                                                 'data': 33})
            Vrops.get_latest_number_properties_multiple = MagicMock(
                return_value=multiple_number_properties_generated)

            multiple_info_properties_generated = list()
            if 'info_metrics' in propkey_yaml[collector]:
                for propkey_pair in propkey_yaml[collector]['info_metrics']:
                    multiple_info_properties_generated.append({'resourceId': '3628-93a1-56e84634050814',
                                                               'propkey': propkey_pair['property'],
                                                               'data': 'test_info_property'})
                    multiple_info_properties_generated.append({'resourceId': "5628-9ba1-55e847050815",
                                                               'propkey': propkey_pair['property'],
                                                               'data': 'test_info_property'})
                    multiple_info_properties_generated.append({'resourceId': "7422-91h7-52s842060815",
                                                               'propkey': propkey_pair['property'],
                                                               'data': 'test_info_property'})
            Vrops.get_latest_info_properties_multiple = MagicMock(
                return_value=multiple_info_properties_generated)

        thread_list = list()

        # start prometheus server to provide metrics later on
        collector_instance = globals()[collector]()
        thread1 = Thread(target=run_prometheus_server, args=(self.random_prometheus_port, [collector_instance]))
        thread1.daemon = True
        thread1.start()
        thread_list.append(thread1)
        # give grandpa thread some time to get prometheus started and run a couple intervals of InventoryBuilder
        time.sleep(10)

        print("prometheus query port " + str(self.random_prometheus_port))
        c = http.client.HTTPConnection("localhost:" + str(self.random_prometheus_port))
        c.request("GET", "/")
        r = c.getresponse()
        self.assertEqual(r.status, 200, "HTTP server return code should be 200")
        self.assertEqual(r.reason, "OK", "HTTP status should be OK")

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
            split_entry = entry.split("}")
            if len(split_entry) != 2:
                continue
            metrics.add(split_entry[0] + "}")

        if rubric:
            metrics_yaml_list = self.metrics_yaml[collector]['metrics'][rubric]
        else:
            metrics_yaml_list = self.metrics_yaml[collector]['metrics']
        self.assertTrue(metrics_yaml_list, msg=collector + " has no metrics defined, FIX IT!")
        self.assertTrue(metrics, msg=collector + " is not producing any metrics at all, how should I continue?")

        # check if there are more metrics being produced and they are not listed in metrics.yaml?!
        issubsetdifference = metrics.difference(metrics_yaml_list)
        self.assertTrue(metrics.issubset(metrics_yaml_list),
                        msg=collector + ": metric not covered by testcase, probably missing in yaml\n" + "\n".join(
                            issubsetdifference))
        # check if all metrics from yaml are here
        supersetdifference = set(metrics_yaml_list).difference(metrics)
        self.assertTrue(set(metrics).issuperset(metrics_yaml_list),
                        msg=collector + ": missing metrics from yaml:\n" + "\n".join(supersetdifference))

        for t in thread_list:
            t.join(timeout=5)

        # we don't want to have any port locks if prometheus server thread is not shutting down
        self.random_prometheus_port += 1
        REGISTRY.unregister(collector_instance)


if __name__ == '__main__':
    unittest.main()
