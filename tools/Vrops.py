from urllib3 import disable_warnings
from urllib3 import exceptions
from tools.helper import chunk_list
from threading import Thread
import requests
import json
import os
import queue
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
            return False, 503

        if response.status_code == 200:
            return response.json()["token"], response.status_code
        else:
            logger.error(f'Problem getting token from {target} : {response.text}')
            return False, response.status_code

    def get_adapter(self, target: str, token: str) -> (str, str):
        url = f'https://{target}/suite-api/api/adapters'
        querystring = {
            "adapterKindKey": "VMWARE"
        }
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': f"vRealizeOpsToken {token}"
        }
        name = uuid = None
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.get(url,
                                    params=querystring,
                                    verify=False,
                                    headers=headers)
        except Exception as e:
            logger.error(f'Problem connecting to {target} - Error: {e}')
            return name, uuid

        if response.status_code == 200:
            for resource in response.json()["adapterInstancesInfoDto"]:
                name = resource["resourceKey"]["name"]
                uuid = resource["id"]

        else:
            logger.error(f'Problem getting adapter {target} : {response.text}')
            return name, uuid
        return name, uuid

    def get_resources(self, target: str, token: str, uuids: list, resourcekinds: list, data_receiving=False) -> list:
        logger.debug(f'Getting {resourcekinds} from {target}')
        url = "https://" + target + "/suite-api/api/resources/bulk/relationships"
        querystring = {
            'pageSize': '100000'
        }
        payload = {
            "relationshipType": "DESCENDANT",
            "resourceIds": uuids,
            "resourceQuery": {
                "adapterKind": ["VMWARE"],
                "resourceKind": resourcekinds,
                "resourceStatus": ["DATA_RECEIVING"]
            },
            "PageSize": 500000,
            "hierarchyDepth": 5
        } if data_receiving else {
            "relationshipType": "DESCENDANT",
            "resourceIds": uuids,
            "resourceQuery": {
                "adapterKind": ["VMWARE"],
                "resourceKind": resourcekinds
            },
            "PageSize": 500000,
            "hierarchyDepth": 5
        }

        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': f"vRealizeOpsToken {token}"
        }
        resources = list()
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.post(url,
                                     data=json.dumps(payload),
                                     params=querystring,
                                     verify=False,
                                     headers=headers)
        except Exception as e:
            logger.error(f'Problem connecting to {target} - Error: {e}')
            return resources

        if response.status_code == 200:
            try:
                relations = response.json()["resourcesRelations"]
                for resource in relations:
                    res = dict()
                    res['name'] = resource["resource"]["resourceKey"]["name"]
                    res['uuid'] = resource["resource"]["identifier"]
                    res['resourcekind'] = resource["resource"]["resourceKey"]["resourceKindKey"]
                    res['parent'] = resource.get("relatedResources", [None])[0]
                    resources.append(res)
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Catching JSONDecodeError for target {target}'
                             f'- Error: {e}')
        else:
            logger.error(f'Problem getting resources from {target} : {response.text}')
        return resources

    def get_datacenter(self, target, token, parent_uuids):
        return self.get_resources(target, token, parent_uuids, resourcekinds=["Datacenter"])

    def get_cluster_and_datastores(self, target, token, parent_uuids):
        return self.get_resources(target, token, parent_uuids, resourcekinds=["ClusterComputeResource", "Datastore"])

    def get_hosts(self, target, token, parent_uuids):
        return self.get_resources(target, token, parent_uuids, resourcekinds=["HostSystem"])

    def get_vms(self, target, token, parent_uuids, vcenter_uuid):
        amount_vms, api_responding, _ = self.get_latest_stats_multiple(target, token, [vcenter_uuid],
                                                                       ['summary|total_number_vms'],
                                                                       'Inventory')

        number_of_vms = amount_vms[0].get('stat-list', {}).get('stat', [])[0].get('data', [0])[0] if \
            api_responding == 200 else 0

        # vrops cannot handle more than 10000 uuids in a single request
        split_factor = int(number_of_vms / 10000)
        if split_factor >= 1:
            uuids_chunked = list(chunk_list(parent_uuids, int(len(parent_uuids) / (split_factor * 2))))
            logger.debug(f'Chunking VM requests into {len(uuids_chunked)} chunks')
            vms = list()
            for uuid_list in uuids_chunked:
                vms.extend(self.get_resources(target, token, uuid_list, resourcekinds=["VirtualMachine"],
                                              data_receiving=True))
            logger.debug(f'Number of VMs collected: {len(vms)}')
            return vms
        return self.get_resources(target, token, parent_uuids, resourcekinds=["VirtualMachine"],
                                  data_receiving=True)

    def get_latest_values_multiple(self, target: str, token: str, uuids: list, keys: list, collector: str,
                                   kind: str = None) -> (list, int, float):

        # vrops can not handle more than 1000 uuids for stats
        uuids_chunked = list(chunk_list(uuids, 1000)) if kind == 'stats' else [uuids]

        url = f"https://{target}/suite-api/api/resources/stats/latest/query" if kind == 'stats' else \
            f"https://{target}/suite-api/api/resources/properties/latest/query"

        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': f"vRealizeOpsToken {token}"
        }

        q = queue.Queue()
        thread_list = list()
        chunk_iteration = 0

        logger.debug('>----------------------- get_latest_values_multiple')
        logger.debug(f'target   : {target}')
        logger.debug(f'collector: {collector}')
        logger.debug(f'Amount keys : {len(keys)}')
        for k in keys:
            logger.debug(f'key  : {k}')

        for uuid_list in uuids_chunked:
            chunk_iteration += 1
            t = Thread(target=Vrops._get_chunk,
                       args=(q, uuid_list, url, headers, keys, target, kind, collector, chunk_iteration))
            thread_list.append(t)
            t.start()
        for t in thread_list:
            t.join()

        return_list = list()
        response_status_codes = list()
        response_time_elapsed = list()

        while not q.empty():
            returned_chunks = q.get()
            response_time_elapsed.append(returned_chunks[2])
            response_status_codes.append(returned_chunks[1])
            return_list.extend(returned_chunks[0])

        logger.debug(f'Amount uuids: {len(uuids)}')
        logger.debug(f'Fetched     : {len({r.get("resourceId") for r in return_list})}')
        logger.debug('<--------------------------------------------------')

        return return_list, max(response_status_codes), sum(response_time_elapsed) / len(response_time_elapsed)

    def get_latest_properties_multiple(self, target: str, token: str, uuids: list, keys: list, collector: str):
        return self.get_latest_values_multiple(target, token, uuids, keys, collector, kind='properties')

    def get_latest_stats_multiple(self, target: str, token: str, uuids: list, keys: list, collector: str):
        return self.get_latest_values_multiple(target, token, uuids, keys, collector, kind='stats')

    def _get_chunk(q, uuid_list, url, headers, keys, target, kind, collector, chunk_iteration):
        logger.debug(f'chunk: {chunk_iteration}')

        payload = {
            "resourceId": uuid_list,
            "statKey": keys,
            "PageSize": 500000
        } if kind == 'stats' else {
            "resourceIds": uuid_list,
            "propertyKeys": keys,
            "PageSize": 500000
        }

        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.post(url,
                                     data=json.dumps(payload),
                                     verify=False,
                                     headers=headers,
                                     timeout=60)
        except Exception as e:
            logger.error(f'{collector} has problems getting latest data from: {target} - Error: {e}')
            q.put([[], 503, 999])
            return

        if response.status_code == 200:
            try:
                q.put([response.json().get('values', []), response.status_code, response.elapsed.total_seconds()])
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Catching JSONDecodeError for {collector}, target: {collector}, chunk_iteration: '
                             f'{chunk_iteration} - Error: {e}')
                q.put([[], response.status_code, response.elapsed.total_seconds()])
                return
        else:
            logger.error(f'Return code: {response.status_code} != 200 for {collector} : {response.text}')
            q.put([[], response.status_code, response.elapsed.total_seconds()])
            return

    def get_project_ids(target: str, token: str, uuids: list, collector: str) -> (list, int):
        logger.debug('>---------------------------------- get_project_ids')
        logger.debug(f'target   : {target}')
        logger.debug(f'collector: {collector}')

        project_ids = list()
        url = f'https://{target}/suite-api/api/resources/bulk/relationships'
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        payload = {
            "relationshipType": "ANCESTOR",
            "resourceIds": uuids,
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
            return [], 503

        if response.status_code == 200:
            try:
                for project in response.json()['resourcesRelations']:
                    p_ids = dict()
                    for vm_uuid in project["relatedResources"]:
                        project_name = project["resource"]["resourceKey"]["name"]
                        p_ids[vm_uuid] = project_name[project_name.find("(") + 1:project_name.find(")")]
                    project_ids.append(p_ids)
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Catching JSONDecodeError for target: {target}, {collector}'
                             f' - Error: {e}')
                return [], response.status_code
        else:
            logger.error(f'Return code: {response.status_code} != 200 for {target} : {response.text}')
            return [], response.status_code

        logger.debug(f'Fetched project ids: {len(project_ids)}')
        logger.debug('<--------------------------------------------------')

        return project_ids
