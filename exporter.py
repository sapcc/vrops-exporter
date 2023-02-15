#!/usr/bin/env python3
import sys
import time
import os
import importlib
import requests
import logging
import random
import signal
from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY
from optparse import OptionParser
from tools.helper import yaml_read


def default_collectors():
    collector_config = yaml_read(os.environ['COLLECTOR_CONFIG']).get('default_collectors')
    return [collector for collector in collector_config] if collector_config else None


def parse_params(logger):
    # init logging here for setting the log level
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    ConsoleHandler = logging.StreamHandler()
    logger.addHandler(ConsoleHandler)
    ConsoleHandler.setFormatter(formatter)

    parser = OptionParser()
    parser.add_option("-o", "--port", help="specify exporter (exporter.py) or inventory serving port(inventory.py)",
                      action="store", dest="port")
    parser.add_option("-i", "--inventory", help="inventory service address", action="store", dest="inventory")
    parser.add_option("-v", "--v", help="logging all level except debug", action="store_true", dest="info",
                      default=False)
    parser.add_option("-d", "--vv", help="logging all level including debug", action="store_true", dest="debug",
                      default=False)
    parser.add_option("-c", "--collector", help="enable collector (use multiple times)", action="append",
                      dest="collectors")
    parser.add_option("-m", "--config", help="path to config to set default collectors, statkeys and properties for "
                                             "collectors", action="store", dest="config")
    parser.add_option("-t", "--target", help="define target vrops", action="store", dest="target")
    (options, args) = parser.parse_args()

    if options.inventory:
        os.environ['INVENTORY'] = options.inventory
    if options.info:
        logger.setLevel(logging.INFO)
        ConsoleHandler.setLevel(logging.INFO)
        logger.info('Starting exporter logging on INFO level')
    if options.debug:
        logger.setLevel(logging.DEBUG)
        ConsoleHandler.setLevel(logging.DEBUG)
        logger.debug('Starting exporter logging on DEBUG level')
    if not options.debug and not options.info:
        logger.setLevel(logging.WARNING)
        ConsoleHandler.setLevel(logging.WARNING)
        logger.warning('Starting exporter logging on WARNING, ERROR and CRITICAL level')
    if options.port:
        os.environ['PORT'] = options.port
    if options.config:
        os.environ['COLLECTOR_CONFIG'] = options.config
    if not options.collectors:
        logger.debug('Exporter using default collectors from config')
        options.collectors = default_collectors()
    if options.target:
        os.environ['TARGET'] = options.target

    if "PORT" not in os.environ and not options.port:
        logger.error('Cannot start, please specify port with ENV or -o')
        sys.exit(1)
    if "INVENTORY" not in os.environ and not options.inventory:
        logger.error('Cannot start, please specify inventory with ENV or -i')
        sys.exit(1)
    if "COLLECTOR_CONFIG" not in os.environ and not options.config:
        logger.error('Cannot start, please specify collector config with ENV or -m')
        sys.exit(1)
    if "TARGET" not in os.environ and not options.target:
        logger.error('Cannot start, please specify TARGET with ENV or -a')
        sys.exit(1)
    if not options.collectors:
        logger.error('Cannot start, no default collectors activated in config')
        sys.exit(1)

    return options


def run_prometheus_server(port, collectors, *args):
    start_http_server(int(port))
    for c in collectors:
        REGISTRY.register(c)
    signal.signal(signal.SIGTERM, exit_gracefully)
    while True:
        time.sleep(1)


def exit_gracefully(no, frm):
    logger.warning('SIGTERM received, shutting down gently.')
    for c in collectors:
        while c.collect_running:
            logger.debug(f'Waiting for {c.name} to finish current collect run.')
            time.sleep(1)
        logger.debug(f'Unregistering {c.name}')
        REGISTRY.unregister(c)
    sys.exit(0)


def initialize_collector_by_name(class_name, logger):
    try:
        class_module = importlib.import_module(f'collectors.{class_name}')
    except ModuleNotFoundError as e:
        print('No Collector "BogusCollector" defined. Ignoring...')
        logger.error(f'No Collector {class_name} defined. {e}')
        return None

    try:
        return class_module.__getattribute__(class_name)()
    except AttributeError as e:
        print('Unable to initialize "ClassNotDefinedCollector". Ignoring...')
        logger.error(f'Unable to initialize {class_name}. {e}')
        return None


if __name__ == '__main__':
    logger = logging.getLogger('vrops-exporter')
    options = parse_params(logger)
    global collectors
    collectors = list(map(lambda c: initialize_collector_by_name(c, logger), options.collectors))
    run_prometheus_server(int(os.environ['PORT']), collectors)
