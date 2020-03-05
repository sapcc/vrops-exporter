import requests, os, json

from urllib3 import disable_warnings, exceptions
from urllib3.exceptions import HTTPError


class Resources:

    def get_resources(self, target, token, resourcekind, parentid):
        url = "https://" + target + "/suite-api/api/resources"
        querystring = {
            'parentId': parentid,
            'adapterKind': 'VMware',
            'resourceKind': resourcekind,
            'pageSize': '50000'
        }
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        resources = list()
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.get(url,
                                    params=querystring,
                                    verify=False,
                                    headers=headers)
            if response.status_code == 200:
                for resource in response.json()["resourceList"]:
                    res = dict()
                    res['name'] = resource["resourceKey"]["name"]
                    res['uuid'] = resource["identifier"]
                    resources.append(res)
            else:
                raise AttributeError("There is no attribute resourceList \nerror message: " + str(response.json()))
        except HTTPError as e:
            raise HTTPError("Request failed for resourceList: " + target + "\nerror message: " + str(e))

        return resources

    def get_project_id(self, target, token):
        project_ids = list()
        for project in self.get_vmfolders(target=target, token=token):
            if project['name'].startswith('Project'):
                p_ids = dict()
                p_ids['project_id'] = project['name'][project['name'].find("(") + 1:project['name'].find(")")]
                p_ids['uuid'] = project['uuid']
                project_ids.append(p_ids)
        return project_ids

    def get_datacenter(self, target, token, parentid):
        return self.get_resources(target, token, parentid=parentid, resourcekind="Datacenter")

    def get_cluster(self, target, token, parentid):
        return self.get_resources(target, token, parentid=parentid, resourcekind="ClusterComputeResource")

    def get_hosts(self, target, token, parentid):
        return self.get_resources(target, token, parentid=parentid, resourcekind="HostSystem")

    def get_virtualmachines(self, target, token, parentid):
        return self.get_resources(target, token, parentid=parentid, resourcekind="VirtualMachine")

    def get_vmfolders(self, target, token):
        return self.get_resources(target, token, parentid=None, resourcekind="VMFolder")

    # not recommended
    def get_latest_stat(target, token, uuid, key):
        url = "https://" + target + "/suite-api/api/resources/" + uuid + "/stats/latest"
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.get(url,
                                    verify=False,
                                    headers=headers)
        except Exception as e:
            print("Problem getting stats Error: " + str(e))
            return False

        if response.status_code == 200:
            for statkey in response.json()["values"][0]["stat-list"]["stat"]:
                if statkey["statKey"]["key"] is not None and statkey["statKey"]["key"] == key:
                    return statkey["data"][0]
        else:
            print("Return code not 200 for " + str(key) + ": " + str(response.json()))
            return False

    def get_latest_stat_multiple(target, token, uuids, key):

        url = "https://" + target + "/suite-api/api/resources/stats/latest/query"
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        payload = {
            "resourceId": uuids,
            "statKey": [key]
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.post(url,
                                     data=json.dumps(payload),
                                     verify=False,
                                     headers=headers)
        except Exception as e:
            print("Problem getting stats Error: " + str(e))
            return False

        if response.status_code == 200:
            return response.json()['values']
        else:
            print("Return code not 200 for " + str(key) + ": " + str(response.json()))
            return False

    def get_latest_property(target, token, uuid, key):
        url = "https://" + target + "/suite-api/api/resources/" + uuid + "properties"
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.get(url,
                                    verify=False,
                                    headers=headers)
        except Exception as e:
            print("Problem getting stats Error: " + str(e))
            return False

        if response.status_code == 200:
            for propkey in response.json()["property"]:
                if propkey["name"] is not None and propkey["name"] == key:
                    return propkey["value"]
        else:
            print("Return code not 200 for " + str(key) + ": " + str(response.json()))
            return False

    def get_latest_properties_multiple(target, token, uuids, propkey):

        url = "https://" + target + "/suite-api/api/resources/properties/latest/query"
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        payload = {
            "resourceIds": uuids,
            "propertyKeys": [propkey]
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.post(url,
                                     data=json.dumps(payload),
                                     verify=False,
                                     headers=headers)
        except Exception as e:
            print("Problem getting property Error: " + str(e))
            return False

        if response.status_code == 200:
            return response.json()['values']
        else:
            print("Return code not 200 for " + str(propkey) + ": " + str(response.json()))
            return False
