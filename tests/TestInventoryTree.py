import sys
sys.path.append('.')
import unittest
from unittest import TestCase
from unittest.mock import call, patch, MagicMock
import requests
import resource_mock
from InventoryBuilder import InventoryBuilder
from tools.Resources import Resources

class InventoryBuilderMock(InventoryBuilder):
    def __init__(self, json, port):
        self.json = json
        self.port = int(port)
        self.vcenter_dict = dict()
        self.target_tokens = dict()
        self.iterated_inventory = dict()
        self.successful_iteration_list = [0]
        
        self.iteration = 1
        self.iterated_inventory[str(self.iteration)] = dict()

class TestIntoryTree(TestCase):
    def setUp(self):
        self.subject = InventoryBuilderMock("/path/to/json", 80)

        Resources.get_token = MagicMock(return_value='a-token')
        requests.get = MagicMock(side_effect=resource_mock.mock_vrops_api)

        self.subject.query_vrops('vrops.example.local')

    def test_vcenters(self):
        res = self.subject.get_vcenters()
        self.assertEqual(len(res), 1)
        self.assertEqual(list(res.keys()), ['vcenter-uuid'])

    def test_datacenters(self):
        res = self.subject.get_datacenters()
        self.assertEqual(len(res), 4)
        self.assertEqual(list(res.keys()), ['Custom DC 1', 'Custom DC 2', 'DC 1', 'DC 2'])

    def test_clusters(self):
        res = self.subject.get_clusters()
        self.assertEqual(len(res), 3)
        self.assertCountEqual(list(res.keys()), ['cluster-uuid1', 'cluster-uuid2', 'cluster-uuid3'])

    def test_duplicate_cluster_has_normal_dc_as_parent(self):
        res = self.subject.get_clusters()
        self.assertEqual(res['cluster-uuid3']['parent_dc_uuid'], 'dc-uuid2')

    def test_hosts(self):
        res = self.subject.get_hosts()
        self.assertEqual(len(res), 2)
        self.assertEqual(list(res.keys()), ['host-uuid1', 'host-uuid2'])

    def test_datastores(self):
        res = self.subject.get_datastores()
        self.assertEqual(len(res), 2)
        self.assertEqual(list(res.keys()), ['ds-uuid1', 'ds-uuid2'])

    def test_vms(self):
        res = self.subject.get_vms()
        self.assertEqual(len(res), 2)
        self.assertEqual(list(res.keys()), ['vm-uuid1', 'vm-uuid2'])

if __name__ == '__main__':
    unittest.main()
