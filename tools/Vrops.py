from urllib3 import disable_warnings
from urllib3 import exceptions
from tools.helper import chunk_list
from threading import Thread
import requests
import json
import os
import logging

logger = logging.getLogger('vrops-exporter')


class Vrops:
    def get_token(target):
        url = "https://" + target + "/suite-api/api/auth/token/acquire"
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json"
        }
        payload = {
            "username": os.environ['USER'],
            "authSource": "Local",
            "password": os.environ['PASSWORD']
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.post(url,
                                     data=json.dumps(payload),
                                     verify=False,
                                     headers=headers,
                                     timeout=10)
        except Exception as e:
            logger.error(f'Problem connecting to {target}. Error: {e}')
            return False

        if response.status_code == 200:
            return response.json()["token"]
        else:
            logger.error(f'Problem getting token from {target} : {response.text}')
            return False

    def get_http_response_code(target, token):
        url = "https://" + target + "/suite-api/api/resources"
        querystring = {
            "adapterKindKey": "VMWARE"
        }
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        disable_warnings(exceptions.InsecureRequestWarning)

        try:
            response = requests.get(url,
                                    params=querystring,
                                    verify=False,
                                    headers=headers)
        except Exception as e:
            logger.error(f'Problem connecting to {target} - Error: {e}')
            return 503

        return response.status_code

    def get_adapter(target, token):
        url = "https://" + target + "/suite-api/api/adapters"
        querystring = {
            "adapterKindKey": "VMWARE"
        }
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        adapters = list()
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.get(url,
                                    params=querystring,
                                    verify=False,
                                    headers=headers)
        except Exception as e:
            logger.error(f'Problem connecting to {target} - Error: {e}')
            return adapters

        if response.status_code == 200:
            for resource in response.json()["adapterInstancesInfoDto"]:
                res = dict()
                res['name'] = resource["resourceKey"]["name"]
                res['uuid'] = resource["id"]
                res['adapterkind'] = resource["resourceKey"]["adapterKindKey"]
                adapters.append(res)
        else:
            logger.error(f'Problem getting adapter {target} : {response.text}')
            return adapters

        return adapters

    def get_resources(self, target, token, resourcekind, parentid):
        url = "https://" + target + "/suite-api/api/resources"
        querystring = {
            'parentId': parentid,
            'adapterKind': 'VMware',
            'resourceKind': resourcekind,
            'pageSize': '50000'
        }
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        resources = list()
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.get(url,
                                    params=querystring,
                                    verify=False,
                                    headers=headers)
        except Exception as e:
            logger.error(f'Problem connecting to {target} - Error: {e}')
            return resources

        if response.status_code == 200:
            try:
                resourcelist = response.json()["resourceList"]
                for resource in resourcelist:
                    res = dict()
                    res['name'] = resource["resourceKey"]["name"]
                    res['uuid'] = resource["identifier"]
                    resources.append(res)
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Catching JSONDecodeError for target {target} and resourcekind: {resourcekind}'
                             f'- Error: {e}')
        else:
            logger.error(f'Problem getting adapter {target} : {response.text}')
        return resources

    def get_project_ids(target, token, uuids, collector):
        logger.debug('>---------------------------------- get_project_ids')
        logger.debug(f'target   : {target}')
        logger.debug(f'collector: {collector}')

        if not isinstance(uuids, list):
            logger.error('Error in get project_ids: uuids must be a list with multiple entries')
            return False
        # vrops can not handle more than 1000 uuids
        uuids_chunked = list(chunk_list(uuids, 1000))
        project_ids = list()
        url = "https://" + target + "/suite-api/api/resources/bulk/relationships"
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        import queue
        q = queue.Queue()
        thread_list = list()
        chunk_iteration = 0

        for uuid_list in uuids_chunked:
            chunk_iteration += 1
            t = Thread(target=Vrops.get_project_id_chunk,
                       args=(q, uuid_list, url, headers, target, chunk_iteration))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        while not q.empty():
            project_ids += q.get()

        logger.debug(f'Amount uuids: {len(uuids)}')
        logger.debug(f'Fetched     : {len(project_ids)}')
        logger.debug('<--------------------------------------------------')

        return project_ids

    def get_datacenter(self, target, token, parentid):
        return self.get_resources(target, token, parentid=parentid, resourcekind="Datacenter")

    def get_cluster(self, target, token, parentid):
        return self.get_resources(target, token, parentid=parentid, resourcekind="ClusterComputeResource")

    def get_hosts(self, target, token, parentid):
        return self.get_resources(target, token, parentid=parentid, resourcekind="HostSystem")

    def get_datastores(self, target, token, parentid):
        return self.get_resources(target, token, parentid=parentid, resourcekind="Datastore")

    def get_virtualmachines(self, target, token, parentid):
        return self.get_resources(target, token, parentid=parentid, resourcekind="VirtualMachine")

    def get_project_folders(self, target, token):
        return self.get_resources(target, token, parentid=None, resourcekind="VMFolder")

    # only recommended for a small number of statkeys and resources.
    def get_latest_stat(target, token, uuid, key, collector):
        logger.debug('>---------------------------------- get_latest_stat')
        logger.debug(f'key      : {key}')
        logger.debug(f'target   : {target}')
        logger.debug(f'collector: {collector}')

        url = "https://" + target + "/suite-api/api/resources/" + uuid + "/stats/latest"
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        disable_warnings(exceptions.InsecureRequestWarning)

        try:
            response = requests.get(url,
                                    verify=False,
                                    headers=headers,
                                    timeout=10)
        except Exception as e:
            logger.error(f'Problem getting stats error for {key} - Error: {e}')
            return False

        if response.status_code == 200:
            try:
                for statkey in response.json()["values"][0]["stat-list"]["stat"]:
                    if statkey["statKey"]["key"] is not None and statkey["statKey"]["key"] == key:
                        logger.debug('<--------------------------------------------------')
                        return statkey["data"][0]
            except IndexError as e:
                logger.error(f'Problem getting statkey error for {key} - Error {e}')
        else:
            logger.error(f'Return code: {response.status_code} != 200 for {key} : {response.text}')
            return False

    # this is for a single query of a property and returns the value only
    def get_property(target, token, uuid, key, collector):
        logger.debug('>------------------------------------- get_property')
        logger.debug(f'key      : {key}')
        logger.debug(f'target   : {target}')
        logger.debug(f'collector: {collector}')

        url = "https://" + target + "/suite-api/api/resources/" + uuid + "/properties"
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.get(url,
                                    verify=False,
                                    headers=headers)
        except Exception as e:
            logger.error(f'Problem getting stats error for {key} - Error: {e}')
            return False

        if response.status_code == 200:
            try:
                for propkey in response.json()["property"]:
                    if propkey["name"] is not None and propkey["name"] == key:
                        logger.debug('<--------------------------------------------------')
                        return propkey["value"]
            except IndexError as e:
                logger.error(f'Problem getting property error for {key} - Error {e}')
        else:
            logger.error(f'Return code: {response.status_code} != 200 for {key} : {response.text}')
            return False

    # if we expect a number without special characters
    def get_latest_number_properties_multiple(target, token, uuids, propkey, collector):
        if not isinstance(uuids, list):
            logger.error('Error in get project_ids: uuids must be a list with multiple entries')
            return False

        logger.debug('>------------ get_latest_number_properties_multiple')
        logger.debug(f'key      : {propkey}')
        logger.debug(f'target   : {target}')
        logger.debug(f'collector: {collector}')

        return_list = list()
        url = "https://" + target + "/suite-api/api/resources/properties/latest/query"
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        payload = {
            "resourceIds": uuids,
            "propertyKeys": [propkey]
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.post(url,
                                     data=json.dumps(payload),
                                     verify=False,
                                     headers=headers)
        except Exception as e:
            logger.error(f'Problem getting property error for {propkey} - Error: {e}')
            return False

        if response.status_code == 200:
            try:
                if not response.json()['values']:
                    return False
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Catching JSONDecodeError for target {target} and property key: {propkey}'
                             f'- Error: {e}')
                return False
            for resource in response.json()['values']:
                d = dict()
                d['resourceId'] = resource['resourceId']
                d['propkey'] = propkey
                content = resource['property-contents']['property-content']
                if content:
                    if 'values' in content[0]:
                        d['data'] = content[0]['values'][0]
                    else:
                        d['data'] = content[0]['data'][0]
                else:
                    # resources can go away, so None is returned
                    logger.warning(f'skipping resource for get property: {propkey}, no property-content')
                return_list.append(d)

            logger.debug(f'Amount uuids: {len(uuids)}')
            logger.debug(f'Fetched     : {len(return_list)}')
            logger.debug('<--------------------------------------------------')

            return return_list
        else:
            logger.error(f'Return code: {response.status_code} != 200 for {propkey} : {response.text}')
            return False

    # if the property describes a status that has several states
    # the expected status returns a 0, all others become 1
    def get_latest_enum_properties_multiple(target, token, uuids, propkey, collector):

        if not isinstance(uuids, list):
            logger.error('Error in get project_ids: uuids must be a list with multiple entries')
            return False

        logger.debug('>-------------- get_latest_enum_properties_multiple')
        logger.debug(f'key      : {propkey}')
        logger.debug(f'target   : {target}')
        logger.debug(f'collector: {collector}')

        url = "https://" + target + "/suite-api/api/resources/properties/latest/query"
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        payload = {
            "resourceIds": uuids,
            "propertyKeys": [propkey]
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.post(url,
                                     data=json.dumps(payload),
                                     verify=False,
                                     headers=headers)
        except Exception as e:
            logger.error(f'Problem getting property error for {propkey} - Error: {e}')
            return False

        properties_list = list()

        if response.status_code == 200:
            try:
                if not response.json()['values']:
                    return False
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Catching JSONDecodeError for target {target} and property key: {propkey}'
                             f' - Error: {e}')
                return False
            for resource in response.json()['values']:
                d = dict()
                d['resourceId'] = resource['resourceId']
                d['propkey'] = propkey
                content = resource['property-contents']['property-content']
                if content:
                    if 'values' in content[0]:
                        d['value'] = content[0]['values'][0]
                else:
                    # resources can go away, so None is returned
                    logger.warning(f'skipping resource for get property: {propkey}, no property-content')
                properties_list.append(d)

            logger.debug(f'Amount uuids: {len(uuids)}')
            logger.debug(f'Fetched     : {len(properties_list)}')
            logger.debug('<--------------------------------------------------')

            return properties_list
        else:
            logger.error(f'Return code: {response.status_code} != 200 for {propkey} : {response.text}')
            return False

    # for all other properties that return a string or numbers with special characters
    def get_latest_info_properties_multiple(target, token, uuids, propkey, collector):

        if not isinstance(uuids, list):
            logger.error('Error in get project_ids: uuids must be a list with multiple entries')
            return False

        logger.debug('>-------------- get_latest_info_properties_multiple')
        logger.debug(f'key      : {propkey}')
        logger.debug(f'target   : {target}')
        logger.debug(f'collector: {collector}')

        url = "https://" + target + "/suite-api/api/resources/properties/latest/query"
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        payload = {
            "resourceIds": uuids,
            "propertyKeys": [propkey]
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.post(url,
                                     data=json.dumps(payload),
                                     verify=False,
                                     headers=headers)
        except Exception as e:
            logger.error(f'Problem getting property error for {propkey} - Error: {e}')
            return False

        properties_list = list()

        if response.status_code == 200:
            try:
                if not response.json()['values']:
                    return False
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Catching JSONDecodeError for target {target} and property key: {propkey}'
                             f' - Error: {e}')
                return False
            for resource in response.json()['values']:
                d = dict()
                d['resourceId'] = resource['resourceId']
                d['propkey'] = propkey
                content = resource['property-contents']['property-content']
                if content:
                    if 'values' in content[0]:
                        info = content[0]['values'][0]
                    else:
                        info = 'None'
                    d['data'] = info
                else:
                    # resources can go away, so None is returned
                    logger.warning(f'skipping resource for get property: {propkey}, no property-content')
                properties_list.append(d)

            logger.debug(f'Amount uuids: {len(uuids)}')
            logger.debug(f'Fetched     : {len(properties_list)}')
            logger.debug('<--------------------------------------------------')

            return properties_list
        else:
            logger.error(f'Return code: {response.status_code} != 200 for {propkey} : {response.text}')
            return False

    def get_latest_stat_multiple(target, token, uuids, key, collector):
        if not isinstance(uuids, list):
            logger.error('Error in get project_ids: uuids must be a list with multiple entries')
            return False

        # vrops can not handle more than 1000 uuids
        uuids_chunked = list(chunk_list(uuids, 1000))
        return_list = list()
        url = "https://" + target + "/suite-api/api/resources/stats/latest/query"
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }

        import queue
        q = queue.Queue()
        thread_list = list()
        chunk_iteration = 0

        logger.debug('>------------------------ get_latest_stats_multiple')
        logger.debug(f'key      : {key}')
        logger.debug(f'target   : {target}')
        logger.debug(f'collector: {collector}')

        for uuid_list in uuids_chunked:
            chunk_iteration += 1
            t = Thread(target=Vrops.get_stat_chunk,
                       args=(q, uuid_list, url, headers, key, target, chunk_iteration))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        while not q.empty():
            return_list += q.get()

        logger.debug(f'Amount uuids: {len(uuids)}')
        logger.debug(f'Fetched     : {len(return_list)}')
        logger.debug('<--------------------------------------------------')

        return return_list

    def get_project_id_chunk(q, uuid_list, url, headers, target, chunk_iteration):
        logger.debug(f'chunk: {chunk_iteration}')

        payload = {
            "relationshipType": "ANCESTOR",
            "resourceIds": uuid_list,
            "resourceQuery": {
                "name": ["Project"],
                "adapterKind": ["VMWARE"],
                "resourceKind": ["VMFolder"]
            },
            "hierarchyDepth": 5
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.post(url,
                                     data=json.dumps(payload),
                                     verify=False,
                                     headers=headers)
        except Exception as e:
            logger.error(f'Problem getting project folder - Error: {e}')
            return False
        if response.status_code == 200:
            try:
                for project in response.json()['resourcesRelations']:
                    p_ids = dict()
                    for vm_uuid in project["relatedResources"]:
                        p_ids[vm_uuid] = project["resource"]["resourceKey"]["name"][
                                         project["resource"]["resourceKey"]["name"].find("(") + 1:
                                         project["resource"]["resourceKey"]["name"].find(")")]
                    q.put([p_ids])
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Catching JSONDecodeError for target: {target}, chunk iteration: {chunk_iteration}'
                             f' - Error: {e}')
                return False
        else:
            logger.error(f'Return code: {response.status_code} != 200 for {target} : {response.text}')
            return False

    def get_stat_chunk(q, uuid_list, url, headers, key, target, chunk_iteration):
        logger.debug(f'chunk: {chunk_iteration}')

        payload = {
            "resourceId": uuid_list,
            "statKey": [key]
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.post(url,
                                     data=json.dumps(payload),
                                     verify=False,
                                     headers=headers,
                                     timeout=10)
        except Exception as e:
            logger.error(f'Problem getting statkey error for {key}, target: {target} - Error: {e}')
            return False

        if response.status_code == 200:
            try:
                q.put(response.json()['values'])
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Catching JSONDecodeError for target  {target} and key {key} chunk_iteration: '
                             f'{chunk_iteration} - Error: {e}')
                return False
        else:
            logger.error(f'Return code: {response.status_code} != 200 for {key} : {response.text}')
            return False
