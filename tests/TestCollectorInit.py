import sys
sys.path.append('.')
import os
import unittest
from unittest import TestCase
from unittest.mock import call, patch, MagicMock
import importlib
import collectors.HostSystemStatsCollector
from exporter import initialize_collector_by_name




class TestCollectorInitialization(TestCase):
    os.environ.setdefault('TARGET', 'testhost.test')
    collectors.HostSystemStatsCollector.BaseCollector.get_target_tokens = MagicMock(return_value={'testhost.test': '2ed214d52'})
    @patch('BaseCollector.BaseCollector.wait_for_inventory_data')
    def test_valid_collector2(self, mocked_wait):
        mocked_wait.return_value = None
        collector = initialize_collector_by_name('HostSystemStatsCollector')
        self.assertIsInstance(collector, collectors.HostSystemStatsCollector.HostSystemStatsCollector)

    @patch('builtins.print')
    def test_with_bogus_collector(self, mocked_print):
        collector = initialize_collector_by_name('BogusCollector')
        self.assertIsNone(collector)
        self.assertEqual(mocked_print.mock_calls, [call('No Collector "BogusCollector" defined. Ignoring...')])

    @patch('builtins.print')
    def test_with_invalid_collector(self, mocked_print):
        importlib.import_module = MagicMock(return_value=collectors.HostSystemStatsCollector)
        collector = initialize_collector_by_name('ClassNotDefinedCollector')
        self.assertIsNone(collector)
        self.assertEqual(mocked_print.mock_calls, [call('Unable to initialize "ClassNotDefinedCollector". Ignoring...')])


if __name__ == '__main__':
    unittest.main()
