import requests
import urllib3
from requests.auth import HTTPBasicAuth


def get_resources(self, resourcetype, resourcekind=None, parentid=None):

    url = "https://" + self._target + "/suite-api/api/" + resourcetype

    querystring = {
        'parentId': parentid,
        'adapterKind': 'VMware',
        'resourceKind': resourcekind,
        'pageSize': '50000'
    }

    headers = {
        'Content-Type': "application/json",
        'Accept': "application/json"
    }

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    resources = list()

    if resourcekind:
        response = requests.get(url,
                                auth=HTTPBasicAuth(self._user, self._password),
                                params=querystring,
                                verify=False,
                                headers=headers)

        for resource in response.json()["resourceList"]:
            res = dict()
            res['name'] = resource["resourceKey"]["name"]
            res['uuid'] = resource["identifier"]
            resources.append(res)

    else:
        response = requests.get(url,
                                auth=HTTPBasicAuth(self._user, self._password),
                                verify=False,
                                headers=headers)

        for resource in response.json()["adapterInstancesInfoDto"]:
            res = dict()
            res['name'] = resource["resourceKey"]["name"]
            res['uuid'] = resource["id"]
            resources.append(res)

    return resources
