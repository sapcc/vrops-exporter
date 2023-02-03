import sys

sys.path.append('.')
import os
import unittest
import logging
from unittest import TestCase
from unittest.mock import call, patch, MagicMock
import importlib
import collectors.HostSystemStatsCollector
from exporter import initialize_collector_by_name

logger = logging.getLogger('test-logger')


class TestCollectorInitialization(TestCase):
    print(f"Running TestCollectorInitialization")
    os.environ.setdefault('TARGET', "vrops-vcenter-test.company.com")
    collectors.HostSystemStatsCollector.StatsCollector.get_vrops_target = MagicMock(
        return_value='vrops-vcenter-test.company.com')
    collectors.HostSystemStatsCollector.StatsCollector.read_collector_config = MagicMock(return_value={})

    @patch('BaseCollector.BaseCollector.wait_for_inventory_data')
    def test_valid_collector2(self, mocked_wait):
        mocked_wait.return_value = None
        collector = initialize_collector_by_name('HostSystemStatsCollector', logger)
        self.assertIsInstance(collector, collectors.HostSystemStatsCollector.HostSystemStatsCollector)

    @patch('builtins.print')
    def test_with_bogus_collector(self, mocked_print):
        collector = initialize_collector_by_name('BogusCollector', logger)
        self.assertIsNone(collector)
        self.assertEqual(mocked_print.mock_calls, [call('No Collector "BogusCollector" defined. Ignoring...')])

    @patch('builtins.print')
    def test_with_invalid_collector(self, mocked_print):
        importlib.import_module = MagicMock(return_value=collectors.HostSystemStatsCollector)
        collector = initialize_collector_by_name('ClassNotDefinedCollector', logger)
        self.assertIsNone(collector)
        self.assertEqual(mocked_print.mock_calls,
                         [call('Unable to initialize "ClassNotDefinedCollector". Ignoring...')])


if __name__ == '__main__':
    unittest.main()
