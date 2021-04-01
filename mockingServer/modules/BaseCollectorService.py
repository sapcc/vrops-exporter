from mockingServer.modules.RequestHandler import RequestHandler
from flask import Blueprint, make_response
import json

baseCollectorBluePrint = Blueprint('BaseCollector', import_name=__name__)

# TODO: The "get_project_ids" mtehod of the BaseCollectorService should me included in the InventoryBuilderService,
#       because the method uses the same URL as the "get_resources" method from InventoryBuilder

class BaseCollectorService(RequestHandler):
    def get(self):
        if not self.check_token():
            return make_response('sessionID check failed', 401)
        return make_response('http request succeeded', 200)

"""
    def post(self):
        if not self.check_token():
            return make_response('sessionID check failed', 401)
        with open('')
"""




baseCollectorBluePrint.add_url_rule('/resources',
                                    view_func=BaseCollectorService.as_view('get_http_response_code'))
baseCollectorBluePrint.add_url_rule('resources/bulk/relationships',
                                    view_func=BaseCollectorService.as_view('get_project_id_chunk'))
