from mockingServer.modules.RequestHandler import RequestHandler
from flask import Blueprint, make_response, request
import json

inventoryBuilderBluePrint = Blueprint('LoggingService', import_name=__name__)


class BuilderResources(RequestHandler):
    # TODO: Needs to be implemented in a way that the "get_project_ids" method from the Basecollector can be served.
    def post(self):
        response = {"resourcesRelations": []}
        payload = json.loads(request.data.decode())
        testname = 'Testname'

        for resource_kind in payload["resourceQuery"]["resourceKind"]:
            # TODO: Should be implemented in a way where the different URLs of the InventoryBuilder provide
            #       different datasets to test against. An example is shown below. Maybe a switch case in which
            #       all keys values are customized for the caller is a good idea.
            if resource_kind == 'HostSystem':
                testname = 'host'
            values = {
                "resource": {
                    "resourceKey": {
                        "name": testname,
                        "resourceKindKey": resource_kind
                    },
                    "identifier": "1337ID"
                },
                "relatedResources": [
                    "1337ID"
                ]
            }
            response["resourcesRelations"].append(values)

        if not self.check_token():
            return make_response('Token check failure at BuilderResources', 404)
        return response


class BuilderAdapter(RequestHandler):
    def get(self):
        response = {"adapterInstancesInfoDto": []}
        values = {
            "resourceKey": {
                "name": "vCenter_name"
            },
            "id": "1337AdapterID"
        }

        response["adapterInstancesInfoDto"].append(values)

        if not self.check_token():
            return make_response('Token check failure at BuilderResources', 404)
        return response


inventoryBuilderBluePrint.add_url_rule('/resources/bulk/relationships',
                                       view_func=BuilderResources.as_view('BuilderResources'))
inventoryBuilderBluePrint.add_url_rule('/adapters', view_func=BuilderAdapter.as_view('BuilderAdapter'))
