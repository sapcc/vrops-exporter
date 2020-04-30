import sys
import os
import unittest

sys.path.append('.')
from unittest import TestCase
from unittest.mock import call, patch, MagicMock
import importlib
import collectors.SampleCollector
from exporter import initialize_collector_by_name

class TestCollectorInitialization(TestCase):
    def test_valid_collector(self):
        collector = initialize_collector_by_name('SampleCollector')
        self.assertIsInstance(collector, collectors.SampleCollector.SampleCollector)

    @patch('builtins.print')
    def test_with_bogus_collector(self, mocked_print):
        collector = initialize_collector_by_name('BogusCollector')
        self.assertIsNone(collector)
        self.assertEqual(mocked_print.mock_calls, [call('No Collector "BogusCollector" defined. Ignoring...')])

    @patch('builtins.print')
    def test_with_invalid_collector(self, mocked_print):
        importlib.import_module = MagicMock(return_value=collectors.SampleCollector)
        collector = initialize_collector_by_name('ClassNotDefinedCollector')
        self.assertIsNone(collector)
        self.assertEqual(mocked_print.mock_calls, [call('Unable to initialize "ClassNotDefinedCollector". Ignoring...')])

if __name__ == '__main__':
    unittest.main()
