import sys

sys.path.append('.')
from unittest import TestCase
from exporter import parse_params
from exporter import default_collectors
import os
import unittest
import logging


logger = logging.getLogger('test-logger')
# Level         Numeric value
# CRITICAL      50
# ERROR         40
# WARNING       30
# INFO          20
# DEBUG         10
# NOTSET        0


class TestLaunchExporter(TestCase):
    print(f"Running TestLaunchExporter")

    # test with debug option on
    def test_with_cli_params_1(self):
        sys.argv = ['prog', '-o', '1234', '-i', 'inventory.some.url', '-m', 'tests/collector_config.yaml', '-t',
                    'vrops-vcenter-test.company.com', '-d']
        parse_params(logger)
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('INVENTORY'), 'inventory.some.url', 'Inventory was not set correctly')
        self.assertEqual(os.getenv('COLLECTOR_CONFIG'), 'tests/collector_config.yaml', 'Config was not set')
        self.assertEqual(os.getenv('TARGET'), 'vrops-vcenter-test.company.com', 'Target was not set')
        self.assertEqual(logger.level, 10)

    # test with debug option off
    def test_with_cli_params_2(self):
        os.environ.clear()
        sys.argv = ['prog', '--port', '1234', '-i', 'inventory.some.url', '-m', 'tests/collector_config.yaml', '-t',
                    'vrops-vcenter-test.company.com']
        parse_params(logger)
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('INVENTORY'), 'inventory.some.url', 'Inventory was not set correctly')
        self.assertEqual(os.getenv('COLLECTOR_CONFIG'), 'tests/collector_config.yaml', 'Config was not set')
        self.assertEqual(os.getenv('TARGET'), 'vrops-vcenter-test.company.com', 'Target was not set')
        self.assertEqual(logger.level, 30)

    def test_with_cli_and_env_params(self):
        sys.argv = ['prog', '--port', '1234', '-i', 'inventory.some.url', '-m',
                    'tests/collector_config.yaml', '-t', 'vrops-vcenter-test.company.com', '-v']
        os.environ['PORT'] = '1123'
        os.environ['INVENTORY'] = 'inventory.wedontwantthis.url'
        os.environ['COLLECTOR_CONFIG'] = 'tests/other_config.yaml'
        os.environ['TARGET'] = 'Othervrops-vcenter-test.company.com'
        parse_params(logger)
        # cli params preferred
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('INVENTORY'), 'inventory.some.url', 'Inventory was not set correctly')
        self.assertEqual(os.getenv('COLLECTOR_CONFIG'), 'tests/collector_config.yaml', 'Config was not set')
        self.assertEqual(os.getenv('TARGET'), 'vrops-vcenter-test.company.com', 'Target was not set')
        self.assertEqual(logger.level, 20)

    # test use default collectors when nothing is specified
    def test_with_no_collector(self):
        sys.argv = ['prog', '--port', '1234', '-i', 'inventory.some.url', '-m',
                    'tests/collector_config.yaml', '-t', 'vrops-vcenter-test.company.com']
        options = parse_params(logger)
        self.assertEqual(options.collectors, default_collectors(), 'Default collector list does not match the default')

    # test with only one collector enabled
    def test_with_one_collector(self):
        sys.argv = ['prog', '--port', '1234', '-i', 'inventory.some.url', '-c', 'VMStatsCollector', '-m',
                    'tests/collector_config.yaml', '-t', 'vrops-vcenter-test.company.com']
        options = parse_params(logger)
        self.assertEqual(options.collectors, ['VMStatsCollector'],
                         'Collector list does not match given single collector')

    # test multiple enabled collectors
    def test_with_multiple_collector(self):
        sys.argv = ['prog', '--port', '1234', '-i', 'inventory.some.url', '-c', 'VMStatsCollector', '-m',
                    'tests/collector_config.yaml', '-c', 'VMPropertiesCollector', '-t', 'vrops-vcenter-test.company.com']
        options = parse_params(logger)
        self.assertEqual(options.collectors, ['VMStatsCollector', 'VMPropertiesCollector'],
                         'Collector list does not match given multiple collectors')

    def test_with_bogus_options(self):
        os.environ.clear()
        sys.argv = ['prog', '-z', 'foo', '-a', 'bar', '-w', 'bar']
        with self.assertRaises(SystemExit) as se:
            parse_params(logger)
        self.assertEqual(se.exception.code, 2, 'PORT or INVENTORY are not set properly in ENV or command line!')

    def test_without_params(self):
        os.environ.clear()
        sys.argv = ['prog']
        with self.assertRaises(KeyError) as e:
            parse_params(logger)
        self.assertEqual(str(e.exception.args), "('COLLECTOR_CONFIG',)", 'no collector config file provided!')


if __name__ == '__main__':
    unittest.main()
