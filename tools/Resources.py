import os
import requests
import urllib3
from requests.auth import HTTPBasicAuth


class Resources:
    
    def get_resources(self, target, parentid, resourcekind):
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
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        resources = list()
        response = requests.get(url,
                                auth=HTTPBasicAuth(username=os.environ['USER'], password=os.environ['PASSWORD']),
                                params=querystring,
                                verify=False,
                                headers=headers)
        for resource in response.json()["resourceList"]:
            res = dict()
            res['name'] = resource["resourceKey"]["name"]
            res['uuid'] = resource["identifier"]
            resources.append(res)
        return resources

    def get_project_id(self, target):
        project_ids = list()
        for project in self.get_resources(target=target, resourcekind='VMFolder'):
            if project['name'].startswith('Project'):
                p_ids = dict()
                p_ids['project_id'] = project['name'][project['name'].find("(") + 1:project['name'].find(")")]
                p_ids['uuid'] = project['uuid']
                project_ids.append(p_ids)
        return project_ids

    def get_datacenter(self, target, parentid):
        self.get_resources(target, parentid, resourcekind="Datacenter")

    def get_cluster(self, target, parentid):
        self.get_resources(target, parentid, resourcekind="ClusterComputeResource")

    def get_hosts(self, target, parentid):
        self.get_resources(target, parentid, resourcekind="HostSystem")

    def get_virtualmachines(self, target, parentid):
        self.get_resources(target, parentid, resourcekind="VirtualMachine")


