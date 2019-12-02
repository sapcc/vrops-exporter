from tools.get_resources import get_resources
from resources import *


class Cluster:

    def __init__(self, vcenter, name, uuid):
        self.vcenter = vcenter
        self.name = name
        self.uuid = uuid
        self.hosts = list()

    def add_host(self):
        for hosts in get_resources(target=self.vcenter.target,
                                   resourcetype='resources',
                                   resourcekind='HostSystem',
                                   parentid=self.uuid):
            self.hosts.append(Host(vcenter=self.vcenter, name=hosts['name'],
                                   uuid=hosts['uuid']))
