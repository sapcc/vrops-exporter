import urllib3.exceptions
from flask import Flask
from gevent.pywsgi import WSGIServer
from threading import Thread
from tools.Vrops import Vrops
from tools.helper import yaml_read
from collections import defaultdict
from types import SimpleNamespace
import time
import json
import os
import logging
import requests

import pudb
logger = logging.getLogger('vrops-exporter')


class InventoryBuilder:
    def __init__(self, atlas_path, port, sleep, timeout):
        self.atlas_path = atlas_path
        self.vrops_list = list()
        self.port = int(port)
        self.sleep = sleep
        self.timeout = int(timeout)
        self._user = os.environ["USER"]
        self._password = os.environ["PASSWORD"]
        self.vcenter_dict = dict()
        self.nsxt_dict = dict()
        self.vcops_dict = dict()
        self.sddc_dict = dict()
        self.target_tokens = dict()
        self.iterated_inventory = dict()
        self.amount_resources = defaultdict(dict)
        self.vrops_collection_times = dict()
        self.response_codes = defaultdict(dict)
        self.alertdefinitions = dict()
        self.successful_iteration_list = [0]
        self.wsgi_address = '0.0.0.0'
        if 'LOOPBACK' in os.environ:
            if os.environ['LOOPBACK'] == '1':
                self.wsgi_address = '127.0.0.1'

        thread = Thread(target=self.run_rest_server)
        thread.start()

        self.query_inventory_permanent()

    def run_rest_server(self):

        app = Flask(__name__)
        logger.info(f'serving /vrops_list on {self.port}')

        @app.route('/vrops_list', methods=['GET'])
        def vrops_list():
            return json.dumps(self.vrops_list)

        logger.info(f'serving /inventory on  {self.port}')

        @app.route('/<target>/vcenters/<int:iteration>', methods=['GET'])
        def vcenters(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('vcenters', {}).get(target, {})

        @app.route('/<target>/datacenters/<int:iteration>', methods=['GET'])
        def datacenters(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('datacenters', {}).get(target, {})

        @app.route('/<target>/clusters/<int:iteration>', methods=['GET'])
        def clusters(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('clusters', {}).get(target, {})

        @app.route('/<target>/hosts/<int:iteration>', methods=['GET'])
        def hosts(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('hosts', {}).get(target, {})

        @app.route('/<target>/datastores/<int:iteration>', methods=['GET'])
        def datastores(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('datastores', {}).get(target, {})

        @app.route('/<target>/vms/<int:iteration>', methods=['GET'])
        def vms(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('vms', {}).get(target, {})

        @app.route('/<target>/dvs/<int:iteration>', methods=['GET'])
        def distributed_virtual_switches(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('distributed_virtual_switches', {}).get(target,
                                                                                                                 {})

        @app.route('/<target>/nsxt_adapter/<int:iteration>', methods=['GET'])
        def nsxt_adapter(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('nsxt_adapter', {}).get(target, {})

        @app.route('/<target>/nsxt_mgmt_cluster/<int:iteration>', methods=['GET'])
        def nsxt_mgmt_cluster(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('nsxt_mgmt_cluster', {}).get(target, {})

        @app.route('/<target>/nsxt_mgmt_nodes/<int:iteration>', methods=['GET'])
        def nsxt_mgmt_nodes(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('nsxt_mgmt_nodes', {}).get(target, {})

        @app.route('/<target>/nsxt_mgmt_service/<int:iteration>', methods=['GET'])
        def nsxt_mgmt_service(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('nsxt_mgmt_service', {}).get(target, {})

        @app.route('/<target>/nsxt_transport_nodes/<int:iteration>', methods=['GET'])
        def nsxt_transport_nodes(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('nsxt_transport_nodes', {}).get(target, {})

        @app.route('/<target>/nsxt_logical_switches/<int:iteration>', methods=['GET'])
        def nsxt_logical_switches(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('nsxt_logical_switches', {}).get(target, {})

        @app.route('/<target>/vcops_objects/<int:iteration>', methods=['GET'])
        def vcops_self_monitoring_objects(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('vcops_objects', {}).get(target,
                                                                                                                {})

        @app.route('/<target>/sddc_objects/<int:iteration>', methods=['GET'])
        def sddc_health_objects(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('sddc_objects', {}).get(target, {})

        @app.route('/alertdefinitions/', methods=['GET'])
        def alert_alertdefinitions():
            return self.alertdefinitions

        @app.route('/iteration', methods=['GET'])
        def iteration():
            return_iteration = self.successful_iteration_list[-1]
            return str(return_iteration)

        @app.route('/amount_resources', methods=['GET'])
        def amount_resources():
            amount_resources = self.amount_resources
            return json.dumps(amount_resources)

        @app.route('/collection_times', methods=['GET'])
        def collection_times():
            vrops_collection_times = self.vrops_collection_times
            return json.dumps(vrops_collection_times)

        @app.route('/api_response_codes', methods=['GET'])
        def api_response_codes():
            response_codes = self.response_codes
            return json.dumps(response_codes)

        # debugging purpose
        @app.route('/iteration_store', methods=['GET'])
        def iteration_store():
            return_iteration = self.successful_iteration_list
            return json.dumps(return_iteration)

        # FIXME: this could basically be the always active token list. no active token? refresh!
        @app.route('/target_tokens', methods=['GET'])
        def token():
            return json.dumps(self.target_tokens)

        try:
            if logger.level == 10:
                # WSGi is logging on DEBUG Level
                WSGIServer((self.wsgi_address, self.port), app).serve_forever()
            else:
                WSGIServer((self.wsgi_address, self.port), app, log=None).serve_forever()
        except TypeError as e:
            logger.error('Problem starting server, you might want to try LOOPBACK=0 or LOOPBACK=1')
            logger.error(f'Current used options: {self.wsgi_address} on port {self.port}')
            logger.error(f'TypeError: {e}')

    def read_inventory_config(self):
        return yaml_read(os.environ['INVENTORY_CONFIG'])

    def get_vrops(self):
        vrops_list = list()
        if not self.atlas_path and not self.vrops_list:
            vrops_list = yaml_read(os.environ['INVENTORY_CONFIG']).get('vrops_targets', [])
        elif self.atlas_path:
            try:
                response = requests.get(url=self.atlas_path)
                netbox_json = response.json()
                vrops_list = [target['labels']['server_name'] for target in netbox_json if
                                   target['labels']['job'] == "vrops"]
            except (urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError,
                    urllib3.exceptions.NewConnectionError):
                logger.error(f'Failed to establish a connection to: {self.atlas_path}, retrying in {self.sleep}s')
                logger.info('continue with the old vrops_list')

        #initate vrops skel
        [self.vrops_list.append(SimpleNamespace(vc=dict(), name=vrops, handle=None)) for vrops in vrops_list]

    def query_inventory_permanent(self):
        # first iteration to fill is 1. while this is not ready,
        # curl to /iteration would still report 0 to wait for actual data
        self.iteration = 1
        while True:
            self.read_inventory_config()
            # get vrops targets every run in case we have new targets appearing
            self.get_vrops()
            if len(self.successful_iteration_list) > 2:
                iteration_to_be_deleted = self.successful_iteration_list.pop(0)
                # initial case, since 0 is never filled in iterated_inventory
                if iteration_to_be_deleted == 0:
                    continue
                self.iterated_inventory.pop(str(iteration_to_be_deleted))
                logger.debug(f'deleting iteration {iteration_to_be_deleted}')

            # initialize empty inventory per iteration
            self.iterated_inventory[str(self.iteration)] = dict()
            logger.info(f'real run {self.iteration}')
            threads = list()
            for vrops_skel in self.vrops_list:
                thread = Thread(target=self.query_vrops, args=(vrops_skel, self.iteration))
                thread.start()
                threads.append((thread, vrops_skel.name))

            timeout = self.timeout
            timeout_reached = False
            start_time = time.time()
            current_time = start_time
            joined_threads = dict()
            while current_time <= (start_time + timeout):
                for t in threads:
                    if not t[0].is_alive():
                        t[0].join()
                        if t[0] not in joined_threads:
                            joined_threads.setdefault(t[1], round(time.time() - start_time))
                if len(joined_threads.keys()) >= len(threads):
                    break
                time.sleep(1)
                current_time = time.time()
            else:
                still_running = [t for t in threads if t[0].is_alive()]
                for running_thread in still_running:
                    logger.info(f"Timeout {timeout}s reached for fetching {running_thread[1]}")
                    running_thread[0].join(0)
                    timeout_reached = True
            for vrops_name in joined_threads:
                self.vrops_collection_times[vrops_name] = joined_threads[vrops_name]
                logger.info(f"Fetched {vrops_name} in {joined_threads[vrops_name]}")

            self.provide_vcenters()
            self.provide_datacenters()
            self.provide_clusters()
            self.provide_hosts()
            self.provide_datastores()
            self.provide_vms()
            self.provide_distributed_vswitches()
            # self.provide_nsxt_adapter()
            # self.provide_nsxt_mgmt_cluster()
            # self.provide_nsxt_mgmt_nodes()
            # self.provide_nsxt_mgmt_service()
            # self.provide_nsxt_transport_nodes()
            # self.provide_nsxt_logical_switches()
            # self.provide_vcops_objects()
            # self.provide_sddc_objects()
            pu.db
            if len(self.iterated_inventory[str(self.iteration)]['vcenters']) > 0:
                self.successful_iteration_list.append(self.iteration)
            else:
                # immediately withdraw faulty inventory
                logger.debug(f'Withdrawing current iteration: {self.iteration}')
                self.iterated_inventory.pop(str(self.iteration))
            self.iteration += 1
            if not timeout_reached:
                logger.info(f'Inventory relaxing before going to work again in {self.sleep}s')
                time.sleep(int(self.sleep))

    def query_vrops(self, vrops_skel, iteration):
        target = vrops_skel.name
        vrops_skel.handle = Vrops()
        logger.info(f'Querying {vrops_skel.name}')
        token, self.response_codes[vrops_skel.name]["token"] = Vrops.get_token(vrops_skel.name)
        if not token:
            logger.warning(f'retrying connection to {vrops_skel.name} in next iteration {self.iteration + 1}')
            return False
        self.target_tokens[vrops_skel.name] = token

        vrops_short_name = vrops_skel.name.split('.')[0]
        logger.info(f'##########  Collecting resources {vrops_short_name}... ##########')

        inventory_config = self.read_inventory_config()
        query_specs = inventory_config.get('query_specs', {})


        # creates all vcenter objects including nsxt & co kg
        vrops_skel = self.create_vcenter_objects(vrops_skel, token, query_specs)
        # self.create_nsxt_objects(vrops_skel, token, query_specs)
        # self.create_vcops_objects(vrops_skel, token, inventory_config)
        # self.create_sddc_health_objects(vrops_skel, token, inventory_config)

        # vcenter = self.create_vcenter_objects(vrops_skel, token, query_specs)
        # nsxt_adapter = self.create_nsxt_objects(vrops_skel, token, query_specs)
        # vcops_adapter = self.create_vcops_objects(vrops_skel, token, inventory_config)
        # sddc_adapter = self.create_sddc_health_objects(vrops_skel, token, inventory_config)

        # TODO: to be done
        # self.vcenter_dict[target] = vcenter
        # self.nsxt_dict[target] = nsxt_adapter
        # self.vcops_dict[target] = vcops_adapter
        # self.sddc_dict[target] = sddc_adapter

        if iteration == 1:
            self.alertdefinitions = Vrops.get_alertdefinitions(vrops_skel.handle, vrops_skel.name, token)
        return True

    def create_vcenter_objects(self, vrops_skel: object, token: str, query_specs: dict):
        vcenter_adapter, self.response_codes[vrops_skel.name]["vcenter"] = \
                Vrops.get_vcenter_adapter(vrops_skel.handle, vrops_skel.name, token)

        # just one vcenter adapter supported
        # vcenter_adapter = vcenter_adapter[0]

        if not vcenter_adapter:
            logger.critical('Could not get any vcenter adapter!')
            return False

        for vcenter in vcenter_adapter:
            logger.debug(f'Collecting vcenter: {vcenter.name}')
            vrops_skel.vc[vcenter.name] = SimpleNamespace(
                vcenter                       = vcenter,
                datacenter                    = list(),
                cluster                       = list(),
                hosts                         = list(),
                datastores                    = list(),
                vms                           = list(),
                distributed_virtual_switches  = list(),
                nsxt_adapter                  = list(),
                nsxt_mgmt_cluster             = list(),
                nsxt_mgmt_nodes               = list(),
                nsxt_mgmt_service             = list(),
                nsxt_transport_nodes          = list(),
                nsxt_logical_switches         = list(),
                vcops_objects                 = list(),
                sddc_objects                  = list(),
                )

            vrops_skel.vc[vcenter.name].datacenter, self.response_codes[vrops_skel.name]["datacenters"] = \
                Vrops.get_datacenter(vrops_skel.handle, vrops_skel.name, token, [vcenter.uuid], query_specs=query_specs)
            vrops_skel.vc[vcenter.name].cluster, self.response_codes[vrops_skel.name]["clusters"] = \
                Vrops.get_cluster(vrops_skel.handle, vrops_skel.name, token, [dc.uuid for dc in vrops_skel.vc[vcenter.name].datacenter], query_specs=query_specs)
            vrops_skel.vc[vcenter.name].datastores, self.response_codes[vrops_skel.name]["datastores"] = \
                Vrops.get_datastores(vrops_skel.handle, vrops_skel.name, token, [dc.uuid for dc in vrops_skel.vc[vcenter.name].datacenter], query_specs=query_specs)
            vrops_skel.vc[vcenter.name].hosts, self.response_codes[vrops_skel.name]["hosts"] = \
                Vrops.get_hosts(vrops_skel.handle, vrops_skel.name, token, [cl.uuid for cl in vrops_skel.vc[vcenter.name].cluster], query_specs=query_specs)
            vrops_skel.vc[vcenter.name].vms, self.response_codes[vrops_skel.name]["vms"] = \
                Vrops.get_vms(vrops_skel.handle, vrops_skel.name, token, [hs.uuid for hs in vrops_skel.vc[vcenter.name].hosts], vcenter.uuid, query_specs=query_specs)
            vrops_skel.vc[vcenter.name].distributed_virtual_switches, self.response_codes[vrops_skel.name]["distributed_virtual_switch"] = \
                Vrops.get_dis_virtual_switch(vrops_skel.handle, vrops_skel.name, token, [dc.uuid for dc in vrops_skel.vc[vcenter.name].datacenter], query_specs=query_specs)

        return vrops_skel

    def create_nsxt_objects(self, vrops, target: str, token: str, query_specs: dict):
        nsxt_adapter_list, self.response_codes[target]["nsxt_adapter"] = Vrops.get_nsxt_adapter(vrops, target, token)
        if not nsxt_adapter_list:
            logger.warning(f'Could not get any nsxt adapter from {target}!')
            return False

        nsxt_mgmt_cluster, self.response_codes[target]["nsxt_mgmt_cluster"] = \
            Vrops.get_nsxt_mgmt_cluster(vrops, target, token, [a.uuid for a in nsxt_adapter_list],
                                        query_specs=query_specs)
        nsxt_mgmt_nodes, self.response_codes[target]["nsxt_mgmt_nodes"] = \
            Vrops.get_nsxt_mgmt_nodes(vrops, target, token, [c.uuid for c in nsxt_mgmt_cluster],
                                      query_specs=query_specs)
        nsxt_mgmt_service, self.response_codes[target]["nsxt_mgmt_services"] = \
            Vrops.get_nsxt_mgmt_service(vrops, target, token, [n.uuid for n in nsxt_mgmt_nodes],
                                        query_specs=query_specs)
        nsxt_transport_zones, self.response_codes[target]["nsxt_transport_zones"] = \
            Vrops.get_nsxt_transport_zone(vrops, target, token, [c.uuid for c in nsxt_mgmt_cluster],
                                          query_specs=query_specs)
        nsxt_transport_nodes, self.response_codes[target]["nsxt_transport_nodes"] = \
            Vrops.get_nsxt_transport_node(vrops, target, token, [z.uuid for z in nsxt_transport_zones],
                                          query_specs=query_specs)
        nsxt_logical_switches, self.response_codes[target]["nsxt_logical_switches"] = \
            Vrops.get_nsxt_logical_switch(vrops, target, token, [c.uuid for c in nsxt_mgmt_cluster],
                                          query_specs=query_specs)

        for nsxt_adapter in nsxt_adapter_list:
            logger.debug(f'Collecting NSX-T adapter: {nsxt_adapter.name}')
            nsxt_adapter.mgmt_cluster = list()

            for mgmt_cluster in nsxt_mgmt_cluster:
                if mgmt_cluster.parent == nsxt_adapter.uuid:
                    nsxt_adapter.mgmt_cluster.append(mgmt_cluster)
                    logger.debug(f'Collecting NSX-T management cluster: {mgmt_cluster.name}')
            for mgmt_cluster_object in nsxt_adapter.mgmt_cluster:
                mgmt_cluster_object.mgmt_nodes = list()
                mgmt_cluster_object.transport_zones = list()
                mgmt_cluster_object.logical_switches = list()
                for mgmt_node in nsxt_mgmt_nodes:
                    if mgmt_node.parent == mgmt_cluster_object.uuid:
                        mgmt_cluster_object.mgmt_nodes.append(mgmt_node)
                        logger.debug(f'Collecting NSX-T management node: {mgmt_node.name}')
                for nsxt_mgmt_node in mgmt_cluster_object.mgmt_nodes:
                    nsxt_mgmt_node.nsxt_mgmt_services = list()
                    for mgmt_service_instance in nsxt_mgmt_service:
                        if mgmt_service_instance.parent == nsxt_mgmt_node.uuid:
                            nsxt_mgmt_node.nsxt_mgmt_services.append(mgmt_service_instance)
                            logger.debug(f'Collecting NSX-T management service: {mgmt_service_instance.name}')
                for transport_zone in nsxt_transport_zones:
                    if transport_zone.parent == mgmt_cluster_object.uuid:
                        mgmt_cluster_object.transport_zones.append(transport_zone)
                        logger.debug(f'Collecting NSX-T transport zone: {transport_zone.name}')
                for nsxt_transport_zone in mgmt_cluster_object.transport_zones:
                    nsxt_transport_zone.nsxt_transport_nodes = list()
                    for transport_node in nsxt_transport_nodes:
                        if transport_node.parent == nsxt_transport_zone.uuid:
                            nsxt_transport_zone.nsxt_transport_nodes.append(transport_node)
                            logger.debug(f'Collecting NSX-T transport node: {transport_node.name}')
                for logical_switch in nsxt_logical_switches:
                    if logical_switch.parent == mgmt_cluster_object.uuid:
                        mgmt_cluster_object.logical_switches.append(logical_switch)
                        logger.debug(f'Collecting NSX-T logical switch: {logical_switch.name}')

        return nsxt_adapter_list

    def create_vcops_objects(self, vrops, target: str, token: str, inventory_config: dict):
        vcops_adapter_instance, self.response_codes[target]["vcops_adapter"] = \
            Vrops.get_vcenter_operations_adapter_intance(vrops, target, token)
        vcops_adapter_instance = vcops_adapter_instance[0]
        if not vcops_adapter_instance:
            logger.critical(f'Could not get vcops adapter!')
            return False

        resourcekinds = [rk for rk in inventory_config.get('resourcekinds', {}).get('vcops_resourcekinds', [])]
        query_specs = inventory_config.get('query_specs', {})

        vcops_objects, self.response_codes[target]["vcops_self_monitoring_objects"] = \
            Vrops.get_vcops_instances(vrops, target, token, parent_uuids=[vcops_adapter_instance.uuid],
                                      resourcekinds=resourcekinds, query_specs=query_specs)
        vcops_adapter_instance.vcops_objects = list()
        for vcops_object in vcops_objects:
            vcops_adapter_instance.vcops_objects.append(vcops_object)

        return vcops_adapter_instance

    def create_sddc_health_objects(self, vrops, target: str, token: str, inventory_config: dict):
        sddc_adapter_instances, self.response_codes[target]["sddc_health_adapter"] = \
            Vrops.get_sddc_health_adapter_intance(vrops, target, token)

        if not sddc_adapter_instances:
            return False

        resourcekinds = [rk for rk in inventory_config.get('resourcekinds', {}).get('sddc_resourcekinds', [])]
        query_specs = inventory_config.get('query_specs', {})

        sddc_objects, self.response_codes[target]["sddc_health_objects"] = \
            Vrops.get_sddc_instances(vrops, target, token, parent_uuids=[s.uuid for s in sddc_adapter_instances],
                                     resourcekinds=resourcekinds, query_specs=query_specs)

        for sddc_adapter in sddc_adapter_instances:
            logger.debug(f'Collecting SDDC adapter: {sddc_adapter.name}')
            sddc_adapter.sddc_health_objects = list()
            for sddc_object in sddc_objects:
                if sddc_object.parent == sddc_adapter.uuid:
                    logger.debug(f'Collecting SDDC object: {sddc_object.name}')
                    sddc_adapter.sddc_health_objects.append(sddc_object)

        return sddc_adapter_instances

    def provide_vcenters(self) -> dict:
        tree = dict()
        for vrops in self.vrops_list:
            for vcenter in vrops.vc:
                vc = vrops.vc[vcenter]
                tree[vc.vcenter.name] = dict()
                kind_uuid = [dc.uuid for dc in vc.datacenter if vc.vcenter.uuid == dc.parent]
                kind_name = [dc.name for dc in vc.datacenter if vc.vcenter.uuid == dc.parent]
                tree[vc.vcenter.name][vc.vcenter.uuid] = {
                    'uuid': vc.vcenter.uuid,
                    'name': vc.vcenter.name,
                    # TODO: compare if parent of datacenter is REALLY uuid of vcenter
                    'kind_dc_uuid': kind_uuid[0],
                    'kind_dc_name': kind_name[0],
                    'target': vc.vcenter.target,
                    'token': vc.vcenter.token
                    }
                # self.amount_resources[target]['vcenters'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['vcenters'] = tree
        return tree

    def provide_datacenters(self) -> dict:
        tree = dict()
        for vrops in self.vrops_list:
            for vcenter in vrops.vc:
                vc = vrops.vc[vcenter]
                tree[vc.vcenter.name] = dict()
                for dc in vc.datacenter:
                    tree[vc.vcenter.name][dc.uuid] = {
                        'uuid': dc.uuid,
                        'name': dc.name,
                        'internal_name': dc.internal_name,
                        'parent_vcenter_uuid': vc.vcenter.uuid,
                        'parent_vcenter_name': vc.vcenter.name,
                        'vcenter': vc.vcenter.name,
                        'target': vc.vcenter.target,
                        'token': vc.vcenter.token,
                        }
                # self.amount_resources[target]['vcenters'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['datacenters'] = tree
        return tree

    def provide_datastores(self) -> dict:
        tree = dict()
        for vrops in self.vrops_list:
            for vcenter in vrops.vc:
                vc = vrops.vc[vcenter]
                tree[vc.vcenter.name] = dict()
                for ds in vc.datastores:
                    parent_uuid = [dc.uuid for dc in vc.datacenter if dc.uuid == ds.parent]
                    parent_name = [dc.name for dc in vc.datacenter if dc.uuid == ds.parent]
                    tree[vc.vcenter.name][ds.uuid] = {
                        'uuid': ds.uuid,
                        'name': ds.name,
                        'internal_name': ds.internal_name,
                        'parent_dc_uuid': parent_uuid[0],
                        'parent_dc_name': parent_name[0],
                        'type': ds.type,
                        'vcenter': vc.vcenter.name,
                        'target': vc.vcenter.target,
                        'token': vc.vcenter.token,
                        }
                # self.amount_resources[target]['vcenters'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['datastores'] = tree
        return tree

    def provide_clusters(self) -> dict:
        tree = dict()
        for vrops in self.vrops_list:
            for vcenter in vrops.vc:
                vc = vrops.vc[vcenter]
                tree[vc.vcenter.name] = dict()
                for cl in vc.cluster:
                    parent_uuid = [dc.uuid for dc in vc.datacenter if dc.uuid == cl.parent]
                    parent_name = [dc.name for dc in vc.datacenter if dc.uuid == cl.parent]
                    tree[vc.vcenter.name][cl.uuid] = {
                        'uuid': cl.uuid,
                        'name': cl.name,
                        'internal_name': cl.internal_name,
                        'parent_dc_uuid': parent_uuid[0],
                        'parent_dc_name': parent_name[0],
                        'vcenter': vc.vcenter.name,
                        'target': vc.vcenter.target,
                        'token': vc.vcenter.token,
                        }
                # self.amount_resources[target]['vcenters'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['clusters'] = tree
        return tree

    def provide_hosts(self) -> dict:
        tree = dict()
        for vrops in self.vrops_list:
            for vcenter in vrops.vc:
                vc = vrops.vc[vcenter]
                tree[vc.vcenter.name] = dict()
                for ho in vc.hosts:
                    parent_uuid = [cl.uuid for cl in vc.cluster if cl.uuid == ho.parent]
                    parent_name = [cl.name for cl in vc.cluster if cl.uuid == ho.parent]
                    tree[vc.vcenter.name][ho.uuid] = {
                        'uuid': ho.uuid,
                        'name': ho.name,
                        'internal_name': ho.internal_name,
                        'parent_cluster_uuid': parent_uuid[0],
                        'parent_cluster_name': parent_name[0],
                        'vcenter': vc.vcenter.name,
                        'target': vc.vcenter.target,
                        'token': vc.vcenter.token,
                        }
                # self.amount_resources[target]['vcenters'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['hosts'] = tree
        return tree

    def provide_vms(self) -> dict:
        tree = dict()
        for vrops in self.vrops_list:
            for vcenter in vrops.vc:
                vc = vrops.vc[vcenter]
                tree[vc.vcenter.name] = dict()
                for vm in vc.vms:
                    parent_uuid = [ho.uuid for ho in vc.hosts if ho.uuid == vm.parent]
                    parent_name = [ho.name for ho in vc.hosts if ho.uuid == vm.parent]
                    # find cluster and datacenter
                    parent_cl_name = [cl.name for cl in vc.cluster if cl.uuid == parent_uuid]
                    # we only have parent_dc_name here, no uuid, hence, comparing names
                    parent_dc_name = [dc.name for dc in vc.datacenter if dc.name == parent_cl_name]
                    tree[vc.vcenter.name][vm.uuid] = {
                        'uuid': vm.uuid,
                        'name': vm.name,
                        'internal_name': vm.internal_name,
                        'instance_uuid': vm.instance_uuid,
                        'parent_host_uuid': parent_uuid[0],
                        'parent_host_name': parent_name[0],
                        'cluster': parent_cl_name,
                        'datacenter': parent_dc_name,
                        'vcenter': vc.vcenter.name,
                        'target': vc.vcenter.target,
                        'token': vc.vcenter.token,
                        }
                # self.amount_resources[target]['vcenters'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['vms'] = tree
        return tree

    def provide_distributed_vswitches(self) -> dict:
        tree = dict()
        for vrops in self.vrops_list:
            for vcenter in vrops.vc:
                vc = vrops.vc[vcenter]
                tree[vc.vcenter.name] = dict()
                for dv in vc.distributed_virtual_switches:
                    parent_uuid = [dc.uuid for dc in vc.datacenter if dc.uuid == dv.parent]
                    parent_name = [dc.name for dc in vc.datacenter if dc.uuid == dv.parent]
                    tree[vc.vcenter.name][dv.uuid] = {
                        'uuid': dv.uuid,
                        'name': dv.name,
                        'parent_dc_uuid': parent_uuid[0],
                        'parent_dc_name': parent_name[0],
                        'vcenter': vc.vcenter.name,
                        'target': vc.vcenter.target,
                        'token': vc.vcenter.token,
                        }
                # self.amount_resources[target]['vcenters'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['distributed_virtual_switches'] = tree
        return tree

    def provide_nsxt_adapter(self) -> dict:
        tree = dict()
        for target in self.nsxt_dict:
            nsxt_adapter_list = self.nsxt_dict[target]
            if not nsxt_adapter_list:
                continue
            tree[target] = dict()
            for nsxt_adapter in nsxt_adapter_list:
                tree[target][nsxt_adapter.uuid] = {
                    'uuid': nsxt_adapter.uuid,
                    'name': nsxt_adapter.name,
                    'target': nsxt_adapter.target,
                    'token': nsxt_adapter.token,
                }
            self.amount_resources[target]['nsxt_adapter'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['nsxt_adapter'] = tree
        return tree

    def provide_nsxt_mgmt_cluster(self) -> dict:
        tree = dict()
        for target in self.nsxt_dict:
            nsxt_adapter_list = self.nsxt_dict[target]
            if not nsxt_adapter_list:
                continue
            tree[target] = dict()
            for nsxt_adapter in nsxt_adapter_list:
                for mgmt_cluster in nsxt_adapter.mgmt_cluster:
                    tree[target][mgmt_cluster.uuid] = {
                        'uuid': mgmt_cluster.uuid,
                        'name': mgmt_cluster.name,
                        'nsxt_adapter_name': nsxt_adapter.name,
                        'nsxt_adapter_uuid': nsxt_adapter.uuid,
                        'target': nsxt_adapter.target,
                        'token': nsxt_adapter.token,
                    }
            self.amount_resources[target]['nsxt_mgmt_cluster'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['nsxt_mgmt_cluster'] = tree
        return tree

    def provide_nsxt_mgmt_nodes(self) -> dict:
        tree = dict()
        for target in self.nsxt_dict:
            nsxt_adapter_list = self.nsxt_dict[target]
            if not nsxt_adapter_list:
                continue
            tree[target] = dict()
            for nsxt_adapter in nsxt_adapter_list:
                for mgmt_cluster in nsxt_adapter.mgmt_cluster:
                    for mgmt_node in mgmt_cluster.mgmt_nodes:
                        tree[target][mgmt_node.uuid] = {
                            'uuid': mgmt_node.uuid,
                            'name': mgmt_node.name,
                            'mgmt_cluster_name': mgmt_cluster.name,
                            'mgmt_cluster_uuid': mgmt_cluster.uuid,
                            'nsxt_adapter_name': nsxt_adapter.name,
                            'nsxt_adapter_uuid': nsxt_adapter.uuid,
                            'target': nsxt_adapter.target,
                            'token': nsxt_adapter.token,
                        }
            self.amount_resources[target]['nsxt_mgmt_nodes'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['nsxt_mgmt_nodes'] = tree
        return tree

    def provide_nsxt_mgmt_service(self) -> dict:
        tree = dict()
        for target in self.nsxt_dict:
            nsxt_adapter_list = self.nsxt_dict[target]
            if not nsxt_adapter_list:
                continue
            tree[target] = dict()
            for nsxt_adapter in nsxt_adapter_list:
                for mgmt_cluster in nsxt_adapter.mgmt_cluster:
                    for mgmt_node in mgmt_cluster.mgmt_nodes:
                        for mgmt_service in mgmt_node.nsxt_mgmt_services:
                            tree[nsxt_adapter.target][mgmt_service.uuid] = {
                                'uuid': mgmt_service.uuid,
                                'name': mgmt_service.name,
                                'nsxt_adapter_name': nsxt_adapter.name,
                                'nsxt_adapter_uuid': nsxt_adapter.uuid,
                                'mgmt_cluster_name': mgmt_cluster.name,
                                'mgmt_cluster_uuid': mgmt_cluster.uuid,
                                'mgmt_node_name': mgmt_node.name,
                                'mgmt_node_uuid': mgmt_node.uuid,
                                'target': nsxt_adapter.target,
                                'token': nsxt_adapter.token,
                            }
            self.amount_resources[target]['nsxt_mgmt_service'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['nsxt_mgmt_service'] = tree
        return tree

    def provide_nsxt_transport_nodes(self) -> dict:
        tree = dict()
        for target in self.nsxt_dict:
            nsxt_adapter_list = self.nsxt_dict[target]
            if not nsxt_adapter_list:
                continue
            tree[target] = dict()
            for nsxt_adapter in nsxt_adapter_list:
                for mgmt_cluster in nsxt_adapter.mgmt_cluster:
                    for transport_zone in mgmt_cluster.transport_zones:
                        for transport_node in transport_zone.nsxt_transport_nodes:
                            tree[nsxt_adapter.target][transport_node.uuid] = {
                                'uuid': transport_node.uuid,
                                'name': transport_node.name,
                                'nsxt_adapter_name': nsxt_adapter.name,
                                'nsxt_adapter_uuid': nsxt_adapter.uuid,
                                'mgmt_cluster_name': mgmt_cluster.name,
                                'mgmt_cluster_uuid': mgmt_cluster.uuid,
                                'transport_zone_name': transport_zone.name,
                                'transport_zone_uuid': transport_zone.uuid,
                                'target': nsxt_adapter.target,
                                'token': nsxt_adapter.token,
                            }
            self.amount_resources[target]['nsxt_transport_nodes'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['nsxt_transport_nodes'] = tree
        return tree

    def provide_nsxt_logical_switches(self) -> dict:
        tree = dict()
        for target in self.nsxt_dict:
            nsxt_adapter_list = self.nsxt_dict[target]
            if not nsxt_adapter_list:
                continue
            tree[target] = dict()
            for nsxt_adapter in nsxt_adapter_list:
                for mgmt_cluster in nsxt_adapter.mgmt_cluster:
                    for logical_switch in mgmt_cluster.logical_switches:
                        tree[target][logical_switch.uuid] = {
                            'uuid': logical_switch.uuid,
                            'name': logical_switch.name,
                            'mgmt_cluster_name': mgmt_cluster.name,
                            'mgmt_cluster_uuid': mgmt_cluster.uuid,
                            'nsxt_adapter_name': nsxt_adapter.name,
                            'nsxt_adapter_uuid': nsxt_adapter.uuid,
                            'target': nsxt_adapter.target,
                            'token': nsxt_adapter.token,
                        }
            self.amount_resources[target]['nsxt_logical_switches'] = len(tree[target])
        self.iterated_inventory[str(self.iteration)]['nsxt_logical_switches'] = tree
        return tree

    def provide_vcops_objects(self) -> dict:
        tree = dict()
        for target in self.vcops_dict:
            vcops_adapter = self.vcops_dict[target]
            if not vcops_adapter:
                continue
            tree[target] = dict()
            for vcops_object in vcops_adapter.vcops_objects:
                tree[target][vcops_object.uuid] = {
                    'uuid': vcops_object.uuid,
                    'name': vcops_object.name,
                    'resourcekind': vcops_object.resourcekind,
                    'target': target
                }
        self.iterated_inventory[str(self.iteration)]['vcops_objects'] = tree
        return tree

    def provide_sddc_objects(self) -> dict:
        tree = dict()
        for target in self.sddc_dict:
            sddc_adapter_instances = self.sddc_dict[target]
            if not sddc_adapter_instances:
                continue
            tree[target] = dict()
            for sddc_health_adapter in sddc_adapter_instances:
                for sddc_object in sddc_health_adapter.sddc_health_objects:
                    tree[target][sddc_object.uuid] = {
                        'uuid': sddc_object.uuid,
                        'name': sddc_object.name,
                        'resourcekind': sddc_object.resourcekind,
                        'target': target
                    }
        self.iterated_inventory[str(self.iteration)]['sddc_objects'] = tree
        return tree
