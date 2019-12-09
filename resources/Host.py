from tools.get_resources import Resources
from resources.VirtualMachine import VirtualMachine


class Host:

    def __init__(self, target, name, uuid):
        self.target = target
        self.uuid = uuid
        self.name = name
        self.vms = list()

    def add_vm(self):
        for vm in Resources.get_resources(target=self.target,
                                          resourcekind="VirtualMachine",
                                          parentid=self.uuid):
            for project_id in Resources.get_project_id(target=self.target):
                if project_id['uuid'] in vm:
                    self.vms.append(VirtualMachine(name=vm['name'], uuid=vm['uuid'],
                                                   project_id=project_id['project_id']))
                else:
                    self.vms.append(VirtualMachine(name=vm['name'], uuid=vm['uuid'],
                                                   project_id='default internal'))
