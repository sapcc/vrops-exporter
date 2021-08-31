from urllib3 import disable_warnings
from urllib3 import exceptions
from tools.helper import chunk_list, remove_html_tags
from threading import Thread
from resources.Resourceskinds import *
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

    def get_adapter(self, target: str, token: str, adapterkind: str, adapter_obj) -> (list, int):
        url = f'https://{target}/suite-api/api/adapters'
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
                                    headers=headers)
        except Exception as e:
            logger.error(f'Problem connecting to {target} - Error: {e}')
            return adapter, 503

        if response.status_code == 200:
            for resource in response.json()["adapterInstancesInfoDto"]:
                adapter_object = adapter_obj(target, token)
                adapter_object.name = resource["resourceKey"]["name"]
                adapter_object.uuid = resource["id"]
                adapter.append(adapter_object)
            return adapter, response.status_code
        else:
            logger.error(f'Problem getting adapter {target} : {response.text}')
            return adapter, response.status_code

    def get_vcenter_adapter(self, target, token):
        return self.get_adapter(target, token, adapterkind="VMWARE", adapter_obj=Vcenter)

    def get_nsxt_adapter(self, target, token):
        return self.get_adapter(target, token, adapterkind="NSXTAdapter", adapter_obj=NSXTAdapterInstance)

    def get_resources(self, target: str, token: str,
                      uuids: list,
                      adapterkind: str,
                      resourcekinds: list,  # Array of resource kind keys
                      resource_class,  #
                      resource_status: list = None  # Array of resource data collection stats
                      ) -> (list, int):
        logger.debug(f'Getting {resourcekinds} from {target}')
        url = "https://" + target + "/suite-api/api/resources/bulk/relationships"
        querystring = {
            'pageSize': 10000
        }
        resource_status_array = [] if not resource_status else resource_status
        payload = {
            "relationshipType": "DESCENDANT",
            "resourceIds": uuids,
            "resourceQuery": {
                "adapterKind": [adapterkind],
                "resourceKind": resourcekinds,
                "resourceStatus": resource_status_array
            },
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
            return resources, 503

        if response.status_code == 200:
            try:
                relations = response.json()["resourcesRelations"]
                for resource in relations:
                    resource_object = resource_class()
                    resource_object.name = resource["resource"]["resourceKey"]["name"]
                    resource_object.uuid = resource["resource"]["identifier"]
                    resource_object.resourcekind = resource["resource"]["resourceKey"]["resourceKindKey"]
                    resource_object.parent = resource.get("relatedResources", [None])[0]
                    resource_identifiers = resource.get('resource', {}).get('resourceKey', {})\
                                                                       .get('resourceIdentifiers')
                    resource_object.internal_name = None
                    internal_name = list(filter(lambda identifier_type:
                                                identifier_type.get('identifierType', {}).get('name')
                                                == 'VMEntityObjectID', resource_identifiers))
                    if internal_name:
                        resource_object.internal_name = internal_name[0].get('value')
                    resources.append(resource_object)
                return resources, response.status_code
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Catching JSONDecodeError for target {target}'
                             f'- Error: {e}')
                return resources, response.status_code
        else:
            logger.error(f'Problem getting resources from {target} : {response.text}')
            return resources, response.status_code

    def get_datacenter(self, target, token, parent_uuids):
        return self.get_resources(target, token, parent_uuids, adapterkind="VMWARE",
                                  resourcekinds=["Datacenter"], resource_class=Datacenter)

    def get_cluster(self, target, token, parent_uuids):
        return self.get_resources(target, token, parent_uuids, adapterkind="VMWARE",
                                  resourcekinds=["ClusterComputeResource"], resource_class=Cluster)

    def get_datastores(self, target, token, parent_uuids):
        datastores, api_responding = self.get_resources(target, token, parent_uuids, adapterkind="VMWARE",
                                                        resourcekinds=["Datastore"], resource_class=Datastore)
        for datastore in datastores:
            datastore.get_type(datastore.name)
        return datastores, api_responding

    def get_hosts(self, target, token, parent_uuids):
        return self.get_resources(target, token, parent_uuids, adapterkind="VMWARE",
                                  resourcekinds=["HostSystem"], resource_class=Host)

    def get_vms(self, target, token, parent_uuids, vcenter_uuid):
        amount_vms, api_responding, _ = self.get_latest_stats_multiple(target, token, [vcenter_uuid],
                                                                       ['summary|total_number_vms'],
                                                                       'Inventory')
        number_of_vms = amount_vms[0].get('stat-list', {}).get('stat', [])[0].get('data', [0])[0] if \
            api_responding == 200 and amount_vms else 0

        # vrops cannot handle more than 10000 uuids in a single request
        split_factor = int(number_of_vms / 10000)
        if split_factor >= 1:
            uuids_chunked = list(chunk_list(parent_uuids, int(len(parent_uuids) / (split_factor + 1))))
            logger.debug(f'Chunking VM requests into {len(uuids_chunked)} chunks')
            vms = list()
            api_responding = list()
            for uuid_list in uuids_chunked:
                vm_chunks, api_chunk_responding = self.get_resources(target, token, uuid_list, adapterkind="VMWARE",
                                                                     resourcekinds=["VirtualMachine"],
                                                                     resource_class=VirtualMachine,
                                                                     resource_status=["DATA_RECEIVING"])
                vms.extend(vm_chunks)
                api_responding.append(api_chunk_responding)
            logger.debug(f'Number of VMs collected: {len(vms)}')
            return vms, max(api_responding)
        return self.get_resources(target, token, parent_uuids, adapterkind="VMWARE", resourcekinds=["VirtualMachine"],
                                  resource_class=VirtualMachine, resource_status=["DATA_RECEIVING"])

    def get_nsxt_mgmt_cluster(self, target, token, parent_uuids):
        return self.get_resources(target, token, parent_uuids, adapterkind="NSXTAdapter",
                                  resourcekinds=["ManagementCluster"], resource_class=NSXTManagementCluster)

    def get_nsxt_mgmt_nodes(self, target, token, parent_uuids):
        return self.get_resources(target, token, parent_uuids, adapterkind="NSXTAdapter",
                                  resourcekinds=["ManagementNode"], resource_class=NSXTManagementNode)

    def get_nsxt_mgmt_service(self, target, token, parent_uuids):
        return self.get_resources(target, token, parent_uuids, adapterkind="NSXTAdapter",
                                  resourcekinds=["ManagementService"], resource_class=NSXTManagementService)

    def get_nsxt_transport_zone(self, target, token, parent_uuids):
        return self.get_resources(target, token, parent_uuids, adapterkind="NSXTAdapter",
                                  resourcekinds=["TransportZone"], resource_class=NSXTTransportZone)

    def get_nsxt_transport_node(self, target, token, parent_uuids):
        return self.get_resources(target, token, parent_uuids, adapterkind="NSXTAdapter",
                                  resourcekinds=["TransportNode"], resource_class=NSXTTransportNode)

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
                                     headers=headers)
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
                    alert_dict["alertDefinitionName"] = alert["alertDefinitionName"]
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
                                    headers=headers)
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
