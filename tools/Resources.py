import requests
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
            try:
                for resource in response.json()["resourceList"]:
                    res = dict()
                    res['name'] = resource["resourceKey"]["name"]
                    res['uuid'] = resource["identifier"]
                    resources.append(res)
            except AttributeError as ar:
                print("There is no attribute: resourceList", ar.args)
        except HTTPError as err:
            print("Request failed: ", err.args)

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


