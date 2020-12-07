from flask import Flask
from gevent.pywsgi import WSGIServer
from threading import Thread
from resources.Vcenter import Vcenter
from tools.Vrops import Vrops
import time
import json
import os
import logging

logger = logging.getLogger('vrops-exporter')


class InventoryBuilder:
    def __init__(self, json, port, sleep):
        self.json = json
        self.port = int(port)
        self.sleep = sleep
        self._user = os.environ["USER"]
        self._password = os.environ["PASSWORD"]
        self.vcenter_dict = dict()
        self.target_tokens = dict()
        self.iterated_inventory = dict()
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
            return self.iterated_inventory[str(iteration)]['vcenters'][target]

        @app.route('/<target>/datacenters/<int:iteration>', methods=['GET'])
        def datacenters(target, iteration):
            return self.iterated_inventory[str(iteration)]['datacenters'][target]

        @app.route('/<target>/clusters/<int:iteration>', methods=['GET'])
        def clusters(target, iteration):
            return self.iterated_inventory[str(iteration)]['clusters'][target]

        @app.route('/<target>/hosts/<int:iteration>', methods=['GET'])
        def hosts(target, iteration):
            return self.iterated_inventory[str(iteration)]['hosts'][target]

        @app.route('/<target>/datastores/<int:iteration>', methods=['GET'])
        def datastores(target, iteration):
            return self.iterated_inventory[str(iteration)]['datastores'][target]

        @app.route('/<target>/vms/<int:iteration>', methods=['GET'])
        def vms(target, iteration):
            return self.iterated_inventory[str(iteration)]['vms'][target]

        @app.route('/iteration', methods=['GET'])
        def iteration():
            return_iteration = self.successful_iteration_list[-1]
            return str(return_iteration)

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
        with open(self.json) as json_file:
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
            for vrops in self.vrops_list:
                if not self.query_vrops(vrops):
                    logger.warning(f'retrying connection to {vrops} in next iteration {self.iteration + 1}')
            self.get_vcenters()
            self.get_datacenters()
            self.get_clusters()
            self.get_hosts()
            self.get_datastores()
            self.get_vms()
            if len(self.iterated_inventory[str(self.iteration)]['vcenters']) > 0:
                self.successful_iteration_list.append(self.iteration)
            else:
                # immediately withdraw faulty inventory
                logger.debug(f'Withdrawing current iteration: {self.iteration}')
                self.iterated_inventory.pop(str(self.iteration))
            self.iteration += 1
            logger.info(f'Inventory relaxing before going to work again')
            time.sleep(int(self.sleep))

    def query_vrops(self, vrops):
        logger.info(f'Querying {vrops}')
        token = Vrops.get_token(target=vrops)
        if not token:
            return False
        self.target_tokens[vrops] = token

        logger.info(f'##############################################')
        logger.info(f'##########  Collecting resources... ##########')
        logger.info(f'##############################################')

        vcenter = self.create_resource_objects(vrops, token)
        self.vcenter_dict[vrops] = vcenter
        return True

    def create_resource_objects(self, vrops, token):
        for adapter in Vrops.get_adapter(target=vrops, token=token):
            logger.debug(f'Collecting vcenter: {adapter["name"]}')
            vcenter = Vcenter(target=vrops, token=token, name=adapter['name'], uuid=adapter['uuid'])
            vcenter.add_datacenter()
            for dc_object in vcenter.datacenter:
                logger.debug(f'Collecting datacenter: {dc_object.name}')
                dc_object.add_cluster()
                for cl_object in dc_object.clusters:
                    logger.debug(f'Collecting cluster: {cl_object.name}')
                    cl_object.add_host()
                    for hs_object in cl_object.hosts:
                        logger.debug(f'Collecting host: {hs_object.name}')
                        hs_object.add_datastore()
                        for ds_object in hs_object.datastores:
                            logger.debug(f'Collecting datastore: {ds_object.name}')
                        hs_object.add_vm()
                        for vm_object in hs_object.vms:
                            logger.debug(f'Collecting VM: {vm_object.name}')
            return vcenter

    def get_vcenters(self):
        tree = dict()
        for vcenter_entry in self.vcenter_dict:
            vcenter = self.vcenter_dict[vcenter_entry]
            tree[vcenter.target] = dict()
            tree[vcenter.target][vcenter.uuid] = {
                'uuid': vcenter.uuid,
                'name': vcenter.name,
                'target': vcenter.target,
                'token': vcenter.token,
            }
        self.iterated_inventory[str(self.iteration)]['vcenters'] = tree
        return tree

    def get_datacenters(self):
        tree = dict()
        for vcenter_entry in self.vcenter_dict:
            vcenter = self.vcenter_dict[vcenter_entry]
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                tree[vcenter.target][dc.uuid] = {
                    'uuid': dc.uuid,
                    'name': dc.name,
                    'parent_vcenter_uuid': vcenter.uuid,
                    'parent_vcenter_name': vcenter.name,
                    'vcenter': vcenter.name,
                    'target': dc.target,
                    'token': dc.token,
                }
        self.iterated_inventory[str(self.iteration)]['datacenters'] = tree
        return tree

    def get_clusters(self):
        tree = dict()
        for vcenter_entry in self.vcenter_dict:
            vcenter = self.vcenter_dict[vcenter_entry]
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                for cluster in dc.clusters:
                    tree[vcenter.target][cluster.uuid] = {
                        'uuid': cluster.uuid,
                        'name': cluster.name,
                        'parent_dc_uuid': dc.uuid,
                        'parent_dc_name': dc.name,
                        'vcenter': vcenter.name,
                        'target': cluster.target,
                        'token': cluster.token,
                    }
        self.iterated_inventory[str(self.iteration)]['clusters'] = tree
        return tree

    def get_hosts(self):
        tree = dict()
        for vcenter_entry in self.vcenter_dict:
            vcenter = self.vcenter_dict[vcenter_entry]
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
                            'target': host.target,
                            'token': host.token,
                        }
        self.iterated_inventory[str(self.iteration)]['hosts'] = tree
        return tree

    def get_datastores(self):
        tree = dict()
        for vcenter_entry in self.vcenter_dict:
            vcenter = self.vcenter_dict[vcenter_entry]
            tree[vcenter.target] = dict()
            for dc in vcenter.datacenter:
                for cluster in dc.clusters:
                    for host in cluster.hosts:
                        for ds in host.datastores:
                            tree[vcenter.target][ds.uuid] = {
                                'uuid': ds.uuid,
                                'name': ds.name,
                                'type': ds.type,
                                'parent_host_uuid': host.uuid,
                                'parent_host_name': host.name,
                                'cluster': cluster.name,
                                'datacenter': dc.name,
                                'vcenter': vcenter.name,
                                'target': ds.target,
                                'token': ds.token,
                            }
        self.iterated_inventory[str(self.iteration)]['datastores'] = tree
        return tree

    def get_vms(self):
        tree = dict()
        for vcenter_entry in self.vcenter_dict:
            vcenter = self.vcenter_dict[vcenter_entry]
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
                                'target': vm.target,
                                'token': vm.token,
                            }
        self.iterated_inventory[str(self.iteration)]['vms'] = tree
        return tree
