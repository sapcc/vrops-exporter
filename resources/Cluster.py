from tools.get_resources import get_resources
from resources.Host import Host


class Cluster:

    def __init__(self, target, name, uuid):
        self.target = target
        self.name = name
        self.uuid = uuid
        self.hosts = list()

    def add_host(self):
        for hosts in get_resources(target=self.target,
                                   resourcetype='resources',
                                   resourcekind='HostSystem',
                                   parentid=self.uuid):
            self.hosts.append(Host(target=self.target, name=hosts['name'],
                                   uuid=hosts['uuid']))
