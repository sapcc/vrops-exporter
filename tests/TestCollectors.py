import sys

sys.path.append('.')
from unittest.mock import MagicMock
from threading import Thread
from exporter import run_prometheus_server
from tools.helper import yaml_read
from tools.Vrops import Vrops
from InventoryBuilder import InventoryBuilder
from BaseCollector import BaseCollector
from resources.Resourceskinds import *
from prometheus_client.core import REGISTRY
import unittest
import random
import http.client
import os
import time
import importlib


class TestCollectors(unittest.TestCase):
    os.environ.setdefault('TARGET', 'testhost.test')

    def test_environment(self):
        self.assertTrue(os.getenv('USER'), 'no dummy USER set')
        self.assertTrue(os.getenv('PASSWORD'), 'no dummy PASSWORD set')
        self.assertTrue(os.getenv('CONFIG'), 'no collector CONFIG set')
        self.assertTrue(os.getenv('TARGET'), 'no target set')

    def test_collector_metrics(self):
        self.metrics_yaml = yaml_read('tests/metrics.yaml')
        self.collector_config = yaml_read(os.environ['CONFIG'])
        self.target = os.getenv('TARGET')
        self.token = '2ed214d523-235f-h283-4566-6sf356124fd62::f234234-234'
        # every collector got to be tested in here
        self.random_prometheus_port = random.randrange(9000, 9700, 1)
        print("chosen testport: " + str(self.random_prometheus_port))

        BaseCollector.get_target_tokens = MagicMock(
            return_value={self.target: self.token})
        Vrops.get_token = MagicMock(return_value=("2ed214d523-235f-h283-4566-6sf356124fd62::f234234-234", 200))

        vc = Vcenter(target=self.target, token=self.token)
        vc.name = "vcenter1"
        vc.uuid = "3628-93a1-56e84634050814"

        nsxt_adapter1 = NSXTAdapterInstance(target=self.target, token=self.token)
        nsxt_adapter2 = NSXTAdapterInstance(target=self.target, token=self.token)
        nsxt_adapter1.name = "nsxt_adapter1"
        nsxt_adapter2.name = "nsxt_adapter2"
        nsxt_adapter1.uuid = nsxt_adapter2.uuid = "3628-93a1-56e84634050814"

        Vrops.get_adapter = MagicMock(return_value=None)
        Vrops.get_vcenter_adapter = MagicMock(return_value=([vc], 200))
        Vrops.get_nsxt_adapter = MagicMock(return_value=([nsxt_adapter1, nsxt_adapter2], 200))

        # test tool get_resources to create resource objects
        nsxt_mgmt_cluster1 = NSXTManagementCluster()
        nsxt_mgmt_cluster2 = NSXTManagementCluster()
        nsxt_mgmt_cluster3 = NSXTManagementCluster()
        nsxt_mgmt_cluster1.name = "nsxt_mgmt_cluster1"
        nsxt_mgmt_cluster2.name = "nsxt_mgmt_cluster2"
        nsxt_mgmt_cluster3.name = "nsxt_mgmt_cluster3"
        nsxt_mgmt_cluster1.uuid = "5628-9ba1-55e847050815"
        nsxt_mgmt_cluster2.uuid = "3628-93a1-56e84634050814"
        nsxt_mgmt_cluster3.uuid = "7422-91h7-52s842060815"
        nsxt_mgmt_cluster1.resourcekind = nsxt_mgmt_cluster2.resourcekind = \
            nsxt_mgmt_cluster3.resourcekind = "ManagementCluster"
        nsxt_mgmt_cluster1.parent = nsxt_mgmt_cluster2.parent = nsxt_mgmt_cluster3.parent = "3628-93a1-56e84634050814"

        nsxt_mgmt_node1 = NSXTManagementNode()
        nsxt_mgmt_node2 = NSXTManagementNode()
        nsxt_mgmt_node3 = NSXTManagementNode()
        nsxt_mgmt_node1.name = "nsxt_mgmt_node1"
        nsxt_mgmt_node2.name = "nsxt_mgmt_node2"
        nsxt_mgmt_node3.name = "nsxt_mgmt_node3"
        nsxt_mgmt_node1.uuid = "5628-9ba1-55e847050815"
        nsxt_mgmt_node2.uuid = "3628-93a1-56e84634050814"
        nsxt_mgmt_node3.uuid = "7422-91h7-52s842060815"
        nsxt_mgmt_node1.resourcekind = nsxt_mgmt_node2.resourcekind = nsxt_mgmt_node3.resourcekind = "ManagementNode"
        nsxt_mgmt_node1.parent = nsxt_mgmt_node2.parent = nsxt_mgmt_node3.parent = "3628-93a1-56e84634050814"

        nsxt_mgmt_service1 = NSXTManagementService()
        nsxt_mgmt_service2 = NSXTManagementService()
        nsxt_mgmt_service3 = NSXTManagementService()
        nsxt_mgmt_service1.name = "nsxt_mgmt_service1"
        nsxt_mgmt_service2.name = "nsxt_mgmt_service2"
        nsxt_mgmt_service3.name = "nsxt_mgmt_service3"
        nsxt_mgmt_service1.uuid = "5628-9ba1-55e847050815"
        nsxt_mgmt_service2.uuid = "3628-93a1-56e84634050814"
        nsxt_mgmt_service3.uuid = "7422-91h7-52s842060815"
        nsxt_mgmt_service1.resourcekind = nsxt_mgmt_service2.resourcekind = nsxt_mgmt_service3.resourcekind = "ManagementService"
        nsxt_mgmt_service1.parent = nsxt_mgmt_service2.parent = nsxt_mgmt_service3.parent = "3628-93a1-56e84634050814"

        dc1 = Datacenter()
        dc2 = Datacenter()
        dc3 = Datacenter()
        dc1.name = "datacenter1"
        dc2.name = "datacenter2"
        dc3.name = "datacenter3"
        dc1.internal_name = "datacenter-1"
        dc2.internal_name = "datacenter-2"
        dc3.internal_name = "datacenter-3"
        dc1.uuid = "3628-93a1-56e84634050814"
        dc2.uuid = "5628-9ba1-55e847050815"
        dc3.uuid = "7422-91h7-52s842060815"
        dc1.resourcekind = dc2.resourcekind = dc3.resourcekind = "Datacenter"
        dc1.parent = dc2.parent = dc3.parent = "3628-93a1-56e84634050814"

        cl1 = Cluster()
        cl2 = Cluster()
        cl3 = Cluster()
        cl1.name = "cluster1"
        cl2.name = "cluster2"
        cl3.name = "cluster3"
        cl1.internal_name = "domain-c1"
        cl2.internal_name = "domain-c2"
        cl3.internal_name = "domain-c3"
        cl1.uuid = "3628-93a1-56e84634050814"
        cl2.uuid = "5628-9ba1-55e847050815"
        cl3.uuid = "7422-91h7-52s842060815"
        cl1.resourcekind = cl2.resourcekind = cl3.resourcekind = "ClusterComputeResource"
        cl1.parent = cl2.parent = cl3.parent = "3628-93a1-56e84634050814"

        ds1 = Datastore()
        ds2 = Datastore()
        ds3 = Datastore()
        ds1.name = "vmfs_vc-w-0_p_ssd_bb091_001"
        ds2.name = "eph-bb112-1"
        ds3.name = "B121_Management_DS03"
        ds1.internal_name = "datastore-1"
        ds2.internal_name = "datastore-2"
        ds3.internal_name = "datastore-3"
        ds1.uuid = "3628-93a1-56e84634050814"
        ds2.uuid = "5628-9ba1-55e847050815"
        ds3.uuid = "7422-91h7-52s842060815"
        ds1.type = "vmfs_p_ssd"
        ds2.type = "ephemeral"
        ds3.type = "Management"
        ds1.resourcekind = ds2.resourcekind = ds3.resourcekind = "Datastore"
        ds1.parent = ds2.parent = ds3.parent = "7422-91h7-52s842060815"

        hs1 = Host()
        hs2 = Host()
        hs3 = Host()
        hs1.name = "hostsystem1"
        hs2.name = "hostsystem2"
        hs3.name = "hostsystem3"
        hs1.internal_name = "host-1234"
        hs2.internal_name = "host-2234"
        hs3.internal_name = "host-3234"
        hs1.uuid = "3628-93a1-56e84634050814"
        hs2.uuid = "5628-9ba1-55e847050815"
        hs3.uuid = "7422-91h7-52s842060815"
        hs1.resourcekind = hs2.resourcekind = hs3.resourcekind = "HostSystem"
        hs1.parent = hs2.parent = hs3.parent = "7422-91h7-52s842060815"

        vm1 = VirtualMachine()
        vm2 = VirtualMachine()
        vm3 = VirtualMachine()
        vm1.name = "vm1"
        vm2.name = "vm2"
        vm3.name = "vm3"
        vm1.internal_name = "vm-11234"
        vm2.internal_name = "vm-21234"
        vm3.internal_name = "vm-31234"
        vm1.uuid = "3628-93a1-56e84634050814"
        vm2.uuid = "5628-9ba1-55e847050815"
        vm3.uuid = "7422-91h7-52s842060815"
        vm1.resourcekind = vm2.resourcekind = vm3.resourcekind = "VirtualMachine"
        vm1.parent = vm2.parent = vm3.parent = "7422-91h7-52s842060815"

        Vrops.get_nsxt_mgmt_cluster = MagicMock(
            return_value=([nsxt_mgmt_cluster1, nsxt_mgmt_cluster2, nsxt_mgmt_cluster3], 200))
        Vrops.get_nsxt_mgmt_nodes = MagicMock(
            return_value=([nsxt_mgmt_node1, nsxt_mgmt_node2, nsxt_mgmt_node3], 200))
        Vrops.get_nsxt_mgmt_service = MagicMock(
            return_value=([nsxt_mgmt_service1, nsxt_mgmt_service2, nsxt_mgmt_service3], 200))
        Vrops.get_datacenter = MagicMock(
            return_value=([dc1, dc2, dc3], 200))
        Vrops.get_cluster = MagicMock(
            return_value=([cl1, cl2, cl3], 200))
        Vrops.get_datastores = MagicMock(
            return_value=([ds1, ds2, ds3], 200))
        Vrops.get_hosts = MagicMock(
            return_value=([hs1, hs2, hs3], 200))
        Vrops.get_vms = MagicMock(
            return_value=([vm1, vm2, vm3], 200))

        Vrops.get_latest_stat = MagicMock(return_value=1)
        Vrops.get_property = MagicMock(return_value="test_property")
        Vrops.get_project_ids = MagicMock(return_value=[{"3628-93a1-56e84634050814": "0815"},
                                                        {"7422-91h7-52s842060815": "0815"},
                                                        {"5628-9ba1-55e847050815": "internal"}])
        Vrops.get_alertdefinitions = MagicMock(return_value={'id': 'test-id', 'name': 'test-alert',
                                                             'symptoms': [{'name': 'test_symptom',
                                                                           'state': 'test-state'}],
                                                             'recommendation': [{'id': 'test-re',
                                                                                 'description': 'test-description'}]})

        thread = Thread(target=InventoryBuilder, args=('./tests/test.json', 8000, 180, 300))
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
                        {"resourceId": "3628-93a1-56e84634050814", "stat-list": {"stat": [
                            {"timestamps": [1582797716394], "statKey": {"key": metric['key']}, "data": [88.0]}]}})
                    multiple_metrics_generated.append(
                        {"resourceId": "3628-93a1-56e84634050814", "stat-list": {"stat": [
                            {"timestamps": [1582797716394], "statKey": {"key": metric['key']}, "data": [44.0]}]}})
                    multiple_metrics_generated.append(
                        {"resourceId": "3628-93a1-56e84634050814", "stat-list": {"stat": [
                            {"timestamps": [1582797716394], "statKey": {"key": metric['key']}, "data": [55.0]}]}})
                Vrops.get_latest_stats_multiple = MagicMock(return_value=(multiple_metrics_generated, 200, 0.5))

            if "Properties" in collector:
                multiple_metrics_generated = list()
                for metric in self.collector_config[collector]:
                    multiple_metrics_generated.append(
                        {"resourceId": "3628-93a1-56e84634050814", "property-contents": {
                            "property-content": [
                                {"timestamps": [1582797716394], "statKey": metric['key'],
                                 "data": [88.0]}]}})
                    multiple_metrics_generated.append(
                        {"resourceId": "3628-93a1-56e84634050814", "property-contents": {
                            "property-content": [
                                {"timestamps": [1582797716394], "statKey": metric['key'],
                                 "values": ["test"]}]}})
                    multiple_metrics_generated.append(
                        {"resourceId": "3628-93a1-56e84634050814", "property-contents": {
                            "property-content": [
                                {"timestamps": [1582797716394], "statKey": metric['key'],
                                 "values": ["test"]}]}})
                Vrops.get_latest_properties_multiple = MagicMock(return_value=(multiple_metrics_generated, 200, 0.5))

            thread_list = list()

            # start prometheus server to provide metrics later on

            thread1 = Thread(target=run_prometheus_server, args=(self.random_prometheus_port, [collector_instance]))
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
