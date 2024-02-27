from collectors.PropertiesCollector import PropertiesCollector
import json
import logging

logger = logging.getLogger('vrops-exporter')

class SDRSPropertiesCollector(PropertiesCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'storagepod' 
        self.label_names = [self.vrops_entity_name, 'vcenter', 'datacenter']
        self.nested_value_metric_keys = [
                "config|sdrsconfig|vmStorageAntiAffinityRules"
                ]

    def get_resource_uuids(self):
        return self.get_SDRS_clusters_by_target()

    def get_labels(self, resource_id, project_ids):
        return [self.sdrs_clusters[resource_id]['name'],
                self.sdrs_clusters[resource_id]['vcenter'],
                self.sdrs_clusters[resource_id]['parent_dc_name'].lower()] if resource_id in self.sdrs_clusters else []

    def unlock_nested_values(self, statkey, metric_value):

        match statkey:
            case "config|sdrsconfig|vmStorageAntiAffinityRules":
                return self.config_sdrsconfig_vmStorageAntiAffinityRules(metric_value)

    def config_sdrsconfig_vmStorageAntiAffinityRules(self, metric_value):

        try:
            metric_value = json.loads(metric_value)

        except (TypeError, json.decoder.JSONDecodeError) as e:
            logger.warning(f'metric_value is not a valid json: {e.args}, {metric_value}')
            return [], [], 0

        rules = metric_value.get("rules") or []
        amount_rules = len(rules)

        rule_labels = ['rule', 'rule_name', 'rule_type', 'valid', 'virtualmachine']
        rule_label_values = []

        for i, rule in enumerate(rules):
            mapped_vms = self.vm_mapping_helper(rule.get('virtualMachines', []))
            for vm in mapped_vms:
                rule_label_values.append([
                    f'{i+1}/{amount_rules}',
                    rule.get('name'),
                    rule.get('type'),
                    str(rule.get('valid')).lower(),
                    vm
                    ])
        return rule_labels, rule_label_values, 1

    def vm_mapping_helper(self, vm_list):
        mapped_vms = []
        vms = self.get_vms(self.target)
        for rule_vm in vm_list:
            for vm in vms:
                if rule_vm == vms[vm].get('internal_name'):
                    mapped_vms.append(vms[vm].get('name'))
        return mapped_vms
