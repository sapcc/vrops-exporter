import sys

sys.path.append('.')
from unittest.mock import MagicMock, patch
from threading import Thread
from exporter import run_prometheus_server
from tools.helper import yaml_read
from tools.Vrops import Vrops
from inventory.Builder import InventoryBuilder
from BaseCollector import BaseCollector
from prometheus_client.core import REGISTRY
import unittest
import random
import http.client
import os
import time
import importlib


class TestCollectors(unittest.TestCase):
    print(f"Running TestCollectors")
    os.environ.setdefault('TARGET', "vrops-vcenter-test.company.com")

    def test_environment(self):
        self.assertTrue(os.getenv('USER'), 'no dummy USER set')
        self.assertTrue(os.getenv('PASSWORD'), 'no dummy PASSWORD set')
        self.assertTrue(os.getenv('COLLECTOR_CONFIG'), 'no COLLECTOR CONFIG set')
        self.assertTrue(os.getenv('INVENTORY_CONFIG'), 'no INVENTORY CONFIG set')
        self.assertTrue(os.getenv('TARGET'), 'no target set')
        self.assertEqual(os.getenv('TARGET'), "vrops-vcenter-test.company.com", "The test must be run with the target: vrops-vcenter-test.company.com")

    @patch('exporter.signal.signal')
    def test_collector_metrics(self, mock_signal):
        self.metrics_yaml = yaml_read('tests/metrics.yaml')
        self.collector_config = yaml_read(os.environ['COLLECTOR_CONFIG'])
        self.target = os.getenv('TARGET')
        self.token = '2ed214d523-235f-h283-4566-6sf356124fd62::f234234-234'
        # every collector got to be tested in here
        self.random_prometheus_port = random.randrange(9000, 9700, 1)
        print("chosen testport: " + str(self.random_prometheus_port))

        BaseCollector.get_target_tokens = MagicMock(
            return_value={self.target: self.token})
        Vrops.get_token = MagicMock(return_value=("2ed214d523-235f-h283-4566-6sf356124fd62::f234234-234", 200, 0.282561))

        def create_adapter_objects(adapterkind) -> list:
            uuids = ["3628-93a1-56e84634050814", "3628-93a1-56e84634050814"]
            object_list = list()
            for i, _ in enumerate(uuids):
                resource_object = type(adapterkind.capitalize(), (object,), {
                    "name": f'{adapterkind.lower()}_{i + 1}',
                    "uuid": uuids[0],
                    "target": self.target,
                    "token": self.token
                })
                object_list.append(resource_object)
            return object_list

        Vrops.get_adapter = MagicMock(return_value=None)
        Vrops.get_vcenter_adapter = MagicMock(return_value=(create_adapter_objects("Vcenter"), 200, 0.282561))
        Vrops.get_nsxt_adapter = MagicMock(return_value=(create_adapter_objects("NSXTAdapterInstance"), 200, 0.282561))
        Vrops.get_vcenter_operations_adapter_intance = MagicMock(
            return_value=(create_adapter_objects("VcopsAdapterInstance"), 200, 0.282561))
        Vrops.get_sddc_health_adapter_intance = MagicMock(
            return_value=(create_adapter_objects("SDDCAdapterInstance"), 200, 0.282561))

        # test tool get_resources to create resource objects
        def create_resource_objects(resourcekind) -> list:
            uuids = ["3628-93a1-56e84634050814", "7422-91h7-52s842060815", "5628-9ba1-55e847050815"]
            object_list = list()
            for i, _ in enumerate(uuids):
                resource_object = type(resourcekind.capitalize(), (object,), {
                    "name": f'{resourcekind.capitalize()}_{i + 1}',
                    "uuid": uuids[i],
                    "resourcekind": resourcekind,
                    "parent": uuids[0],
                    "internal_name": f'{resourcekind.lower()}_1234',
                    "instance_uuid": f'{resourcekind.lower()}_12345678'
                })
                object_list.append(resource_object)
            return object_list

        Vrops.get_nsxt_mgmt_cluster = MagicMock(return_value=(create_resource_objects("ManagementCluster"), 200, 0.282561))
        Vrops.get_nsxt_mgmt_nodes = MagicMock(return_value=(create_resource_objects("ManagementNode"), 200, 0.282561))
        Vrops.get_nsxt_mgmt_service = MagicMock(return_value=(create_resource_objects("ManagementService"), 200, 0.282561))
        Vrops.get_nsxt_transport_zone = MagicMock(return_value=(create_resource_objects("TransportZone"), 200, 0.282561))
        Vrops.get_nsxt_transport_node = MagicMock(return_value=(create_resource_objects("TransportNode"), 200, 0.282561))
        Vrops.get_nsxt_logical_switch = MagicMock(return_value=(create_resource_objects("LogicalSwitch"), 200, 0.282561))
        Vrops.get_datacenter = MagicMock(return_value=(create_resource_objects("Datacenter"), 200, 0.282561))
        Vrops.get_cluster = MagicMock(return_value=(create_resource_objects("ClusterComputeResource"), 200, 0.282561))
        Vrops.get_SDRS_cluster = MagicMock(return_value=(create_resource_objects("StoragePod"), 200, 0.282561))
        datastores = create_resource_objects("Datastore")
        for ds in datastores:
            ds.type = 'other'
        Vrops.get_datastores = MagicMock(return_value=(datastores, 200, 0.282561))
        Vrops.get_hosts = MagicMock(return_value=(create_resource_objects("HostSystem"), 200, 0.282561))
        Vrops.get_vms = MagicMock(return_value=(create_resource_objects("VirtualMachine"), 200, 0.282561))
        Vrops.get_dis_virtual_switch = MagicMock(return_value=(create_resource_objects("VmwareDistributedSwitch"), 200, 0.282561))
        Vrops.get_vcops_instances = MagicMock(return_value=(create_resource_objects("vcops_object"), 200, 0.282561))
        Vrops.get_sddc_instances = MagicMock(return_value=(create_resource_objects("sddc_object"), 200, 0.282561))

        Vrops.get_project_ids = MagicMock(return_value=[{"3628-93a1-56e84634050814": "0815"},
                                                        {"7422-91h7-52s842060815": "0815"},
                                                        {"5628-9ba1-55e847050815": "internal"}])
        Vrops.get_alertdefinitions = MagicMock(return_value={'id': 'test-id', 'name': 'test-alert',

                                                             'symptoms': [{'name': 'test_symptom',
                                                                           'state': 'test-state'}],
                                                             'recommendation': [{'id': 'test-re',
                                                                                 'description': 'test-description'}]})
        Vrops.get_service_states = MagicMock(return_value=[
            {'service': [{'details': 'Success, Service LOCATOR is running and responding',
                          'health': 'OK',
                          'name': 'LOCATOR',
                          'startedOn': 1702541189387,
                          'uptime': 6412774450},
                         {'details': 'Success, Service ANALYTICS is running and responding',
                          'health': 'OK',
                          'name': 'ANALYTICS',
                          'startedOn': 1702541205556,
                          'uptime': 6412762377},
                         {'details': 'Success, Service COLLECTOR is running and responding',
                          'health': 'OK',
                          'name': 'COLLECTOR',
                          'startedOn': 1702541203086,
                          'uptime': 6412760790},
                         {'details': 'Success, Service API is running and responding',
                          'health': 'OK',
                          'name': 'API',
                          'startedOn': 1702541204544,
                          'uptime': 6412759317},
                         {'details': 'Success, Service CASA is running and responding',
                          'health': 'OK',
                          'name': 'CASA',
                          'startedOn': 1702541071734,
                          'uptime': 6412892126},
                         {'details': 'Success, Service ADMINUI is running and responding',
                          'health': 'OK',
                          'name': 'ADMINUI',
                          'startedOn': 1702541195420,
                          'uptime': 6412768497},
                         {'details': 'Success, Service UI is running and responding',
                          'health': 'OK',
                          'name': 'UI',
                          'startedOn': 1702541195420,
                          'uptime': 6412768503}]}, 200, 0.282561])

        thread = Thread(target=InventoryBuilder, args=(self.target, 8000, 180))
        thread.daemon = True
        thread.start()

        for collector in self.metrics_yaml.keys():
            print("\nTesting " + collector)
            class_module = importlib.import_module(f'collectors.{collector}')
            collector_instance = class_module.__getattribute__(collector)()

            if "Stats" in collector:
                multiple_metrics_generated = list()
                for metric in self.collector_config[collector]:
                    multiple_metrics_generated.append(
                        {"resourceId": "7422-91h7-52s842060815", "stat-list": {"stat": [
                            {"timestamps": [1582797716394], "statKey": {"key": metric['key']}, "data": [88.0]}]}})
                    multiple_metrics_generated.append(
                        {"resourceId": "3628-93a1-56e84634050814", "stat-list": {"stat": [
                            {"timestamps": [1582797716394], "statKey": {"key": metric['key']}, "data": [44.0]}]}})
                    multiple_metrics_generated.append(
                        {"resourceId": "5628-9ba1-55e847050815", "stat-list": {"stat": [
                            {"timestamps": [1582797716394], "statKey": {"key": metric['key']}, "data": [55.0]}]}})
                Vrops.get_latest_stats_multiple = MagicMock(return_value=(multiple_metrics_generated, 200, 0.5))

            if "Properties" in collector:
                multiple_metrics_generated = list()
                for metric in self.collector_config[collector]:
                    multiple_metrics_generated.append(
                        {"resourceId": "7422-91h7-52s842060815", "property-contents": {
                            "property-content": [
                                {"timestamps": [1582797716394], "statKey": metric['key'],
                                 "data": [88.0]}]}})
                    multiple_metrics_generated.append(
                        {"resourceId": "3628-93a1-56e84634050814", "property-contents": {
                            "property-content": [
                                {"timestamps": [1582797716394], "statKey": metric['key'],
                                 "values": ["test"]}]}})
                    multiple_metrics_generated.append(
                        {"resourceId": "5628-9ba1-55e847050815", "property-contents": {
                            "property-content": [
                                {"timestamps": [1582797716394], "statKey": metric['key'],
                                 "values": ["test"]}]}})
                Vrops.get_latest_properties_multiple = MagicMock(return_value=(multiple_metrics_generated, 200, 0.5))

            thread_list = list()

            # start prometheus server to provide metrics later on

            thread1 = Thread(target=run_prometheus_server, args=(self.random_prometheus_port, [collector_instance], mock_signal))
            thread1.daemon = True
            thread1.start()
            thread_list.append(thread1)
            # give grandpa thread some time to get prometheus started and run a couple intervals of InventoryBuilder
            time.sleep(3)

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

            metrics_yaml_list = self.metrics_yaml[collector]
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
