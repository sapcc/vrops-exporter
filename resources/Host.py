from tools.Vrops import Vrops
from resources.Datastore import Datastore
from resources.VirtualMachine import VirtualMachine


class Host:

    def __init__(self, name, uuid):
        self.uuid = uuid
        self.name = name
        self.datastores = list()
        self.vms = list()

    def add_datastore(self, datastore):
        self.datastores.append(Datastore(datastore.get('name'), datastore.get('uuid')))

    def add_vm(self, vm):
        self.vms.append(VirtualMachine(vm.get('name'), vm.get('uuid')))

