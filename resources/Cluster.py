from tools.get_resources import get_resources
from resources.Host import Host


class Cluster:

    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid
        self.hosts = list()

    def add_host(self):

        for hosts in get_resources(self, resourcetype='resources', resourcekind='HostSystem'):
            self.hosts.append(Host(hosts['name'], hosts['uuid']))


