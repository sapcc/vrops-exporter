from tools.Resources import Resources
from resources.Datacenter import Datacenter


class Vcenter(Resources):

    def __init__(self, name, uuid):
        self.uuid = uuid
        self.name = name
        self.datacenter = list()

    def add_datacenter(self):
        for dc in Resources.get_datacenter(self, parentid=self.uuid):
            self.datacenter.append(Datacenter(name=dc['name'], uuid=dc['uuid']))
