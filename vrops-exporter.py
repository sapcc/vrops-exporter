import requests
from prometheus_client import Metric, start_http_server, REGISTRY
import json
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning

class Collector(object):

    def __init__(self, target, user, password):
        self._target = target
        self._user = user
        self._password = password

    def collect(self):
        url = "https://vcops01.wdf.sap.corp/suite-api/api/resources"

        querystring = {"resourceKind": "host"}

        payload = "{\n  \"username\" : \"prometheusapiuser\",\n  \"password\" : \"2SNNg/&GCsyN\"\n}\n"
        headers = {
            'Content-Type': "application/json",
            'Authorization': "Basic cHJvbWV0aGV1c2FwaXVzZXI6MlNOTmcvJkdDc3lO",
            'User-Agent': "PostmanRuntime/7.17.1",
            'Accept': "application/json",
            'Cache-Control': "no-cache",
            'Postman-Token': "b1eed2c7-4bc3-46ad-aac8-19a7dbd9fdfd,a9ad9a2a-3d1b-4063-b9aa-70184deb04ae",
            'Host': "vcops01.wdf.sap.corp",
            'Accept-Encoding': "gzip, deflate",
            'Content-Length': "70",
            'Connection': "keep-alive",
            'cache-control': "no-cache"
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring, verify=False)
        response.

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

# main-Klasse
if __name__ == '__main__':
    # Start the Prometheus http server and register exporter class.
    start_http_server(1234)

    # vrops registrieren
    registry = REGISTRY.register(Collector(target="vcops01", user="prometheusapiuser", password="2SNNg/&GCsyN"))

    while True:
        time.sleep(1)

