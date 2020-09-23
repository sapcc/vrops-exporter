#!/usr/bin/python3
import sys
import time
import os
import importlib
from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY
from optparse import OptionParser
from tools.helper import yaml_read


def default_collectors():
    return [i for i in yaml_read(os.environ['CONFIG'])['default_collectors']]

def parse_params():
    parser = OptionParser()
    parser.add_option("-o", "--port", help="specify exporter (exporter.py) or inventory serving port(inventory.py)",
                      action="store", dest="port")
    parser.add_option("-i", "--inventory", help="inventory service address", action="store", dest="inventory")
    parser.add_option("-d", "--debug", help="enable debug", action="store_true", dest="debug", default=False)
    parser.add_option("-c", "--collector", help="enable collector (use multiple times)", action="append",
                      dest="collectors")
    parser.add_option("-m", "--config", help="path to config to set default collectors, statkeys and properties for "
                                             "collectors", action="store", dest="config")
    parser.add_option("-t", "--target", help="define target vcenter", action="store", dest="target")
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
    if options.config:
        os.environ['CONFIG'] = options.config
    if not options.collectors:
        options.collectors = default_collectors()
    if options.port:
        os.environ['TARGET'] = options.target


    if "PORT" not in os.environ and not options.port:
        print("Can't start, please specify port with ENV or -o")
        sys.exit(0)
    if "INVENTORY" not in os.environ and not options.inventory:
        print("Can't start, please specify inventory with ENV or -i")
        sys.exit(0)
    if "CONFIG" not in os.environ and not options.config:
        print("Can't start, please specify statkeys with ENV or -m")
        sys.exit(0)

    return options


def run_prometheus_server(port, collectors, *args):
    start_http_server(int(port))
    for c in collectors:
        REGISTRY.register(c)
    while True:
        time.sleep(1)


def initialize_collector_by_name(class_name):
    try:
        class_module = importlib.import_module('collectors.%s' % (class_name))
    except ModuleNotFoundError:
        print('No Collector "%s" defined. Ignoring...' % (class_name))
        return None

    try:
        return getattr(class_module, class_name)()
    except AttributeError:
        print('Unable to initialize "%s". Ignoring...' % (class_name))
        return None


if __name__ == '__main__':
    options = parse_params()
    collectors = list(map(lambda c: initialize_collector_by_name(c), options.collectors))
    run_prometheus_server(int(os.environ['PORT']), collectors)
