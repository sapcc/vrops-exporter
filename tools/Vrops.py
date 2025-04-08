from urllib3 import disable_warnings
from urllib3 import exceptions
from tools.helper import chunk_list, remove_html_tags
from threading import Thread
import requests
import json
import os
import queue
import logging
import re

logger = logging.getLogger('vrops-exporter')


class Vrops:
    def get_token(target):
        url = "https://" + target + "/suite-api/api/auth/token/acquire"
        timeout = 40
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
                                     timeout=timeout)
        except requests.exceptions.ReadTimeout as e:
            logger.error(f'Request to {url} timed out. Error: {e}')
            return False, 504, timeout
        except Exception as e:
            logger.error(f'Problem connecting to {target}. Error: {e}')
            return False, 503, 0

        if response.status_code == 200:
            return response.json()["token"], response.status_code, response.elapsed.total_seconds()
        else:
            logger.error(f'Problem getting token from {target} : {response.text}')
            return False, response.status_code, response.elapsed.total_seconds()

    def get_adapter(self, target: str, token: str, adapterkind: str) -> (list, int):
        url = f'https://{target}/suite-api/api/adapters'
        timeout = 40
        querystring = {
            "adapterKindKey": adapterkind
        }
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': f"vRealizeOpsToken {token}"
        }
        adapter = list()
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.get(url,
                                    params=querystring,
                                    verify=False,
                                    headers=headers,
                                    timeout=timeout)
        except requests.exceptions.ReadTimeout as e:
            logger.error(f'Request to {url} timed out. Error: {e}')
            return adapter, 504, timeout
        except Exception as e:
            logger.error(f'Problem connecting to {target} - Error: {e}')
            return adapter, 503, 0

        if response.status_code == 200:
            for resource in response.json()["adapterInstancesInfoDto"]:
                resourcekindkey = resource["resourceKey"]["resourceKindKey"]
                resourcekindkey = re.sub("[^a-zA-Z]+", "", resourcekindkey)

                adapter_object = type(resourcekindkey, (object,), {
                    "name": resource["resourceKey"]["name"],
                    "uuid": resource["id"],
                    "adapterkind": adapterkind,
                    "resourcekindkey": resourcekindkey,
                    "target": target,
                    "token": token
                })
                adapter.append(adapter_object)
            return adapter, response.status_code, response.elapsed.total_seconds()
        else:
            logger.error(f'Problem getting adapter {target} : {response.text}')
            return adapter, response.status_code, response.elapsed.total_seconds()

    def get_vcenter_adapter(self, target, token):
        return self.get_adapter(target, token, adapterkind="VMWARE")

    def get_nsxt_adapter(self, target, token):
        return self.get_adapter(target, token, adapterkind="NSXTAdapter")

    def get_vcenter_operations_adapter_intance(self, target, token):
        return self.get_adapter(target, token, adapterkind="vCenter Operations Adapter")

    def get_sddc_health_adapter_intance(self, target, token):
        return self.get_adapter(target, token, adapterkind="SDDCHealthAdapter")

    def get_resources(self, target: str,
                      token: str,
                      adapterkind: str,
                      resourcekinds: list,  # Array of resource kind keys
                      uuids: list,  # Array of parent uuids
                      query_specs: dict,  # Dict of resource query specifications
                      h_depth: int = 1) -> (list, int):
        if not uuids:
            logger.debug(f'No parent resources for {resourcekinds} from {target}')
            return [], 400, 0
        logger.debug(f'Getting {resourcekinds} from {target}')
        url = "https://" + target + "/suite-api/api/resources/bulk/relationships"
        timeout = 40

        logger.debug(f'Using resource query specs: {query_specs}')
        r_status_list = [rs for rs in query_specs.get('resourceStatus', [])]
        r_health_list = [rh for rh in query_specs.get('resourceHealth', [])]
        r_states_list = [rst for rst in query_specs.get('resourceStates', [])]

        querystring = {
            'pageSize': 10000
        }
        payload = {
            "relationshipType": "DESCENDANT",
            "resourceIds": uuids,
            "resourceQuery": {
                "adapterKind": [adapterkind],
                "resourceKind": resourcekinds,
                "resourceStatus": r_status_list,
                "resourceHealth": r_health_list,
                "resourceState": r_states_list
            },
            "hierarchyDepth": h_depth
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
                                     headers=headers,
                                     timeout=timeout)
        except requests.exceptions.ReadTimeout as e:
            logger.error(f'Request to {url} timed out. Error: {e}')
            return resources, 504, timeout
        except Exception as e:
            logger.error(f'Problem connecting to {target} - Error: {e}')
            return resources, 503, 0

        if response.status_code == 200:
            try:
                relations = response.json()["resourcesRelations"]
                if not relations:
                    resourcekinds_beautyfied = ', '.join(resourcekinds)
                    logger.warning(f'No child relation returned for {resourcekinds_beautyfied} from adapter {adapterkind} for {target}.')
                    return resources, 204, response.elapsed.total_seconds()
                for resource in relations:
                    resourcekind = resource["resource"]["resourceKey"]["resourceKindKey"]
                    resourcekind = re.sub("[^a-zA-Z]+", "", resourcekind)
                    resource_identifiers = resource["resource"]["resourceKey"]["resourceIdentifiers"]
                    internal_name = list(filter(lambda identifier_type:
                                                identifier_type['identifierType']['name']
                                                == 'VMEntityObjectID', resource_identifiers))
                    internal_name = internal_name[0].get('value') if internal_name else None
                    instance_uuid = list(filter(lambda identifier_type:
                                                identifier_type['identifierType']['name']
                                                == 'VMEntityInstanceUUID', resource_identifiers))
                    instance_uuid = instance_uuid[0].get('value') if instance_uuid else None

                    resource_object = type(resourcekind, (object,), {
                        "name": resource["resource"]["resourceKey"]["name"],
                        "uuid": resource["resource"]["identifier"],
                        "resourcekind": resourcekind,
                        "parent": resource.get("relatedResources", ["None"])[0],
                        "internal_name": internal_name,
                        "instance_uuid": instance_uuid
                    })
                    if not resource.get("relatedResources"):
                        logger.warning(f'No parent relation returned for {resource["resource"]["resourceKey"]["name"]}; resourcekind: {resourcekind}; target: {target}.')
                    resources.append(resource_object)
                return resources, response.status_code, response.elapsed.total_seconds()
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Catching JSONDecodeError for target {target}'
                             f'- Error: {e}')
                return resources, response.status_code, response.elapsed.total_seconds()
        else:
            logger.error(f'Problem getting resources from {target} : {response.text}')
            return resources, response.status_code, response.elapsed.total_seconds()

    def get_datacenter(self, target, token, parent_uuids, query_specs):
        resourcekind = 'Datacenter'
        return self.get_resources(target, token, adapterkind="VMWARE", resourcekinds=[resourcekind],
                                  uuids=parent_uuids, query_specs=self._set_query_specs(query_specs, resourcekind))

    def get_cluster(self, target, token, parent_uuids, query_specs):
        resourcekind = 'ClusterComputeResource'
        return self.get_resources(target, token, adapterkind="VMWARE", resourcekinds=[resourcekind],
                                  uuids=parent_uuids, query_specs=self._set_query_specs(query_specs, resourcekind))

    def get_SDRS_cluster(self, target, token, parent_uuids, query_specs):
        resourcekind = 'StoragePod'
        return self.get_resources(target, token, adapterkind="VMWARE", resourcekinds=["StoragePod"],
                                  uuids=parent_uuids, query_specs=self._set_query_specs(query_specs, resourcekind))

    def get_datastores(self, target, token, parent_uuids, query_specs):
        resourcekind = 'Datastore'
        datastores, http_code, response_time = self.get_resources(target, token, adapterkind="VMWARE",
                                                        resourcekinds=["Datastore"], uuids=parent_uuids,
                                                        query_specs=self._set_query_specs(query_specs, resourcekind))
        for datastore in datastores:
            if "p_ssd" in datastore.name:
                datastore.type = "vmfs_p_ssd"
            elif "s_hdd" in datastore.name:
                datastore.type = "vmfs_s_hdd"
            elif datastore.name.startswith("eph") or datastore.name.startswith("donotdeploy_eph"):
                datastore.type = "ephemeral"
            elif "Management" in datastore.name:
                datastore.type = "Management"
            elif datastore.name.endswith("local"):
                datastore.type = "local"
            elif datastore.name.startswith('nfs'):
                datastore.type = "nfs"
            elif datastore.name.startswith('nsxt'):
                datastore.type = "nsxt"
            elif datastore.name.endswith("swap"):
                datastore.type = "NVMe"
            else:
                datastore.type = "other"
        return datastores, http_code, response_time

    def get_hosts(self, target, token, parent_uuids, query_specs):
        resourcekind = 'HostSystem'
        return self.get_resources(target, token, adapterkind="VMWARE", resourcekinds=[resourcekind],
                                  uuids=parent_uuids, query_specs=self._set_query_specs(query_specs, resourcekind))

    def get_vms(self, target, token, parent_uuids, vcenter_uuid, query_specs):
        if not parent_uuids:
            logger.debug(f'No parent resources for virtual machines from {target}')
            return [], 400, 0
        resourcekind = 'VirtualMachine'
        q_specs = self._set_query_specs(query_specs, resourcekind)
        amount_vms, http_code, _ = self.get_latest_stats_multiple(target, token, [vcenter_uuid],
                                                                       ['summary|total_number_vms'],
                                                                       'Inventory')

        number_of_vms = amount_vms[0].get('stat-list', {}).get('stat', [])[0].get('data', [0])[0] if \
            http_code == 200 and amount_vms else 0

        # vrops cannot handle more than 10000 uuids in a single request
        split_factor = int(number_of_vms / 10000)
        if split_factor >= 1:
            uuids_chunked = list(chunk_list(parent_uuids, int(len(parent_uuids) / (split_factor + 1))))
            logger.debug(f'Chunking VM requests into {len(uuids_chunked)} chunks')
            vms = list()
            http_codes = list()
            response_times = list()

            for uuid_list in uuids_chunked:

                vm_chunks, http_code, response_time = self.get_resources(target, token, adapterkind="VMWARE",
                                                                     resourcekinds=[resourcekind],
                                                                     uuids=uuid_list, query_specs=q_specs)
                vms.extend(vm_chunks)
                http_codes.append(http_code)
                response_times.append(response_time)
            logger.debug(f'Number of VMs collected: {len(vms)}')
            return vms, max(http_codes), sum(response_times)
        return self.get_resources(target, token, adapterkind="VMWARE", resourcekinds=[resourcekind],
                                  uuids=parent_uuids, query_specs=q_specs)

    def get_dis_virtual_switch(self, target, token, parent_uuids, query_specs):
        resourcekind = 'VmwareDistributedVirtualSwitch'
        return self.get_resources(target, token, adapterkind="VMWARE", resourcekinds=[resourcekind],
                                  uuids=parent_uuids, query_specs=self._set_query_specs(query_specs, resourcekind))

    def get_nsxt_mgmt_cluster(self, target, token, parent_uuids, query_specs):
        resourcekind = 'ManagementCluster'
        return self.get_resources(target, token, adapterkind="NSXTAdapter", resourcekinds=[resourcekind],
                                  uuids=parent_uuids, query_specs=self._set_query_specs(query_specs, resourcekind))

    def get_nsxt_mgmt_nodes(self, target, token, parent_uuids, query_specs):
        resourcekind = 'ManagementNode'
        return self.get_resources(target, token, adapterkind="NSXTAdapter", resourcekinds=[resourcekind],
                                  uuids=parent_uuids, query_specs=self._set_query_specs(query_specs, resourcekind), h_depth=5)

    def get_nsxt_mgmt_service(self, target, token, parent_uuids, query_specs):
        resourcekind = 'ManagementService'
        return self.get_resources(target, token, adapterkind="NSXTAdapter", resourcekinds=[resourcekind],
                                  uuids=parent_uuids, query_specs=self._set_query_specs(query_specs, resourcekind), h_depth=5)

    def get_nsxt_transport_zone(self, target, token, parent_uuids, query_specs):
        resourcekind = 'TransportZone'
        return self.get_resources(target, token, adapterkind="NSXTAdapter", resourcekinds=[resourcekind],
                                  uuids=parent_uuids, query_specs=self._set_query_specs(query_specs, resourcekind), h_depth=5)

    def get_nsxt_transport_node(self, target, token, parent_uuids, query_specs):
        resourcekind = 'TransportNode'
        return self.get_resources(target, token, adapterkind="NSXTAdapter", resourcekinds=[resourcekind],
                                  uuids=parent_uuids, query_specs=self._set_query_specs(query_specs, resourcekind))

    def get_nsxt_logical_switch(self, target, token, parent_uuids, query_specs):
        resourcekind = 'LogicalSwitch'
        return self.get_resources(target, token, adapterkind="NSXTAdapter", resourcekinds=[resourcekind],
                                  uuids=parent_uuids, query_specs=self._set_query_specs(query_specs, resourcekind), h_depth=5)

    def get_vcops_instances(self, target, token, parent_uuids, resourcekinds, query_specs):
        return self.get_resources(target, token, adapterkind="vCenter Operations Adapter",
                                  resourcekinds=resourcekinds, uuids=parent_uuids,
                                  query_specs=query_specs.get('default', {}), h_depth=5)

    def get_sddc_instances(self, target, token, parent_uuids, resourcekinds, query_specs):
        return self.get_resources(target, token, adapterkind="SDDCHealthAdapter",
                                  resourcekinds=resourcekinds, uuids=parent_uuids,
                                  query_specs=query_specs.get('default', {}), h_depth=5)

    def _set_query_specs(self, query_specs, resourcekind):
        return query_specs.get(resourcekind) if resourcekind in query_specs else query_specs.get('default', {})

    def get_latest_values_multiple(self, target: str, token: str,
                                   uuids: list,
                                   keys: list,
                                   collector: str,
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

        querystring = {
            "pageSize": 10000
        }
        # Indicates whether to report only "current" stat values, i.e. skip the stat-s that haven't published any value
        # during recent collection cycles.
        current_only = True

        payload = {
            "resourceId": uuid_list,
            "statKey": keys,
            "currentOnly": current_only
        } if kind == 'stats' else {
            "resourceIds": uuid_list,
            "propertyKeys": keys,
            "currentOnly": current_only
        }

        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.post(url,
                                     params=querystring,
                                     data=json.dumps(payload),
                                     verify=False,
                                     headers=headers,
                                     timeout=60)
        except requests.exceptions.ReadTimeout as e:
            logger.error(f'{collector} has timed out getting latest data from: {target} - Error: {e}')
            q.put([[], 504, 999])
            return
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
        querystring = {
            'pageSize': 10000
        }
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
                                     params=querystring,
                                     verify=False,
                                     headers=headers,
                                     timeout=30)
        except requests.exceptions.ReadTimeout as e:
            logger.error(f'Request for getting project folder timed out - Error: {e}')
            return [], 504
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

    def get_alerts(self, target: str, token: str,
                   alert_criticality: list,  # [ "CRITICAL", "IMMEDIATE", "WARNING", "INFORMATION" ]
                   resourcekinds: list,  # [ "HostSystem" ]
                   active_only=True,
                   resourceIds: list = None,
                   adapterkinds: list = None,  # [ "VMWARE" ]
                   resource_names: list = None,  # [ "Windows2017VM", "Windows2018VM" ]
                   regex: list = None  # [ "\\\\S+-BNA-\\\\S+", null ]
                   ):
        logger.debug('>---------------------------------- get_alerts')
        logger.debug(f'target   : {target}')

        alerts = list()
        url = f'https://{target}/suite-api/api/alerts/query'
        querystring = {
            "pageSize": 10000
        }

        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': "vRealizeOpsToken " + token
        }
        payload = {
            "compositeOperator": "AND",
            "resource-query": {
                "name": resource_names,
                "regex": regex,
                "adapterKind": adapterkinds,
                "resourceKind": resourcekinds,
                "resourceId": resourceIds,
                "statKeyInclusive": True
            },
            "activeOnly": active_only,
            "alertCriticality": alert_criticality
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.post(url,
                                     data=json.dumps(payload),
                                     params=querystring,
                                     verify=False,
                                     headers=headers,
                                     timeout=30)
        except requests.exceptions.ReadTimeout as e:
            logger.error(f'Request for getting project folder timed out - Error: {e}')
            return [], 504
        except Exception as e:
            logger.error(f'Problem getting project folder - Error: {e}')
            return [], 503
        if response.status_code == 200:
            try:
                for alert in response.json()['alerts']:
                    alert_dict = dict()
                    alert_dict["resourceId"] = alert["resourceId"]
                    alert_dict["alertLevel"] = alert["alertLevel"]
                    alert_dict["status"] = alert['status']
                    alert_dict["alertDefinitionName"] = alert.get("alertDefinitionName", alert["alertDefinitionId"])
                    alert_dict["alertImpact"] = alert["alertImpact"]
                    alert_dict["alertDefinitionId"] = alert["alertDefinitionId"]
                    alerts.append(alert_dict)
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Catching JSONDecodeError for target: {target}'
                             f' - Error: {e}')
                return [], response.status_code
        else:
            logger.error(f'Return code get_alerts: {response.status_code} != 200 for {target} : {response.text}')
            return [], response.status_code

        logger.debug(f'Fetched alerts: {len(alerts)}')
        logger.debug('<--------------------------------------------------')

        return alerts, response.status_code, response.elapsed.total_seconds()

    def get_definitions(self, target, token, name: str):
        url = f'https://{target}/suite-api/api/{name}'

        querystring = {
            'pageSize': 10000
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
                                    headers=headers,
                                    timeout=30)
        except requests.exceptions.ReadTimeout as e:
            logger.error(f'Request to {url} timed out. Error: {e}')
            return {}
        except Exception as e:
            logger.error(f'Problem connecting to {target} - Error: {e}')
            return {}

        if response.status_code == 200:
            return response.json()

        else:
            logger.error(f'Problem getting {name} {target} : {response.text}')
            return {}

    def get_alert_recommendations(self, target, token):
        return self.get_definitions(target, token, name='recommendations')

    def get_alert_symptomdefinitions(self, target, token):
        return self.get_definitions(target, token, name='symptomdefinitions')

    def get_alertdefinitions(self, target, token):
        alertdefinitions = self.get_definitions(target, token, name='alertdefinitions')
        symptomdefinitions = self.get_alert_symptomdefinitions(target, token)
        recommendations = self.get_alert_recommendations(target, token)

        # mapping symptoms and recommendations to alerts
        alerts = dict()
        for alert in alertdefinitions['alertDefinitions']:
            alert_entry = dict()
            alert_entry['id'] = alert.get('id')
            alert_entry['name'] = alert.get('name')
            alert_entry['description'] = alert.get('description', 'n/a')
            alert_entry['adapterKindKey'] = alert.get('adapterKindKey', 'n/a')
            alert_entry['resourceKindKey'] = alert.get('resourceKindKey', 'n/a')
            alert_entry['symptoms'] = list()
            symptomdefinition_ids = alert.get("states", [])[0].get("base-symptom-set", {}).get(
                "symptomDefinitionIds", [])
            for symptom_id in symptomdefinition_ids:
                for symptomdefinition_id in symptomdefinitions["symptomDefinitions"]:
                    if symptom_id == symptomdefinition_id['id']:
                        symptom_entry = dict()
                        symptom_entry['name'] = symptomdefinition_id['name']
                        symptom_entry['state'] = symptomdefinition_id['state']
                        alert_entry['symptoms'].append(symptom_entry)

            alert_entry['recommendations'] = list()
            recommendation_ids = alert.get("states", [])[0].get("recommendationPriorityMap", {})
            for recommendation in recommendation_ids:
                for rd in recommendations["recommendations"]:
                    if recommendation == rd["id"]:
                        recommendation_entry = dict()
                        recommendation_entry['id'] = rd.get("id")
                        recommendation_entry['description'] = remove_html_tags(rd.get("description"))
                        alert_entry['recommendations'].append(recommendation_entry)
            alerts[alert.get('id')] = alert_entry
        return alerts

    def get_service_states(self, target: str, token: str):
        url = f'https://{target}/suite-api/api/deployment/node/services/info'
        timeout = 40
        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'Authorization': f"vRealizeOpsToken {token}"
        }
        disable_warnings(exceptions.InsecureRequestWarning)
        try:
            response = requests.get(url,
                                    verify=False,
                                    headers=headers,
                                    timeout=timeout)
        except requests.exceptions.ReadTimeout as e:
            logger.error(f'Request to {url} timed out. Error: {e}')
            return {}, 504, timeout
        except Exception as e:
            logger.error(f'Problem connecting to {target} - Error: {e}')
            return {}, 503, 0

        if response.status_code == 200:
            return response.json(), response.status_code, response.elapsed.total_seconds()
        else:
            logger.error(f'Problem getting service stats from {target} : {response.text}')
            return response.json(), response.status_code, response.elapsed.total_seconds()
