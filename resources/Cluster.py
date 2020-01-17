import os
from tools.Resources import Resources
from resources.Host import Host


class Cluster(Resources):

    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid
        self.hosts = list()

    def add_host(self):
        for hosts in Resources.get_hosts(self, parentid=self.uuid):
            self.hosts.append(Host(name=hosts['name'], uuid=hosts['uuid']))
