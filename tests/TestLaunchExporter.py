import sys
import os
import unittest
import json

sys.path.append('.')
from unittest import TestCase
from exporter import parse_params
from pathlib import Path


class TestLaunchExporter(TestCase):

    # test with debug option on
    def test_with_cli_params_1(self):
        sys.argv = ['prog', '-u', 'testuser', '-p', 'testpw31!', '-o', '1234', '-d']
        parse_params()
        self.assertEqual(os.getenv('USER'), 'testuser', 'The user was not set correctly!')
        self.assertEqual(os.getenv('PASSWORD'), 'testpw31!', 'The password was not set correctly!')
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('DEBUG'), '1', 'Debug was not set correctly!')

    # test with debug option off
    def test_with_cli_params_2(self):
        os.environ.clear()
        sys.argv = ['prog', '--user', 'testuser', '--password', 'testpw31!', '--port', '1234']
        parse_params()
        self.assertEqual(os.getenv('USER'), 'testuser', 'The user was not set correctly!')
        self.assertEqual(os.getenv('PASSWORD'), 'testpw31!', 'The password was not set correctly!')
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('DEBUG'), '0', 'Debug was not set correctly')

    def test_with_cli_and_env_params(self):
        sys.argv = ['prog', '--user', 'cli_testuser', '--password', 'testpw31!', '--port', '1234', "--debug"]
        os.environ['USER'] = 'env_testuser'
        os.environ['PASSWORD'] = 'testps31!_2'
        os.environ['PORT'] = '1123'
        parse_params()
        # cli params preferred
        self.assertEqual(os.getenv('USER'), 'cli_testuser', 'The user was not set correctly!')
        self.assertEqual(os.getenv('PASSWORD'), 'testpw31!', 'The password was not set correctly!')
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')

    def test_with_bogus_options(self):
        os.environ.clear()
        sys.argv = ['prog', '-z', 'foo', '-v', 'bar', '-w', 'bar']
        with self.assertRaises(SystemExit) as se:
            parse_params()
        self.assertEqual(se.exception.code, 2, 'PORT, USER or PASSWORD are not set properly in ENV or command line!')

    def test_without_params(self):
        os.environ.clear()
        sys.argv = ['prog']
        with self.assertRaises(SystemExit) as se:
            parse_params()
        self.assertEqual(se.exception.code, 0, 'PORT, USER or PASSWORD are not set in ENV or command line!')

    def test_for_atlas_configfile(self):
        os.environ.clear()
        netbox_json_file = Path("./atlas/netbox.json")
        self.assertTrue(netbox_json_file.is_file(), msg="configfile does not exist")
        try:
            with open('./atlas/netbox.json') as json_file:
                netbox_json = json.load(json_file)
        except (ValueError, json.decoder.JSONDecodeError):
            raise AssertionError("No valid JSON file provided")
        
        if netbox_json:
            for target in netbox_json:
                self.assertTrue("job" in target['labels'],
                                msg="Key 'job' needed in InventoryBuilder are missing")
                self.assertTrue("server_name" in target['labels'],
                                msg="Key 'server_name' needed in InventoryBuilder are missing")
                self.assertTrue("vrops" in target['labels']['job'],
                                msg="There is no target 'vrops' in atlas configfile")


if __name__ == '__main__':
    unittest.main()
