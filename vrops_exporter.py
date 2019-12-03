#!/usr/bin/python3

import sys
import time
import os
from prometheus_client import start_http_server
from optparse import OptionParser
from VropsCollector import VropsCollector


def parse_params():
    parser = OptionParser()
    parser.add_option("-u", "--user", help="specify user to log in", action="store", dest="user")
    parser.add_option("-p", "--password", help="specify password to log in", action="store", dest="password")
    parser.add_option("-o", "--port", help="specify exporter port", action="store", dest="port")
    parser.add_option("-d", "--debug", help="enable debug", action="store_true", dest="debug", default=False)
    (options, args) = parser.parse_args()

    if options.user:
        os.environ['USER'] = options.user
    if options.password:
        os.environ['PASSWORD'] = options.password
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
    if "USER" not in os.environ and not options.user:
        print("Can't start, please specify user with ENV or -u")
        sys.exit(0)
    if "PASSWORD" not in os.environ and not options.password:
        print("Can't start, please specify password with ENV or -p")
        sys.exit(0)

def run_prometheus_server(port, *args):
    # Start the Prometheus http server.
    # start_http_server(int(os.environ['PORT']))
    start_http_server(int(port))

    while True:
        time.sleep(1)

if __name__ == '__main__':
    parse_params()
    run_prometheus_server(int(os.environ['PORT']))
