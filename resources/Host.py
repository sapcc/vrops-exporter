from tools.get_resources import get_resources
from resources.VirtualMachine import VirtualMachine


class Host:

    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid
        self.vms = list()

    def add_vm(self):

        # collect project_ids
        project_ids = list()

        for project in get_resources(self,
                                     resourcetype='resources',
                                     resourcekind='VMFolder'):
            if project['name'].startswith('Project'):
                p_ids = dict()
                p_ids['project_id'] = project['name'][project['name'].find("(")+1:project['name'].find(")")]
                p_ids['uuid'] = project['uuid']
                project_ids.append(p_ids)

        # fetch the virtual machines depending on the project_id and add them to a host
        for project_id in project_ids:
            for vm in get_resources(self,
                                    resourcetype="resources",
                                    resourcekind="VirtualMachine",
                                    parentid=project_id['uuid']):
                self.vms.append(VirtualMachine(vm['uuid'], project_id['project_id']))

        for vm in get_resources(self,
                                resourcetype="resources",
                                resourcekind="VirtualMachine"):
            for vm_id in self.vms:
                if vm['uuid'] != vm_id.uuid:
                    self.vms.append(VirtualMachine(vm['uuid'], project_id='default internal'))

