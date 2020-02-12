import os
from tools.Resources import Resources
from resources.VirtualMachine import VirtualMachine


class Host:

    def __init__(self, target, token, name, uuid):
        self.target = target
        self.token = token
        self.uuid = uuid
        self.name = name
        self.vms = list()

    def add_vm(self):
        r = Resources()
        project_ids = Resources.get_project_id(r, target=self.target, token=self.token)
        for vm in Resources.get_virtualmachines(r, target=self.target, token=self.token, parentid=self.uuid):
            if vm['uuid'] in project_ids:
                if os.environ['DEBUG'] == '1':
                    print(vm['name'] + ' has project id: ' + project_ids['project_id'])
                self.vms.append(VirtualMachine(name=vm['name'], uuid=vm['uuid'],
                                               project_id=project_ids['project_id']))
            else:
                self.vms.append(VirtualMachine(name=vm['name'], uuid=vm['uuid'],
                                               project_id='default internal'))
