from tools.Vrops import Vrops
from InventoryBuilder import InventoryBuilder
import json
import os

"""
Purpose of this file was to call specific parts of the vrops exporter to test the mock server.
I keep this file in so that the setup needed is transparent for further development.
This file currently starts the InventoryBuilder as a server, which polls against the mock server once every 500 seconds.
"""

if __name__ == '__main__':
    os.environ['User'] = 'Mocking'
    os.environ['PASSWORD'] = 'Server'
    target = '127.0.0.1'
    vrops = Vrops()

    """
    with open('./mockingServer/data/inventory_builder_response.json', 'r') as fp:
        response = json.load(fp)

    print(response["resourcesRelations"]["resource"]["resourceKey"]["name"])
    print(response["resourcesRelations"]["resource"]["identifier"])
    print(response["resourcesRelations"]["resource"]["resourceKey"]["resourceKindKey"])
    print(response["resourcesRelations"]["relatedResources"][0])
    """

    ib = InventoryBuilder('./mockingServer/data/atlasmock.json', 9011, 500, 60)
    #ib = InventoryBuilder.create_resource_objects('127.0.0.1', '779b8ede-1337-11eb-9581-3c58c27e75a6')
    #print(ib)
    #response = vrops.get_resources('127.0.0.1', 'token', [1234], 'reskinds')
    #print(response)
    #name, uuid = Vrops.get_adapter('127.0.0.1', 'token')
   # print(name, uuid)
    # Token
    #token_response = Vrops.get_token(target)
   # print(token_response)
   # token = token_response[0]

    # basecollector http_response
   # bc_response = Vrops.get_http_response_code(target, token)
   # print(bc_response)

    # basecollector get_project_ids
    #proj_ids = Vrops.get_project_ids(target, token, ['123456'], 'testexporter')
