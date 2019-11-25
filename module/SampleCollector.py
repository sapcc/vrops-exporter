from BaseCollector import BaseCollector
import os
from prometheus_client.core import GaugeMetricFamily
from resources import *
from tools import get_resources
from random import randint


class SampleCollector(BaseCollector):

    def __init__(self, target, user, password):
        self._target = target
        self._user = user
        self._password = password

    def collect(self):
        vcenter = list()
        metric_list = list()
        if os.environ['DEBUG'] == '1':
            print('started')

        # resources were collected

        for vc in get_resources(self, target=self._target, user=self._user, password=self._password,
                                resourcetype='adapters'):
            vcenter.append(Vcenter(target=self._target, user=self._user, password=self._password,
                                   name=vc['name'], uuid=vc['uuid']))

        g = GaugeMetricFamily('vrops_ressource_gauge', 'Gauge Collector for vRops',
                              labels=['target', 'vcenter', 'datacenter', 'cluster', 'host', 'VirtualMachine', 'value'])

        for vc_object in vcenter:
            vc_object.add_datacenter()
            if os.environ['DEBUG'] == '1':
                print("Collecting Vcenter: " + vc_object.name)
            for dc_object in vc_object.datacenter:
                dc_object.add_cluster()
                # dc_object.get_project_ids()
                if os.environ['DEBUG'] == '1':
                    print("Collecting Datacenter: " + dc_object.name)
                for cl_object in dc_object.clusters:
                    cl_object.add_host()
                    if os.environ['DEBUG'] == '1':
                        print("Collecting Cluster: " + cl_object.name)
                    for hs_object in cl_object.hosts:
                        hs_object.add_vm()
                        if os.environ['DEBUG'] == '1':
                            print("Collecting Hosts: " + hs_object.name)
                        for vm_object in hs_object.vms:
                            if os.environ['DEBUG'] == '1':
                                print("Collecting VM: " + vm_object.name)
                        g.add_metric(labels=[self._target, vc_object.name, dc_object.name, cl_object.name,
                                             hs_object.name], value=randint(23, 6962))

        metric_list.append(g)
        return metric_list
