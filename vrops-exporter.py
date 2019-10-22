import sys
import time
import os
from prometheus_client import start_http_server
from tools.YamlRead import YamlRead
import VropsCollector

if __name__ == '__main__':
    # Read yaml file
    config = YamlRead(sys.argv[1]).run()
    os.environ['USER'] = config['user']
    os.environ['PASSWORD'] = config['password']

    # Debug option
    os.environ['DEBUG'] = '0'
    if config['debug'] is True:
        os.environ['DEBUG'] = '1'

    # Start the Prometheus http server.
    start_http_server(config['port'])

    while True:
        time.sleep(1)

