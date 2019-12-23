import sys
import os
import unittest

sys.path.append('.')
from unittest import TestCase
from vrops_exporter import parse_params


class TestLaunchExporter(TestCase):
    def test_with_cli_params_1(self):
        sys.argv = ['prog', '-u', 'testuser', '-p', 'testpw31!', '-o', '1234']
        parse_params()
        self.assertEqual(os.getenv('USER'), 'testuser', 'The user was not set correctly!')
        self.assertEqual(os.getenv('PASSWORD'), 'testpw31!', 'The password was not set correctly!')
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('DEBUG'), '0', 'Debug was not set correctly!')

    def test_with_cli_params_2(self):
        sys.argv = ['prog', '--user', 'testuser', '--password', 'testpw31!', '--port', '1234']
        parse_params()
        self.assertEqual(os.getenv('USER'), 'testuser', 'The user was not set correctly!')
        self.assertEqual(os.getenv('PASSWORD'), 'testpw31!', 'The password was not set correctly!')
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('DEBUG'), '0', 'Debug was not set correctly!')

    def test_with_cli_and_env_params(self):
        sys.argv = ['prog', '--user', 'testuser', '--password', 'testpw31!', '--port', '1234', "--debug"]
        os.environ['USER'] = 'testuser_2'
        os.environ['PASSWORD'] = 'testps31!_2'
        os.environ['PORT'] = '1123'
        os.environ['DEBUG'] = '0'
        parse_params()
        # cli params win over env
        self.assertEqual(os.getenv('USER'), 'testuser', 'The user was not set correctly!')
        self.assertEqual(os.getenv('PASSWORD'), 'testpw31!', 'The password was not set correctly!')
        self.assertEqual(os.getenv('PORT'), '1234', 'The port was not set correctly!')
        self.assertEqual(os.getenv('DEBUG'), '1', 'Debug was not set correctly!')

    def test_with_wrong_params(self):
        os.environ['USEER'] = ' '
        os.environ['PASSWORRD'] = ' '
        os.environ['PORTE'] = ' '
        os.environ['DEBUUG'] = ' '
        with self.assertRaises(SystemExit) as se:
            parse_params()
        self.assertEqual(se.exception.code, 0, 'PORT, USER or PASSWORD is not set properly in ENV or command line!')

    def test_with_blank_params(self):
        sys.argv = ['prog', '-p', ' ', '-u', ' ', '-o', ' ']
        with self.assertRaises(SystemExit) as se:
            parse_params()
        self.assertEqual(se.exception.code, 0, 'PORT, USER or PASSWORD is not set properly in ENV or command line!')

    def test_without_params(self):
        sys.argv = ['prog']
        with self.assertRaises(SystemExit) as se:
            parse_params()
        self.assertEqual(se.exception.code, 0, 'PORT, USER or PASSWORD is not set in ENV or command line!')


if __name__ == '__main__':
    unittest.main()
