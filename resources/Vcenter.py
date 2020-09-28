from tools.vrops import Vrops
from resources.Datacenter import Datacenter


class Vcenter:

    def __init__(self, target, token, name, uuid):
        self.target = target
        self.token = token
        self.uuid = uuid
        self.name = name
        self.datacenter = list()

    def add_datacenter(self):
        vrops = Vrops()
        for dc in Vrops.get_datacenter(vrops, target=self.target, token=self.token, parentid=self.uuid):
            self.datacenter.append(Datacenter(target=self.target, token=self.token, name=dc['name'], uuid=dc['uuid']))
