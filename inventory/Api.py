from threading import Thread
from flask import Flask
from gevent.pywsgi import WSGIServer
import logging
import json
import os

logger = logging.getLogger('vrops-exporter')


class InventoryApi:
    def __init__(self, builder, port):
        self.builder = builder
        self.port = int(port)
        self.wsgi_address = '0.0.0.0'
        if 'LOOPBACK' in os.environ:
            if os.environ['LOOPBACK'] == '1':
                self.wsgi_address = '127.0.0.1'
        thread = Thread(target=self.run_rest_server)
        thread.start()

    def run_rest_server(self):

        app = Flask(__name__)
        logger.info(f'serving /target on {self.port}')

        @app.route('/target', methods=['GET'])
        def target():
            return json.dumps(self.builder.target)

        logger.info(f'serving /inventory on  {self.port}')

        @app.route('/<target>/vcenters/<int:iteration>', methods=['GET'])
        def vcenters(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('vcenters', {}).get(target, {})

        @app.route('/<target>/datacenters/<int:iteration>', methods=['GET'])
        def datacenters(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('datacenters', {}).get(target, {})

        @app.route('/<target>/clusters/<int:iteration>', methods=['GET'])
        def clusters(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('clusters', {}).get(target, {})

        @app.route('/<target>/hosts/<int:iteration>', methods=['GET'])
        def hosts(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('hosts', {}).get(target, {})

        @app.route('/<target>/datastores/<int:iteration>', methods=['GET'])
        def datastores(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('datastores', {}).get(target, {})

        @app.route('/<target>/storagepod/<int:iteration>', methods=['GET'])
        def storagepod(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('storagepod', {}).get(target, {})

        @app.route('/<target>/vms/<int:iteration>', methods=['GET'])
        def vms(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('vms', {}).get(target, {})

        @app.route('/<target>/dvs/<int:iteration>', methods=['GET'])
        def distributed_virtual_switches(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('distributed_virtual_switches', {}).get(
                    target, {})

        @app.route('/<target>/nsxt_adapter/<int:iteration>', methods=['GET'])
        def nsxt_adapter(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('nsxt_adapter', {}).get(target, {})

        @app.route('/<target>/nsxt_mgmt_cluster/<int:iteration>', methods=['GET'])
        def nsxt_mgmt_cluster(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('nsxt_mgmt_cluster', {}).get(target, {})

        @app.route('/<target>/nsxt_mgmt_nodes/<int:iteration>', methods=['GET'])
        def nsxt_mgmt_nodes(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('nsxt_mgmt_nodes', {}).get(target, {})

        @app.route('/<target>/nsxt_mgmt_service/<int:iteration>', methods=['GET'])
        def nsxt_mgmt_service(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('nsxt_mgmt_service', {}).get(target, {})

        @app.route('/<target>/nsxt_transport_nodes/<int:iteration>', methods=['GET'])
        def nsxt_transport_nodes(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('nsxt_transport_nodes', {}).get(target,
                                                                                                               {})

        @app.route('/<target>/nsxt_logical_switches/<int:iteration>', methods=['GET'])
        def nsxt_logical_switches(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('nsxt_logical_switches', {}).get(target,
                                                                                                                {})

        @app.route('/<target>/vcops_objects/<int:iteration>', methods=['GET'])
        def vcops_self_monitoring_objects(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('vcops_objects', {}).get(target, {})

        @app.route('/<target>/sddc_objects/<int:iteration>', methods=['GET'])
        def sddc_health_objects(target, iteration):
            return self.builder.iterated_inventory.get(str(iteration), {}).get('sddc_objects', {}).get(target, {})

        @app.route('/alertdefinitions/<alert_id>', methods=['GET'])
        def alert_alertdefinition(alert_id):
            return self.builder.alertdefinitions.get(alert_id, {})

        @app.route('/alertdefinitions', methods=['GET'])
        def alert_alertdefinitions():
            return self.builder.alertdefinitions

        @app.route('/iteration', methods=['GET'])
        def iteration():
            return_iteration = self.builder.successful_iteration_list[-1]
            return str(return_iteration)

        @app.route('/amount_resources', methods=['GET'])
        def amount_resources():
            amount_resources = self.builder.amount_resources
            return json.dumps(amount_resources)

        @app.route('/collection_times', methods=['GET'])
        def collection_times():
            vrops_collection_times = self.builder.vrops_collection_times
            return json.dumps(vrops_collection_times)

        @app.route('/api_response_codes', methods=['GET'])
        def api_response_codes():
            response_codes = self.builder.response_codes
            return json.dumps(response_codes)

        @app.route('/api_response_times', methods=['GET'])
        def api_response_times():
            response_times = self.builder.response_times
            return json.dumps(response_times)

        @app.route('/service_states', methods=['GET'])
        def service_states():
            service_states = self.builder.service_states
            return json.dumps(service_states)

        # debugging purpose
        @app.route('/iteration_store', methods=['GET'])
        def iteration_store():
            return_iteration = self.builder.successful_iteration_list
            return json.dumps(return_iteration)

        @app.route('/stop')
        def stop():
            self.builder.am_i_killed = True
            self.WSGIServer.stop()
            return "Bye"

        # FIXME: this could basically be the always active token list. no active token? refresh!
        @app.route('/target_tokens', methods=['GET'])
        def token():
            return json.dumps(self.builder.target_tokens)

        try:
            if logger.level == 10:
                # WSGi is logging on DEBUG Level
                self.WSGIServer = WSGIServer((self.wsgi_address, self.port), app)
            else:
                self.WSGIServer = WSGIServer((self.wsgi_address, self.port), app, log=None)
            self.WSGIServer.serve_forever()
        except TypeError as e:
            logger.error('Problem starting server, you might want to try LOOPBACK=0 or LOOPBACK=1')
            logger.error(f'Current used options: {self.wsgi_address} on port {self.port}')
            logger.error(f'TypeError: {e}')
