import requests
from requests.auth import HTTPBasicAuth
import sys
from prometheus_client import Metric, start_http_server, CollectorRegistry
from prometheus_client.exposition import MetricsHandler, choose_encoder
import json
import time
from urllib.parse import urlparse, parse_qs, parse_qsl
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from module.read_yaml import YamlRead


def do_GET(self):
    registry = CollectorRegistry()
    params = parse_qs(urlparse(self.path).query)
    print(params)
    if len(params.keys()) != 0:
        try:
            print(params['target'])
            collector = Collector(params['target'][0], config)
        except Exception as e:
            print("obviously missing params: " + json.dumps(params))
            print(e)
            return
        try:
            registry.register(collector)
        except Exception as e:
            print("failed to register: " + json.dumps(params))
            print(e)
            return

    encoder, content_type = choose_encoder(self.headers.get('Accept'))
    try:
        output = encoder(registry)
    except:
        self.send_error(500, 'error generating metric output')
        raise
    self.send_response(200)
    self.send_header('Content-Type', content_type)
    self.end_headers()
    self.wfile.write(output)


MetricsHandler.do_GET = do_GET


class Collector(object):

    def __init__(self, target, config):
        self._target = target
        self._user = config['user']
        self._password = config['password']

    def collect(self):

        url = "https://" + self._target + "/suite-api/api/resources"
        querystring = {"resourceKind": "host"}
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

        response = requests.get(url, auth=HTTPBasicAuth(self._user, self._password), verify=False, params=querystring,
                                headers=headers)

        print(response)
        json_response = response.json()
        for resource in json_response["resourceList"]:
            print(resource["identifier"], resource["resourceKey"]["name"])
        print("Completed")

        entityname = "vmentityname"

        metric = Metric("vrops_virtualmachine", "virtualmachine from vrops", "gauge")

        metric.add_sample("vrops_vmentityname",
                          value=1, labels={"target": self._target,
                                           "entityname": entityname})

        yield metric


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# main
if __name__ == '__main__':
    # Read yaml file
    config = YamlRead(sys.argv[1]).run()

    # Start the Prometheus http server.
    start_http_server(config['port'])

    while True:
        time.sleep(1)

