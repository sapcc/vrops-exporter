#!/usr/bin/python3
from InventoryBuilder import InventoryBuilder
from optparse import OptionParser
import sys
import os
import logging


def parse_params(logger):
    # init logging here for setting the log level
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    ConsoleHandler = logging.StreamHandler()
    logger.addHandler(ConsoleHandler)
    ConsoleHandler.setFormatter(formatter)

    parser = OptionParser()
    parser.add_option("-u", "--user", help="specify user to log in", action="store", dest="user")
    parser.add_option("-p", "--password", help="specify password to log in", action="store", dest="password")
    parser.add_option("-o", "--port", help="specify inventory port", action="store", dest="port")
    parser.add_option("-a", "--atlas", help="path to atlas configfile", action="store", dest="atlas")
    parser.add_option("-m", "--config", help="Path to the configuration to set properties of the resources kept in "
                                             "the inventory", action="store", dest="config")
    parser.add_option("-v", "--v", help="logging all level except debug", action="store_true", dest="info",
                      default=False)
    parser.add_option("-d", "--vv", help="logging all level including debug", action="store_true", dest="debug",
                      default=False)
    parser.add_option("-l", "--loopback", help="use 127.0.0.1 address instead of listen to 0.0.0.0",
                      action="store_true", dest="loopback")
    parser.add_option("-s", "--sleep", help="specifiy sleep time for inventory builder, default: 1800", action="store",
                      dest="sleep")
    parser.add_option("-t", "--timeout", help="specifiy timeout for fetching data from vROps, default: 600",
                      action="store", dest="timeout")
    (options, args) = parser.parse_args()

    if options.user:
        os.environ['USER'] = options.user
    if options.password:
        os.environ['PASSWORD'] = options.password
    if options.info:
        logger.setLevel(logging.INFO)
        ConsoleHandler.setLevel(logging.INFO)
        logger.info('Starting inventory logging on INFO level')
    if options.debug:
        logger.setLevel(logging.DEBUG)
        ConsoleHandler.setLevel(logging.DEBUG)
        logger.debug('Starting inventory logging on DEBUG level')
    if not options.debug and not options.info:
        logger.setLevel(logging.WARNING)
        ConsoleHandler.setLevel(logging.WARNING)
        logger.warning('Starting inventory logging on WARNING, ERROR and CRITICAL level')
    if options.loopback:
        os.environ['LOOPBACK'] = "1"
    if options.port:
        os.environ['PORT'] = options.port
    if options.atlas:
        os.environ['ATLAS'] = options.atlas
    if options.config:
        os.environ['INVENTORY_CONFIG'] = options.config
    if options.sleep:
        os.environ['SLEEP'] = options.sleep
    if not options.sleep and 'SLEEP' not in os.environ:
        logger.info('Defaulting sleep to 60s')
        os.environ['SLEEP'] = "60"
    if options.timeout:
        os.environ['TIMEOUT'] = options.timeout
    if not options.timeout and 'TIMEOUT' not in os.environ:
        logger.info('Defaulting timeout to 120s')
        os.environ['TIMEOUT'] = "120"

    if "PORT" not in os.environ and not options.port:
        logger.error('Cannot start, please specify PORT with ENV or -o')
        sys.exit(0)
    if "USER" not in os.environ and not options.user:
        logger.error('Cannot start, please specify USER with ENV or -u')
        sys.exit(0)
    if "PASSWORD" not in os.environ and not options.password:
        logger.error('Cannot start, please specify PASSWORD with ENV or -p')
        sys.exit(0)
    if "ATLAS" not in os.environ and not options.atlas:
        logger.error('Cannot start, please specify ATLAS path with ENV or -a')
        sys.exit(0)
    if "INVENTORY_CONFIG" not in os.environ and not options.config:
        logger.error('Cannot start, please specify inventory config with ENV or -m')
        sys.exit(0)

    return options


if __name__ == '__main__':
    logger = logging.getLogger('vrops-exporter')
    options = parse_params(logger)
    InventoryBuilder(options.atlas, os.environ['PORT'], os.environ['SLEEP'], os.environ['TIMEOUT'])
