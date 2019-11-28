import sys
import os
import unittest
from unittest.mock import MagicMock
sys.path.append('../vrops-exporter')
sys.path.append('../vrops-exporter/tools')
sys.path.append('../vrops-exporter/modules')
from threading import Thread
from vrops_exporter import run_prometheus_server
import http.client
from tools.YamlRead import YamlRead
from VropsCollector import VropsCollector

class TestCollectors(unittest.TestCase):
    USER        = os.getenv('USER')
    PASSWORD    = os.getenv('PASSWORD')
    PORT        = int(os.getenv('PORT'))
    TARGET      = os.getenv('TARGET')

    def test_collector_metrics(self):
        #MagicMock get_modules to just test one module at a time

        #check if we have all metrics from test/metrics
        metrics_yaml = YamlRead('tests/metrics.yaml').run()
        print(metrics_yaml)
        #test every module all alone
        for collector in metrics_yaml.keys():
            print() #nicer output
            print("Testing " + collector)
            VropsCollector.get_modules = MagicMock(return_value=('/vrops-exporter/module', [collector]))

            #start prometheus server to provide metrics later on
            thread = Thread(target=run_prometheus_server, args=(self.PORT,))
            thread.daemon = True
            thread.start()
            
            c = http.client.HTTPConnection("localhost:9160")
            c.request("GET", "/?target=testhost.test")
            r = c.getresponse()
            
            self.assertEqual(r.status, 200, "HTTP server return code should be 200")
            self.assertEqual(r.reason, "OK", "HTTP status should be OK")

            data = r.read().decode()
            data_array = data.split('\n')
            # metrics = dict()
            # metrics['metrics'] = list()
            metrics = list()
            for entry in data_array:
                if entry.startswith('#'):
                    continue
                split_entry = entry.split()
                if len(split_entry) != 2:
                    continue
                # metrics.append({ split_entry[0] : split_entry[1] })
                metrics.append({ 'metric' : split_entry[0],
                                 'value'  : split_entry[1] })
            

            # 2 things
            # check if all metrics from yaml are here
            print("list1")
            print(metrics)
            print("list2")
            print(metrics_yaml[collector]['metrics'])
            # set(metrics.keys()).intersection(metrics_yaml[collector]['metrics'])

            list_test = metrics
            list_yaml = metrics_yaml[collector]['metrics']



            # for single_metric in metrics_yaml[collector]['metrics']:
             

            # check if there are more metrics being produced and there is no test?!

            thread.join(timeout=0)
            #increase to not run into locks
            self.PORT += 1

if __name__ == '__main__':
    unittest.main()
