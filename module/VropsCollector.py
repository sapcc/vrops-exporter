import requests
import json
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.auth import HTTPBasicAuth
from prometheus_client.core import GaugeMetricFamily
from prometheus_client import CollectorRegistry
from prometheus_client.exposition import MetricsHandler, choose_encoder
from urllib.parse import urlparse, parse_qs, parse_qsl


def do_GET(self):
    registry = CollectorRegistry()
    params = parse_qs(urlparse(self.path).query)
    print(params)
    if len(params.keys()) != 0:
        try:
            print(params['target'])
            collector = VropsCollector(params['target'][0])
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
    if 'name[]' in params:
        registry = registry.restricted_registry(params['name[]'])
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


class VropsCollector:

    def __init__(self, target):
        self._target = target
        self._user = os.environ['USER']
        self._password = os.environ['PASSWORD']

    def collect(self):
        if os.environ['DEBUG'] == '1':
            print('started')

        url = "https://" + self._target + "/suite-api/api/resources"
        querystring = {"resourceKind": "host"}
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

        response = requests.get(url, auth=HTTPBasicAuth(self._user, self._password), verify=False, params=querystring,
                                headers=headers)

        if os.environ['DEBUG'] == '1':
            print(response)

        json_response = response.json()
        for resource in json_response["resourceList"]:
            print(resource["identifier"], resource["resourceKey"]["name"])

        if os.environ['DEBUG'] == '1':
            print("Completed")

        entityname = "vmentityname"

        g = GaugeMetricFamily('vrops_ressource_gauge', 'Gauge Collector for vRops',
                              labels=['target', 'entityname'])
        g.add_metric(labels=[self._target, entityname], value=1)
        yield g


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
