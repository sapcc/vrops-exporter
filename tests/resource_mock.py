import unittest
from unittest import TestCase
from unittest.mock import MagicMock
import requests
import tools.YamlRead

def mock_vrops_api(url, **kwargs):
    # sniff Adapter or resource query
    if url.endswith('adapters'):
        type = 'Adapter'
        adapter_type = kwargs['params'].get('adapterKindKey', None)
        parentId = None
        list_element = 'adapterInstancesInfoDto'
    elif url.endswith('resources'):
        type = kwargs['params']['resourceKind']
        adapter_type = None
        parentId = kwargs['params'].get('parentId', None)
        list_element = 'resourceList'
    else:
        type: "Invalid"
        adapter_type = None
        parentId = None
        list_element = "list"

    resources = tools.YamlRead.YamlRead("tests/vrops_api_responses.yaml").run().get(type, [])

    # Filter Resource by Parent (does not affect Adapters)
    if parentId != None:
        resources = list(filter(lambda r: r['parent'] == parentId, resources))
    # Filter Adapter by Kind (does not effect Resources)
    if adapter_type != None:
        resources = list(filter(lambda r: r['data']['resourceKey']['adapterKindKey'] == adapter_type, resources))

    response = {
        "pageInfo": {
            "totalCount": len(resources),
            "page": 0,
            "size": kwargs['params'].get("pageSize", 50000)
        },
        "links": dict(),
    }
    response[list_element] = list(map(lambda r: r['data'], resources))
    
    return MagicMock(status_code=200, json = lambda: response)
        