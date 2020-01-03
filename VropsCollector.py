import json
import os
import importlib
import sys
import requests
import traceback

sys.path.append('./module')
from requests.auth import HTTPBasicAuth
from prometheus_client import CollectorRegistry
from prometheus_client.exposition import MetricsHandler, choose_encoder
from urllib.parse import urlparse, parse_qs
from urllib3 import disable_warnings, exceptions
from urllib3.exceptions import HTTPError
from resources.Vcenter import Vcenter


def do_GET(self):
    registry = CollectorRegistry()
    params = parse_qs(urlparse(self.path).query)
    if len(params.keys()) != 0:
        try:
            if os.environ['DEBUG'] == '1':
                print(params['target'])
            collector = VropsCollector(params['target'][0])
        except Exception as e:
            print("Problem instantiating VropsCollector:\n" + str(e))
            print(sys.exc_info()[0])
            traceback.print_exc()
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
        envvars = os.environ.keys()
        if 'USER' not in envvars:
            raise ValueError('USER not set')
        if 'PASSWORD' not in envvars:
            raise ValueError('PASSWORD not set')
        self._user = os.environ['USER']
        self._password = os.environ['PASSWORD']
        self._resources = self.create_resource_objects()
        modules = self.get_modules()
        self._modules = modules[1]
        self._modules_dict = dict()
        for module in self._modules:
            if os.environ['DEBUG'] == '1':
                print(module + ' does cool stuff now')
            self._modules_dict[module] = importlib.import_module(module, modules[0])

    def create_resource_objects(self):
        for adapter in self.get_adapter(target=self._target):
            vcenter = Vcenter(target=self._target, name=adapter['name'], uuid=adapter['uuid'])
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
            if hasattr(response.json(), "adapterInstancesInfoDto"):
                for resource in response.json()["adapterInstancesInfoDto"]:
                    res = dict()
                    res['name'] = resource["resourceKey"]["name"]
                    res['uuid'] = resource["id"]
                    res['adapterkind'] = resource["resourceKey"]["adapterKindKey"]
                    adapters.append(res)
            else:
                raise AttributeError("There is no attribute: adapterInstancesInfoDto")
        except HTTPError as err:
            print("Request failed: ", err.args)

        return adapters

    def get_modules(self):
        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        target_dir = current_dir.replace('/vrops-exporter', '/vrops-exporter/module')
        all_files = os.listdir(target_dir)
        files = list()
        for file in all_files:
            if file.startswith('__') or file.startswith('.'):
                continue
            file = file[:-3]
            files.append(file)
        return target_dir, files

    def collect(self):
        for module in self._modules_dict.keys():
            imported_module = self._modules_dict[module]
            func = getattr(imported_module, module)
            res = func(self._resources, self._target, self._user, self._password).collect()
            for i in res:
                yield i
