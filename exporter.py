#!/usr/bin/python3
import sys
import time
import os
from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY #GaugeMetricFamily, REGISTRY, CounterMetricFamily
from optparse import OptionParser
from threading import Thread

# from VropsCollector import VropsCollector
from collectors.SampleCollector import SampleCollector
from collectors.HostSystemStatsCollector import HostSystemStatsCollector
from collectors.HostSystemPropertiesCollector import HostSystemPropertiesCollector
from collectors.DatastoreStatsCollector import DatastoreStatsCollector
from collectors.ClusterPropertiesCollector import ClusterPropertiesCollector 
from collectors.VMStatsCollector import VMStatsCollector
from collectors.VMPropertiesCollector import VMPropertiesCollector
from collectors.CollectorUp import CollectorUp
from collectors.ClusterStatsCollector import ClusterStatsCollector

def parse_params():
    parser = OptionParser()
    parser.add_option("-o", "--port", help="specify exporter (exporter.py) or inventory serving port(inventory.py)", action="store", dest="port")
    parser.add_option("-i", "--inventory", help="inventory service address", action="store", dest="inventory")
    parser.add_option("-d", "--debug", help="enable debug", action="store_true", dest="debug", default=False)
    (options, args) = parser.parse_args()

    if options.inventory:
        os.environ['INVENTORY'] = options.inventory
    if options.debug:
        os.environ['DEBUG'] = "1"
        print('DEBUG enabled')
    else:
        if 'DEBUG' not in os.environ.keys():
            os.environ['DEBUG'] = "0"
        else:
            print('DEBUG enabled')
    if options.port:
        os.environ['PORT'] = options.port

    if "PORT" not in os.environ and not options.port:
        print("Can't start, please specify port with ENV or -o")
        sys.exit(0)
    if "INVENTORY" not in os.environ and not options.inventory:
        print("Can't start, please specify inventory with ENV or -i")
        sys.exit(0)

    return options


def run_prometheus_server(port, collectors,  *args):
    start_http_server(int(port))
    for c in collectors:
        REGISTRY.register(c)
    while True:
        time.sleep(1)

if __name__ == '__main__':
    options = parse_params()
    collectors = [
                # SampleCollector(),
                ClusterStatsCollector(),
                ClusterPropertiesCollector(),
                HostSystemStatsCollector(),
                HostSystemPropertiesCollector(),
                DatastoreStatsCollector(),
                VMStatsCollector(),
                VMPropertiesCollector()
                # add new collectors above this line
                # CollectorUp()
            ]
    run_prometheus_server(int(os.environ['PORT']), collectors)
