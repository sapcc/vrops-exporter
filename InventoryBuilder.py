from flask import Flask
from gevent.pywsgi import WSGIServer
from threading import Thread
from resources.Resourceskinds import NSXTMgmtPlane
from tools.Vrops import Vrops
import time
import json
import os
import logging

logger = logging.getLogger('vrops-exporter')


class InventoryBuilder:
    def __init__(self, atlas_config, port, sleep, timeout):
        self.atlas_config = atlas_config
        self.port = int(port)
        self.sleep = sleep
        self.timeout = int(timeout)
        self._user = os.environ["USER"]
        self._password = os.environ["PASSWORD"]
        self.vcenter_dict = dict()
        self.nsxt_dict = dict()
        self.target_tokens = dict()
        self.iterated_inventory = dict()
        self.vrops_collection_times = dict()
        self.response_codes = dict()
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
            return self.iterated_inventory[str(iteration)]['vcenters'].get(target, {})

        @app.route('/<target>/datacenters/<int:iteration>', methods=['GET'])
        def datacenters(target, iteration):
            return self.iterated_inventory[str(iteration)]['datacenters'].get(target, {})

        @app.route('/<target>/clusters/<int:iteration>', methods=['GET'])
        def clusters(target, iteration):
            return self.iterated_inventory[str(iteration)]['clusters'].get(target, {})

        @app.route('/<target>/hosts/<int:iteration>', methods=['GET'])
        def hosts(target, iteration):
            return self.iterated_inventory[str(iteration)]['hosts'].get(target, {})

        @app.route('/<target>/datastores/<int:iteration>', methods=['GET'])
        def datastores(target, iteration):
            return self.iterated_inventory[str(iteration)]['datastores'].get(target, {})

        @app.route('/<target>/vms/<int:iteration>', methods=['GET'])
        def vms(target, iteration):
            return self.iterated_inventory[str(iteration)]['vms'].get(target, {})

        @app.route('/<target>/nsxt_adapter/<int:iteration>', methods=['GET'])
        def nsxt_adapter(target, iteration):
            return self.iterated_inventory[str(iteration)]['nsxt_adapter'].get(target, {})

        @app.route('/<target>/nsxt_mgmt_cluster/<int:iteration>', methods=['GET'])
        def nsxt_mgmt_cluster(target, iteration):
            return self.iterated_inventory[str(iteration)]['nsxt_mgmt_cluster'].get(target, {})

        @app.route('/<target>/nsxt_mgmt_nodes/<int:iteration>', methods=['GET'])
        def nsxt_mgmt_nodes(target, iteration):
            return self.iterated_inventory[str(iteration)]['nsxt_mgmt_nodes'].get(target, {})

        @app.route('/<target>/nsxt_mgmt_service/<int:iteration>', methods=['GET'])
        def nsxt_mgmt_service(target, iteration):
            return self.iterated_inventory[str(iteration)]['nsxt_mgmt_service'].get(target, {})

        @app.route('/alertdefinitions/', methods=['GET'])
        def alert_alertdefinitions():
            return self.alertdefinitions

        @app.route('/iteration', methods=['GET'])
        def iteration():
            return_iteration = self.successful_iteration_list[-1]
            return str(return_iteration)

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

    def get_vrops(self):
        with open(self.atlas_config) as json_file:
            netbox_json = json.load(json_file)
        self.vrops_list = [target['labels']['server_name'] for target in netbox_json if
                           target['labels']['job'] == "vrops"]

    def query_inventory_permanent(self):
        # first iteration to fill is 1. while this is not ready,
        # curl to /iteration would still report 0 to wait for actual data
        self.iteration = 1
        while True:
            # get vrops targets every run in case we have new targets appearing
            self.get_vrops()
            if len(self.successful_iteration_list) > 3:
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
            for vrops in self.vrops_list:
                self.response_codes[vrops] = dict()
                vrops_short_name = vrops.split('.')[0]
                thread = Thread(target=self.query_vrops, args=(vrops, vrops_short_name, self.iteration))
                thread.start()
                threads.append((thread, vrops))

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
            for vrops in joined_threads:
                self.vrops_collection_times[vrops] = joined_threads[vrops]
                logger.info(f"Fetched {vrops} in {joined_threads[vrops]}s")

            self.provide_vcenters()
            self.provide_datacenters()
            self.provide_clusters()
            self.provide_hosts()
            self.provide_datastores()
            self.provide_vms()
            self.provide_nsxt_adapter()
            self.provide_nsxt_mgmt_cluster()
            self.provide_nsxt_mgmt_nodes()
            self.provide_nsxt_mgmt_service()
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

    def query_vrops(self, target, vrops_short_name, iteration):
        vrops = Vrops()
        logger.info(f'Querying {target}')
        token, self.response_codes[target]["token"] = Vrops.get_token(target=target)
        if not token:
            logger.warning(f'retrying connection to {target} in next iteration {self.iteration + 1}')
            return False
        self.target_tokens[target] = token

        logger.info(f'##########  Collecting resources {vrops_short_name}... ##########')

        vcenter = self.create_vcenter_objects(vrops, target, token)
        nsxt_adapter = self.create_nsxt_objects(vrops, target, token)

        self.vcenter_dict[vrops] = vcenter
        self.nsxt_dict[vrops] = nsxt_adapter

        if iteration == 1:
            self.alertdefinitions = Vrops.get_alertdefinitions(vrops, target, token)
        return True

    def create_vcenter_objects(self, vrops, target: str, token: str):
        vcenter_adapter, self.response_codes[target]["vcenter"] = Vrops.get_vcenter_adapter(vrops, target, token)
        # just one vcenter adapter supported
        vcenter_adapter = vcenter_adapter[0]

        if not vcenter_adapter:
            logger.critical(f'Could not get vcenter adapter!')
            return False
        logger.debug(f'Collecting vcenter: {vcenter_adapter.name}')

        datacenter, self.response_codes[target]["datacenters"] = \
            Vrops.get_datacenter(vrops, target, token, [vcenter_adapter.uuid])
        cluster, self.response_codes[target]["clusters"] = \
            Vrops.get_cluster(vrops, target, token, [dc.uuid for dc in datacenter])
        datastores, self.response_codes[target]["datastores"] = \
            Vrops.get_datastores(vrops, target, token, [dc.uuid for dc in datacenter])
        hosts, self.response_codes[target]["hosts"] = \
            Vrops.get_hosts(vrops, target, token, [cl.uuid for cl in cluster])
        vms, self.response_codes[target]["vms"] = \
            Vrops.get_vms(vrops, target, token, [hs.uuid for hs in hosts], vcenter_adapter.uuid)

        for dc in datacenter:
            vcenter_adapter.add_datacenter(dc)
        for dc_object in vcenter_adapter.datacenter:
            logger.debug(f'Collecting datacenter: {dc_object.name}')
            for ds in datastores:
                if ds.parent == dc_object.uuid:
                    dc_object.add_datastore(ds)
                    logger.debug(f'Collecting datastore: {ds.name}')
            for cl in cluster:
                dc_object.add_cluster(cl)
            for cl_object in dc_object.clusters:
                logger.debug(f'Collecting cluster: {cl_object.name}')
                for hs in hosts:
                    if hs.parent == cl_object.uuid:
                        cl_object.add_host(hs)
                for hs_object in cl_object.hosts:
                    logger.debug(f'Collecting host: {hs_object.name}')
                    for vm in vms:
                        if vm.parent == hs_object.uuid:
                            hs_object.add_vm(vm)
                            logger.debug(f'Collecting VM: {vm.name}')
        return vcenter_adapter

    def create_nsxt_objects(self, vrops, target: str, token: str):
        nsxt_adapter, self.response_codes[target]["nsxt_adapter"] = Vrops.get_nsxt_adapter(vrops, target, token)
        if not nsxt_adapter:
            return False

        nsxt_mgmt_plane = NSXTMgmtPlane(target, token)
        for adapter in nsxt_adapter:
            logger.debug(f'Collecting NSX-T adapter: {adapter.name}')
            nsxt_mgmt_plane.add_adapter(adapter)

        nsxt_mgmt_cluster, self.response_codes[target]["nsxt_mgmt_cluster"] = \
            Vrops.get_nsxt_mgmt_cluster(vrops, target,token,[a.uuid for a in nsxt_adapter])
        nsxt_mgmt_nodes, self.response_codes[target]["nsxt_mgmt_nodes"] = \
            Vrops.get_nsxt_mgmt_nodes(vrops, target, token, [c.uuid for c in nsxt_mgmt_cluster])
        nsxt_mgmt_service, self.response_codes[target]["nsxt_mgmt_services"] = \
            Vrops.get_nsxt_mgmt_service(vrops, target, token, [n.uuid for n in nsxt_mgmt_nodes])

        for nsxt_adapter_object in nsxt_mgmt_plane.adapter:
            for mgmt_cluster in nsxt_mgmt_cluster:
                if mgmt_cluster.parent == nsxt_adapter_object.uuid:
                    nsxt_adapter_object.add_mgmt_cluster(mgmt_cluster)
                    logger.debug(f'Collecting NSX-T management cluster: {mgmt_cluster.name}')
            for mgmt_cluster_object in nsxt_adapter_object.management_cluster:
                for mgmt_node in nsxt_mgmt_nodes:
                    mgmt_cluster_object.add_mgmt_node(mgmt_node)
                    logger.debug(f'Collecting NSX-T management node: {mgmt_node.name}')
                for nsxt_mgmt_node in mgmt_cluster_object.management_nodes:
                    for mgmt_service_instance in nsxt_mgmt_service:
                        if mgmt_service_instance.parent == nsxt_mgmt_node.uuid:
                            nsxt_mgmt_node.add_mgmt_service(mgmt_service_instance)
                            logger.debug(f'Collecting NSX-T management service: {mgmt_service_instance.name}')

        return nsxt_mgmt_plane

    def provide_vcenters(self) -> dict:
        tree = dict()
        for vcenter_entry in self.vcenter_dict:
            vcenter = self.vcenter_dict[vcenter_entry]
            if not vcenter:
                continue
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                tree[vcenter.target][vcenter.uuid] = {
                    'uuid': vcenter.uuid,
                    'name': vcenter.name,
                    'kind_dc_name': dc.name,
                    'kind_dc_uuid': dc.uuid,
                    'target': vcenter.target,
                    'token': vcenter.token,
                }
        self.iterated_inventory[str(self.iteration)]['vcenters'] = tree
        return tree

    def provide_datacenters(self) -> dict:
        tree = dict()
        for vcenter_entry in self.vcenter_dict:
            vcenter = self.vcenter_dict[vcenter_entry]
            if not vcenter:
                continue
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                tree[vcenter.target][dc.uuid] = {
                    'uuid': dc.uuid,
                    'name': dc.name,
                    'parent_vcenter_uuid': vcenter.uuid,
                    'parent_vcenter_name': vcenter.name,
                    'vcenter': vcenter.name,
                    'target': vcenter.target,
                    'token': vcenter.token,
                }
        self.iterated_inventory[str(self.iteration)]['datacenters'] = tree
        return tree

    def provide_datastores(self) -> dict:
        tree = dict()
        for vcenter_entry in self.vcenter_dict:
            vcenter = self.vcenter_dict[vcenter_entry]
            if not vcenter:
                continue
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                for datastore in dc.datastores:
                    tree[vcenter.target][datastore.uuid] = {
                        'uuid': datastore.uuid,
                        'name': datastore.name,
                        'parent_dc_uuid': dc.uuid,
                        'parent_dc_name': dc.name,
                        'type': datastore.type,
                        'vcenter': vcenter.name,
                        'target': vcenter.target,
                        'token': vcenter.token,
                    }
        self.iterated_inventory[str(self.iteration)]['datastores'] = tree
        return tree

    def provide_clusters(self) -> dict:
        tree = dict()
        for vcenter_entry in self.vcenter_dict:
            vcenter = self.vcenter_dict[vcenter_entry]
            if not vcenter:
                continue
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                for cluster in dc.clusters:
                    tree[vcenter.target][cluster.uuid] = {
                        'uuid': cluster.uuid,
                        'name': cluster.name,
                        'parent_dc_uuid': dc.uuid,
                        'parent_dc_name': dc.name,
                        'vcenter': vcenter.name,
                        'target': vcenter.target,
                        'token': vcenter.token,
                    }
        self.iterated_inventory[str(self.iteration)]['clusters'] = tree
        return tree

    def provide_hosts(self) -> dict:
        tree = dict()
        for vcenter_entry in self.vcenter_dict:
            vcenter = self.vcenter_dict[vcenter_entry]
            if not vcenter:
                continue
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                for cluster in dc.clusters:
                    for host in cluster.hosts:
                        tree[vcenter.target][host.uuid] = {
                            'uuid': host.uuid,
                            'name': host.name,
                            'parent_cluster_uuid': cluster.uuid,
                            'parent_cluster_name': cluster.name,
                            'datacenter': dc.name,
                            'vcenter': vcenter.name,
                            'target': vcenter.target,
                            'token': vcenter.token,
                        }
        self.iterated_inventory[str(self.iteration)]['hosts'] = tree
        return tree

    def provide_vms(self) -> dict:
        tree = dict()
        for vcenter_entry in self.vcenter_dict:
            vcenter = self.vcenter_dict[vcenter_entry]
            if not vcenter:
                continue
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                for cluster in dc.clusters:
                    for host in cluster.hosts:
                        for vm in host.vms:
                            tree[vcenter.target][vm.uuid] = {
                                'uuid': vm.uuid,
                                'name': vm.name,
                                'parent_host_uuid': host.uuid,
                                'parent_host_name': host.name,
                                'cluster': cluster.name,
                                'datacenter': dc.name,
                                'vcenter': vcenter.name,
                                'target': vcenter.target,
                                'token': vcenter.token,
                            }
        self.iterated_inventory[str(self.iteration)]['vms'] = tree
        return tree

    def provide_nsxt_adapter(self) -> dict:
        tree = dict()
        for nsxt_entry in self.nsxt_dict:
            nsxt_mgmt_plane = self.nsxt_dict[nsxt_entry]
            if not nsxt_mgmt_plane:
                continue
            tree[nsxt_mgmt_plane.target] = dict()
            for nsxt_adapter in nsxt_mgmt_plane.adapter:
                tree[nsxt_mgmt_plane.target][nsxt_adapter.uuid] = {
                    'uuid': nsxt_adapter.uuid,
                    'name': nsxt_adapter.name,
                    'target': nsxt_mgmt_plane.target,
                    'token': nsxt_mgmt_plane.token,
                }
        self.iterated_inventory[str(self.iteration)]['nsxt_adapter'] = tree
        return tree

    def provide_nsxt_mgmt_cluster(self) -> dict:
        tree = dict()
        for nsxt_entry in self.nsxt_dict:
            nsxt_mgmt_plane = self.nsxt_dict[nsxt_entry]
            if not nsxt_mgmt_plane:
                continue
            tree[nsxt_mgmt_plane.target] = dict()
            for nsxt_adapter in nsxt_mgmt_plane.adapter:
                for mgmt_cluster in nsxt_adapter.management_cluster:
                    tree[nsxt_mgmt_plane.target][mgmt_cluster.uuid] = {
                        'uuid': mgmt_cluster.uuid,
                        'name': mgmt_cluster.name,
                        'nsxt_adapter_name': nsxt_adapter.name,
                        'nsxt_adapter_uuid': nsxt_adapter.uuid,
                        'target': nsxt_mgmt_plane.target,
                        'token': nsxt_mgmt_plane.token,
                    }
        self.iterated_inventory[str(self.iteration)]['nsxt_mgmt_cluster'] = tree
        return tree

    def provide_nsxt_mgmt_nodes(self) -> dict:
        tree = dict()
        for nsxt_entry in self.nsxt_dict:
            nsxt_mgmt_plane = self.nsxt_dict[nsxt_entry]
            if not nsxt_mgmt_plane:
                continue
            tree[nsxt_mgmt_plane.target] = dict()
            for nsxt_adapter_object in nsxt_mgmt_plane.adapter:
                for mgmt_cluster in nsxt_adapter_object.management_cluster:
                    for mgmt_node in mgmt_cluster.management_nodes:
                        tree[nsxt_mgmt_plane.target][mgmt_node.uuid] = {
                            'uuid': mgmt_node.uuid,
                            'name': mgmt_node.name,
                            'mgmt_cluster_name': mgmt_cluster.name,
                            'mgmt_cluster_uuid': mgmt_cluster.uuid,
                            'nsxt_adapter_name': nsxt_adapter_object.name,
                            'nsxt_adapter_uuid': nsxt_adapter_object.uuid,
                            'target': nsxt_mgmt_plane.target,
                            'token': nsxt_mgmt_plane.token,
                        }
        self.iterated_inventory[str(self.iteration)]['nsxt_mgmt_nodes'] = tree
        return tree

    def provide_nsxt_mgmt_service(self) -> dict:
        tree = dict()
        for nsxt_entry in self.nsxt_dict:
            nsxt_mgmt_plane = self.nsxt_dict[nsxt_entry]
            if not nsxt_mgmt_plane:
                continue
            tree[nsxt_mgmt_plane.target] = dict()
            for nsxt_adapter_object in nsxt_mgmt_plane.adapter:
                for mgmt_cluster in nsxt_adapter_object.management_cluster:
                    for mgmt_node in mgmt_cluster.management_nodes:
                        for mgmt_service in mgmt_node.management_service:
                            tree[nsxt_mgmt_plane.target][mgmt_service.uuid] = {
                                'uuid': mgmt_service.uuid,
                                'name': mgmt_service.name,
                                'nsxt_adapter_name': nsxt_adapter_object.name,
                                'nsxt_adapter_uuid': nsxt_adapter_object.uuid,
                                'mgmt_cluster_name': mgmt_cluster.name,
                                'mgmt_cluster_uuid': mgmt_cluster.uuid,
                                'mgmt_node_name': mgmt_node.name,
                                'mgmt_node_uuid': mgmt_node.uuid,
                                'target': nsxt_mgmt_plane.target,
                                'token': nsxt_mgmt_plane.token,
                            }
        self.iterated_inventory[str(self.iteration)]['nsxt_mgmt_service'] = tree
        return tree
