import sys

sys.path.append('.')
from unittest import TestCase
from inventory import parse_params
import os
import unittest
import logging

logger = logging.getLogger('test-logger')


class TestLaunchExporter(TestCase):
    # test with debug option on
    def test_with_cli_params_1(self):
        sys.argv = ['prog', '-u', 'testuser', '-p', 'testpw31!', '-o', '1234',
                    '-a', '/path/to/atlas.yaml', '-l', '-s', '180']
        parse_params(logger)
        self.assertEqual(os.getenv('USER'), 'testuser', 'The user was not set correctly!')
        self.assertEqual(os.getenv('PASSWORD'), 'testpw31!', 'The password was not set correctly!')
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('ATLAS'), '/path/to/atlas.yaml', 'Atlas was not set correctly')
        self.assertEqual(os.getenv('LOOPBACK'), '1', 'Loopback was not set correctly')
        self.assertEqual(os.getenv('SLEEP'), '180', 'Sleep time was not set correctly')

    # test with debug option off
    def test_with_cli_params_2(self):
        os.environ.clear()
        sys.argv = ['prog', '--user', 'testuser', '--password', 'testpw31!', '--port', '1234',
                    '-a', '/path/to/atlas.yaml', '-l', '--sleep', '180']
        parse_params(logger)
        self.assertEqual(os.getenv('USER'), 'testuser', 'The user was not set correctly!')
        self.assertEqual(os.getenv('PASSWORD'), 'testpw31!', 'The password was not set correctly!')
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('ATLAS'), '/path/to/atlas.yaml', 'Atlas was not set correctly')
        self.assertEqual(os.getenv('LOOPBACK'), '1', 'Loopback was not set correctly')
        self.assertEqual(os.getenv('SLEEP'), '180', 'Sleep time was not set correctly')

    def test_with_cli_and_env_params(self):
        sys.argv = ['prog', '--user', 'cli_testuser', '--password', 'testpw31!',
                    '--port', '1234', '-a', '/path/to/atlas.yaml', '-l', '-s', '180']
        os.environ['USER'] = 'env_testuser'
        os.environ['PASSWORD'] = 'testps31!_2'
        os.environ['PORT'] = '1123'
        os.environ['ATLAS'] = '/wrong/path/to/atlas.yaml'
        os.environ['LOOPBACK'] = '0'
        os.environ['SLEEP'] = '199'
        parse_params(logger)
        # cli params preferred
        self.assertEqual(os.getenv('USER'), 'cli_testuser', 'The user was not set correctly!')
        self.assertEqual(os.getenv('PASSWORD'), 'testpw31!', 'The password was not set correctly!')
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('ATLAS'), '/path/to/atlas.yaml', 'Atlas was not set correctly')
        self.assertEqual(os.getenv('LOOPBACK'), '1', 'Loopback was not set correctly')
        self.assertEqual(os.getenv('SLEEP'), '180', 'Sleep time was not set correctly')

    def test_with_bogus_options(self):
        os.environ.clear()
        sys.argv = ['prog', '-z', 'foo', '-x', 'bar', '-w', 'bar']
        with self.assertRaises(SystemExit) as se:
            parse_params(logger)
        self.assertEqual(se.exception.code, 2, 'PORT, USER, ATLAS or PASSWORD are not set properly in ENV or command '
                                               'line!')

    def test_without_params(self):
        os.environ.clear()
        sys.argv = ['prog']
        with self.assertRaises(SystemExit) as se:
            parse_params(logger)
        self.assertEqual(se.exception.code, 0, 'PORT, USER, ATLAS or PASSWORD are not set in ENV or command line!')


if __name__ == '__main__':
    unittest.main()
