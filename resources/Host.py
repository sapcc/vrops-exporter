from tools.get_resources import get_resources
from resources.VirtualMachine import VirtualMachine


class Host:

    def __init__(self, target, name, uuid):
        self.target = target
        self.uuid = uuid
        self.name = name
        self.vms = list()

    def add_vm(self):
        # fetch the virtual machines depending on the project_id and add them to a host
        """
        for project_id in Datacenter:
            for folder in get_resources(self, target=self._target, user=self._user, password=self._password,
                                        resourcetype="resources",
                                        resourcekind="VirtualMachine",
                                        parentid=project_id['uuid']):
                for vm in get_resources(self, target=self._target, user=self._user, password=self._password,
                                        resourcetype="resources",
                                        resourcekind="VirtualMachine",
                                        parentid=folder['uuid']):
                    self.vms.append(VirtualMachine(name=vm['name'], uuid=vm['uuid'],
                                                   project_id=project_id['project_id']))
        """

        for vm in get_resources(target=self.target,
                                resourcetype="resources",
                                resourcekind="VirtualMachine",
                                parentid=self.uuid):
            self.vms.append(VirtualMachine(name=vm['name'], uuid=vm['uuid'], project_id='default internal'))
