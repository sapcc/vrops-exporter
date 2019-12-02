from tools.get_resources import get_resources
from resources import *


class Vcenter:

    def __init__(self, vcenter, name, uuid):
        self.vcenter = vcenter
        self.uuid = uuid
        self.name = name
        self.datacenter = list()

    def add_datacenter(self):
        for dc in get_resources(self, resourcetype='resources', resourcekind='Datacenter', parentid=self.uuid):
            self.datacenter.append(Datacenter(vcenter=self.vcenter, name=dc['name'], uuid=dc['uuid']))


