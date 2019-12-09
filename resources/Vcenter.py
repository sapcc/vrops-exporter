from tools.get_resources import Resources
from resources.Datacenter import Datacenter


class Vcenter:

    def __init__(self, target, name, uuid):
        self.target = target
        self.uuid = uuid
        self.name = name
        self.datacenter = list()

    def add_datacenter(self):
        for dc in Resources.get_resources(target=self.target, resourcekind='Datacenter',
                                          parentid=self.uuid):
            self.datacenter.append(Datacenter(target=self.target, name=dc['name'], uuid=dc['uuid']))
