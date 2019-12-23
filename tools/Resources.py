import os
import requests
from urllib3 import disable_warnings, exceptions
from urllib3.exceptions import HTTPError
from requests.auth import HTTPBasicAuth


class Resources:

    def get_resources(self, target, resourcekind, parentid):
        url = "https://" + target + "/suite-api/api/resources"
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
        resources = list()
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.get(url,
                                    auth=HTTPBasicAuth(username=os.environ['USER'], password=os.environ['PASSWORD']),
                                    params=querystring,
                                    verify=False,
                                    headers=headers)
            if hasattr(response.json(), "resourceList"):
                for resource in response.json()["resourceList"]:
                    res = dict()
                    res['name'] = resource["resourceKey"]["name"]
                    res['uuid'] = resource["identifier"]
                    resources.append(res)
            else:
                raise AttributeError("There is no attribute: resourceList")
        except HTTPError as err:
            print("Request failed: ", err.args)

        return resources

    def get_project_id(self, target):
        project_ids = list()
        for project in self.get_vmfolders(target=target):
            if project['name'].startswith('Project'):
                p_ids = dict()
                p_ids['project_id'] = project['name'][project['name'].find("(") + 1:project['name'].find(")")]
                p_ids['uuid'] = project['uuid']
                project_ids.append(p_ids)
        return project_ids

    def get_datacenter(self, target, parentid):
        return self.get_resources(target, parentid=parentid, resourcekind="Datacenter")

    def get_cluster(self, target, parentid):
        return self.get_resources(target, parentid=parentid, resourcekind="ClusterComputeResource")

    def get_hosts(self, target, parentid):
        return self.get_resources(target, parentid=parentid, resourcekind="HostSystem")

    def get_virtualmachines(self, target, parentid):
        return self.get_resources(target, parentid=parentid, resourcekind="VirtualMachine")

    def get_vmfolders(self, target):
        return self.get_resources(target, parentid=None, resourcekind="VMFolder")


