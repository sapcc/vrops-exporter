from flask import Flask
from gevent.pywsgi import WSGIServer
from threading import Thread
from tools.Vrops import Vrops
from tools.helper import yaml_read
import time
import json
import os
import logging

logger = logging.getLogger('vrops-exporter')


class InventoryBuilder:
    def __init__(self, atlas_config, port, sleep, timeout):
        self.atlas_config = atlas_config
        self.inventory_config = self.read_inventory_config()
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

        @app.route('/<target>/vcops_self_monitoring_objects/<int:iteration>', methods=['GET'])
        def vcops_self_monitoring_objects(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('vcops_self_monitoring_objects', {}).get(target,
                                                                                                                {})

        @app.route('/<target>/sddc_health_objects/<int:iteration>', methods=['GET'])
        def sddc_health_objects(target, iteration):
            return self.iterated_inventory.get(str(iteration), {}).get('sddc_health_objects', {}).get(target, {})

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

    def read_inventory_config(self):
        config_file = yaml_read(os.environ['INVENTORY_CONFIG'])
        return config_file

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
            self.read_inventory_config()
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
            self.provide_distributed_vswitches()
            self.provide_nsxt_adapter()
            self.provide_nsxt_mgmt_cluster()
            self.provide_nsxt_mgmt_nodes()
            self.provide_nsxt_mgmt_service()
            self.provide_nsxt_transport_nodes()
            self.provide_nsxt_logical_switches()
            self.provide_vcops_self_monitoring_objects()
            self.provide_sddc_health_objects()
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
        vcops_adapter = self.create_vcops_objects(vrops, target, token)
        sddc_adapter = self.create_sddc_health_objects(vrops, target, token)

        self.vcenter_dict[target] = vcenter
        self.nsxt_dict[target] = nsxt_adapter
        self.vcops_dict[target] = vcops_adapter
        self.sddc_dict[target] = sddc_adapter

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

        query_specs = self.inventory_config.get('query_specs', {})

        datacenter, self.response_codes[target]["datacenters"] = \
            Vrops.get_datacenter(vrops, target, token, [vcenter_adapter.uuid],
                                 query_specs=query_specs.get('default', {}))
        cluster, self.response_codes[target]["clusters"] = \
            Vrops.get_cluster(vrops, target, token, [dc.uuid for dc in datacenter],
                              query_specs=query_specs.get('default', {}))
        datastores, self.response_codes[target]["datastores"] = \
            Vrops.get_datastores(vrops, target, token, [dc.uuid for dc in datacenter],
                                 query_specs=query_specs.get('default', {}))
        hosts, self.response_codes[target]["hosts"] = \
            Vrops.get_hosts(vrops, target, token, [cl.uuid for cl in cluster],
                            query_specs=query_specs.get('hostsystems', {}))
        vms, self.response_codes[target]["vms"] = \
            Vrops.get_vms(vrops, target, token, [hs.uuid for hs in hosts], vcenter_adapter.uuid,
                          query_specs=query_specs.get('virtual_machines', {}))
        distributed_virtual_switchs, self.response_codes[target]["distributed_virtual_switch"] = \
            Vrops.get_dis_virtual_switch(vrops, target, token, [dc.uuid for dc in datacenter],
                                         query_specs=query_specs.get('default', {}))

        vcenter_adapter.datacenter = list()
        for dc in datacenter:
            vcenter_adapter.datacenter.append(dc)
            logger.debug(f'Collecting datacenter: {dc.name}')

        for dc_object in vcenter_adapter.datacenter:
            dc_object.datastores = list()
            dc_object.clusters = list()
            dc_object.dvss = list()

            for ds in datastores:
                if ds.parent == dc_object.uuid:
                    dc_object.datastores.append(ds)
                    logger.debug(f'Collecting datastore: {ds.name}')
            for cl in cluster:
                if cl.parent == dc_object.uuid:
                    dc_object.clusters.append(cl)
                    logger.debug(f'Collecting cluster: {cl.name}')
            for cl_object in dc_object.clusters:
                cl_object.hosts = list()
                for hs in hosts:
                    if hs.parent == cl_object.uuid:
                        cl_object.hosts.append(hs)
                        logger.debug(f'Collecting host: {hs.name}')
                for hs_object in cl_object.hosts:
                    hs_object.vms = list()
                    for vm in vms:
                        if vm.parent == hs_object.uuid:
                            hs_object.vms.append(vm)
                            logger.debug(f'Collecting VM: {vm.name}')
            for dvs in distributed_virtual_switchs:
                if dvs.parent == dc_object.uuid:
                    dc_object.dvss.append(dvs)
                    logger.debug(f'Collecting distributed virtual switch: {dvs.name}')
        return vcenter_adapter

    def create_nsxt_objects(self, vrops, target: str, token: str):
        nsxt_adapter_list, self.response_codes[target]["nsxt_adapter"] = Vrops.get_nsxt_adapter(vrops, target, token)
        if not nsxt_adapter_list:
            logger.critical(f'Could not get any nsxt adapter!')
            return False

        query_specs = self.inventory_config.get('query_specs', {})

        nsxt_mgmt_cluster, self.response_codes[target]["nsxt_mgmt_cluster"] = \
            Vrops.get_nsxt_mgmt_cluster(vrops, target, token, [a.uuid for a in nsxt_adapter_list],
                                        query_specs=query_specs.get('default', {}))
        nsxt_mgmt_nodes, self.response_codes[target]["nsxt_mgmt_nodes"] = \
            Vrops.get_nsxt_mgmt_nodes(vrops, target, token, [c.uuid for c in nsxt_mgmt_cluster],
                                      query_specs=query_specs.get('default', {}))
        nsxt_mgmt_service, self.response_codes[target]["nsxt_mgmt_services"] = \
            Vrops.get_nsxt_mgmt_service(vrops, target, token, [n.uuid for n in nsxt_mgmt_nodes],
                                        query_specs=query_specs.get('default', {}))
        nsxt_transport_zones, self.response_codes[target]["nsxt_transport_zones"] = \
            Vrops.get_nsxt_transport_zone(vrops, target, token, [c.uuid for c in nsxt_mgmt_cluster],
                                          query_specs=query_specs.get('default', {}))
        nsxt_transport_nodes, self.response_codes[target]["nsxt_transport_nodes"] = \
            Vrops.get_nsxt_transport_node(vrops, target, token, [z.uuid for z in nsxt_transport_zones],
                                          query_specs=query_specs.get('default', {}))
        nsxt_logical_switches, self.response_codes[target]["nsxt_logical_switches"] = \
            Vrops.get_nsxt_logical_switch(vrops, target, token, [c.uuid for c in nsxt_mgmt_cluster],
                                          query_specs=query_specs.get('default', {}))

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

    def create_vcops_objects(self, vrops, target: str, token: str):
        vcops_adapter_instance, self.response_codes[target]["vcops_adapter"] = \
            Vrops.get_vcenter_operations_adapter_intance(vrops, target, token)
        vcops_adapter_instance = vcops_adapter_instance[0]
        if not vcops_adapter_instance:
            logger.critical(f'Could not get vcops adapter!')
            return False

        resourcekinds = [rk for rk in self.inventory_config.get('resourcekinds', {}).get('vcops_resourcekinds', [])]
        query_specs = self.inventory_config.get('query_specs', {})

        vcops_objects, self.response_codes[target]["vcops_self_monitoring_objects"] = \
            Vrops.get_vcops_instances(vrops, target, token, parent_uuids=[vcops_adapter_instance.uuid],
                                      resourcekinds=resourcekinds, query_specs=query_specs)
        vcops_adapter_instance.vcops_objects = list()
        for vcops_object in vcops_objects:
            vcops_adapter_instance.vcops_objects.append(vcops_object)

        return vcops_adapter_instance

    def create_sddc_health_objects(self, vrops, target: str, token: str):
        sddc_adapter_instances, self.response_codes[target]["sddc_health_adapter"] = \
            Vrops.get_sddc_health_adapter_intance(vrops, target, token)

        if not sddc_adapter_instances:
            return False

        resourcekinds = [rk for rk in self.inventory_config.get('resourcekinds', {}).get('sddc_resourcekinds', [])]
        query_specs = self.inventory_config.get('query_specs', {})

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
        for target in self.vcenter_dict:
            vcenter = self.vcenter_dict[target]
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
        for target in self.vcenter_dict:
            vcenter = self.vcenter_dict[target]
            if not vcenter:
                continue
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                tree[vcenter.target][dc.uuid] = {
                    'uuid': dc.uuid,
                    'name': dc.name,
                    'internal_name': dc.internal_name,
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
        for target in self.vcenter_dict:
            vcenter = self.vcenter_dict[target]
            if not vcenter:
                continue
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                for datastore in dc.datastores:
                    tree[vcenter.target][datastore.uuid] = {
                        'uuid': datastore.uuid,
                        'name': datastore.name,
                        'internal_name': datastore.internal_name,
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
        for target in self.vcenter_dict:
            vcenter = self.vcenter_dict[target]
            if not vcenter:
                continue
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                for cluster in dc.clusters:
                    tree[vcenter.target][cluster.uuid] = {
                        'uuid': cluster.uuid,
                        'name': cluster.name,
                        'internal_name': cluster.internal_name,
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
        for target in self.vcenter_dict:
            vcenter = self.vcenter_dict[target]
            if not vcenter:
                continue
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                for cluster in dc.clusters:
                    for host in cluster.hosts:
                        tree[vcenter.target][host.uuid] = {
                            'uuid': host.uuid,
                            'name': host.name,
                            'internal_name': host.internal_name,
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
        for target in self.vcenter_dict:
            vcenter = self.vcenter_dict[target]
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
                                'internal_name': vm.internal_name,
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

    def provide_distributed_vswitches(self) -> dict:
        tree = dict()
        for target in self.vcenter_dict:
            vcenter = self.vcenter_dict[target]
            if not vcenter:
                continue
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                for dvs in dc.dvss:
                    tree[vcenter.target][dvs.uuid] = {
                        'uuid': dvs.uuid,
                        'name': dvs.name,
                        'parent_dc_uuid': dc.uuid,
                        'parent_dc_name': dc.name,
                        'vcenter': vcenter.name,
                        'target': vcenter.target,
                        'token': vcenter.token,
                    }
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
        self.iterated_inventory[str(self.iteration)]['nsxt_logical_switches'] = tree
        return tree

    def provide_vcops_self_monitoring_objects(self) -> dict:
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
        self.iterated_inventory[str(self.iteration)]['vcops_self_monitoring_objects'] = tree
        return tree

    def provide_sddc_health_objects(self) -> dict:
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
        self.iterated_inventory[str(self.iteration)]['sddc_health_objects'] = tree
        return tree
