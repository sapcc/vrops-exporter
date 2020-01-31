import json, os
from flask import Flask
from gevent.pywsgi import WSGIServer
import re, yaml, sys, time
import traceback
import requests
from threading import Thread
from resources.Vcenter import Vcenter
from urllib.parse import urlparse, parse_qs
from urllib3 import disable_warnings, exceptions
from urllib3.exceptions import HTTPError
from requests.auth import HTTPBasicAuth

class InventoryBuilder:
    def __init__(self, json):
        self.region = os.environ["REGION"]
        self.json = json
        self._user = os.environ["USER"]
        self._password = os.environ["PASSWORD"]
        self.vcenter_list = list()
        self.get_vrops()
        # self.query_vrops()
        # self.restify_object_tree()

        thread = Thread(target=self.run_rest_server)
        thread.start()

        self.query_inventory_permanent()

    def run_rest_server(self):
        app = Flask(__name__)
        print('serving /vrops_list on 8000')
        @app.route('/vrops_list', methods=['GET'])
        def vrops_list():
            return json.dumps(self.vrops_list)
        print('serving /inventory on 8000')
        @app.route('/inventory', methods=['GET'])
        def inventory():
            return self.rest_ready_tree
        # WSGIServer(('127.0.0.1', 8000), app).serve_forever()
        WSGIServer(('0.0.0.0', 8000), app).serve_forever()

    def get_vrops(self):
        with open(self.json) as json_file:
            netbox_json = json.load(json_file)
        vrops_list = list()
        for target in netbox_json:
            if target['labels']['job'] == "vrops":
                vrops = target['labels']['server_name']
                vrops_list.append(vrops)
        self.vrops_list = vrops_list

    def query_inventory_permanent(self):
        iteration = 0
        while True:
            print("real " + str(iteration))
            self.iteration = iteration
            iteration += 1
            self.query_vrops()
            self.restify_object_tree()

    def restify_object_tree(self):
        tree = dict()
        for vcenter in self.vcenter_list:
           tree[vcenter.uuid] = {
                   'uuid': vcenter.uuid,
                   'name': vcenter.name
                   }

           for datacenter in vcenter.datacenter:
               tree[vcenter.uuid][datacenter.uuid] = {
                      'uuid': datacenter.uuid,
                      'name': datacenter.name
                   }

               for cluster in datacenter.clusters:
                   tree[vcenter.uuid][datacenter.uuid][cluster.uuid] = {
                           'uuid': cluster.uuid,
                           'name': cluster.name
                       }
                   for host in cluster.hosts:
                       tree[vcenter.uuid][datacenter.uuid][cluster.uuid][host.uuid] = {
                               'uuid': host.uuid,
                               'name': host.name
                           }
                       for vm in host.vms:
                           tree[vcenter.uuid][datacenter.uuid][cluster.uuid][host.uuid][vm.uuid] = {
                                   'uuid': vm.uuid,
                                   'name': vm.name,
                                   'project_id': vm.project_id 
                               }
        self.rest_ready_tree = tree

    def query_vrops(self):
        for vrops in self.vrops_list:
            print("querying " + vrops)
            vcenter = self.create_resource_objects(vrops)
            self.vcenter_list.append(vcenter)

    def create_resource_objects(self, vrops):
        for adapter in self.get_adapter(target=vrops):
            vcenter = Vcenter(target=vrops, name=adapter['name'], uuid=adapter['uuid'])
            print(adapter['name'])
            vcenter.add_datacenter()
            for dc_object in vcenter.datacenter:
                print("Collecting Datacenter: " + dc_object.name)
                dc_object.add_cluster()
                for cl_object in dc_object.clusters:
                    print("Collecting Cluster: " + cl_object.name)
                    cl_object.add_host()
                    for hs_object in cl_object.hosts:
                        print("Collecting Hosts: " + hs_object.name)
                        hs_object.add_vm()
                        for vm_object in hs_object.vms:
                            print("Collecting VM: " + vm_object.name)
            return vcenter

    def get_adapter(self, target):
        url = "https://" + target + "/suite-api/api/adapters"
        querystring = {
            "adapterKindKey": "VMWARE"
        }
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json"
        }
        adapters = list()
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.get(url,
                                    auth=HTTPBasicAuth(username=self._user, password=self._password),
                                    params=querystring,
                                    verify=False,
                                    headers=headers)
        except HTTPError as err:
            print("Request failed: ", err.args)
        # print(response.json())
        if 'adapterInstancesInfoDto' in response.json():
            for resource in response.json()["adapterInstancesInfoDto"]:
                res = dict()
                res['name'] = resource["resourceKey"]["name"]
                res['uuid'] = resource["id"]
                res['adapterkind'] = resource["resourceKey"]["adapterKindKey"]
                adapters.append(res)
        else:
            raise AttributeError("There is no attribute: adapterInstancesInfoDto")

        return adapters
