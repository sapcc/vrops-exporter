import sys
import os
import unittest

sys.path.append('.')
from unittest import TestCase
from unittest.mock import call, patch, MagicMock
from exporter import parse_params
from exporter import default_collectors


class TestLaunchExporter(TestCase):

    # test with debug option on
    def test_with_cli_params_1(self):
        sys.argv = ['prog', '-o', '1234', '-d', '-i', 'inventory.some.url']
        parse_params()
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('DEBUG'), '1', 'Debug was not set correctly!')
        self.assertEqual(os.getenv('INVENTORY'), 'inventory.some.url', 'Inventory was not set correctly')

    # test with debug option off
    def test_with_cli_params_2(self):
        os.environ.clear()
        sys.argv = ['prog', '--port', '1234', '-i', 'inventory.some.url']
        parse_params()
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('DEBUG'), '0', 'Debug was not set correctly')
        self.assertEqual(os.getenv('INVENTORY'), 'inventory.some.url', 'Inventory was not set correctly')

    def test_with_cli_and_env_params(self):
        sys.argv = ['prog', '--port', '1234', "--debug", '-i', 'inventory.some.url']
        os.environ['PORT'] = '1123'
        os.environ['INVENTORY'] = 'inventory.wedontwantthis.url'
        parse_params()
        # cli params preferred
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('INVENTORY'), 'inventory.some.url', 'Inventory was not set correctly')

    # test use default collectors when nothing is specified
    def test_with_no_collector(self):
        sys.argv = ['prog', '--port', '1234', '-i', 'inventory.some.url']
        options = parse_params()
        self.assertEqual(options.collectors, default_collectors(), 'Default collector list does not match the default')

    # test with only one collector enabled
    def test_with_one_collector(self):
        sys.argv = ['prog', '--port', '1234', '-i', 'inventory.some.url', '-c', 'VMStatsCollector']
        options = parse_params()
        self.assertEqual(options.collectors, ['VMStatsCollector'], 'Default collector list does not match the default')

    # test multiple enabled collectors
    def test_with_multiple_collector(self):
        sys.argv = ['prog', '--port', '1234', '-i', 'inventory.some.url', '-c', 'VMStatsCollector', '-c', 'VMPropertiesCollector']
        options = parse_params()
        self.assertEqual(options.collectors, ['VMStatsCollector', 'VMPropertiesCollector'], 'Default collector list does not match the default')

    def test_with_bogus_options(self):
        os.environ.clear()
        sys.argv = ['prog', '-z', 'foo', '-a', 'bar', '-w', 'bar']
        with self.assertRaises(SystemExit) as se:
            parse_params()
        self.assertEqual(se.exception.code, 2, 'PORT or INVENTORY are not set properly in ENV or command line!')

    def test_without_params(self):
        os.environ.clear()
        sys.argv = ['prog']
        with self.assertRaises(SystemExit) as se:
            parse_params()
        self.assertEqual(se.exception.code, 0, 'PORT or INVENTORY are not set properly in ENV or command line!')

import collectors.CollectorUp
import importlib
from exporter import initialize_collector_by_name
class TestCollectorInitialization(TestCase):
    def test_valid_collector(self):
        collector = initialize_collector_by_name('CollectorUp')
        self.assertIsInstance(collector, collectors.CollectorUp.CollectorUp)

    @patch('builtins.print')
    def test_with_bogus_collector(self, mocked_print):
        collector = initialize_collector_by_name('BogusCollector')
        self.assertIsNone(collector)
        self.assertEqual(mocked_print.mock_calls, [call('No Collector "BogusCollector" defined. Ignoring...')])

    @patch('builtins.print')
    def test_with_invalid_collector(self, mocked_print):
        importlib.import_module = MagicMock(return_value=collectors.CollectorUp)
        collector = initialize_collector_by_name('ClassNotDefinedCollector')
        self.assertIsNone(collector)
        self.assertEqual(mocked_print.mock_calls, [call('Unable to initialize "ClassNotDefinedCollector". Ignoring...')])

if __name__ == '__main__':
    unittest.main()
