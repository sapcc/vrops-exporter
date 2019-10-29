from BaseCollector import BaseCollector
import requests
import os
from requests.auth import HTTPBasicAuth
from prometheus_client.core import GaugeMetricFamily


class SampleCollector(BaseCollector):

    def __init__(self, target, user, password):
        self._target = target
        self._user = user
        self._password = password

    def collect(self):
        metric_list = list()
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

        metric_list.append(g)
        return metric_list
