from tools.Vrops import Vrops
from resources.Datacenter import Datacenter


class Vcenter:

    def __init__(self, target, token, name, uuid):
        self.target = target
        self.token = token
        self.uuid = uuid
        self.name = name
        self.datacenter = list()

    def add_datacenter(self, datacenter):
        self.datacenter.append(Datacenter(datacenter.get('name'), datacenter.get('uuid')))
