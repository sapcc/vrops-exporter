import sys
sys.path.append('.')
import os
import http.client
import unittest
import time
import json
from random import randint
from threading import Thread
from InventoryBuilder import InventoryBuilder


class TestNetboxTargets(unittest.TestCase):

    def test_enviroment(self):
         self.assertTrue(os.getenv('ATLAS'), 'no ATLAS config file set')
         self.assertTrue(os.getenv('SLEEP'), 'no SLEEP time for inventory builder set')

    def test_new_targets_from_netbox(self):
        print("chosen path to netbox file:", os.environ["ATLAS"])
        os.environ['PASSWORD'] = "Foo"
        os.environ['USER'] = "bar"
        os.environ['DEBUG'] = "0"
        port = randint(8000, 8050)
        path_to_netbox_file = os.environ['ATLAS']
        sleep_time = os.environ["SLEEP"]
        thread = Thread(target=InventoryBuilder, args=(path_to_netbox_file, port, sleep_time))
        thread.daemon = True
        thread.start()

        while True:
            with open(path_to_netbox_file) as json_file:
                netbox_json = json.load(json_file)
            vrops_list = [target['labels']['server_name'] for target in netbox_json if
                          target['labels']['job'] == "vrops"]
            print("querying vrops_list on port", str(port))
            c = http.client.HTTPConnection("localhost:" + str(port))
            c.request("GET", "/vrops_list")
            r = c.getresponse()
            self.assertEqual(r.status, 200, "HTTP server return code should be 200")
            self.assertEqual(r.reason, "OK", "HTTP status should be OK")

            data = r.read().decode()
            self.assertEqual(json.dumps(vrops_list), data, "New targets where not taken into account!")
            r.close()
            c.close()
            print(data, "==", json.dumps(vrops_list))
            print("Test for targets OK! \nRelaxing together with inventory...")
            time.sleep(int(sleep_time)+20)
