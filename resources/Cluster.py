from tools.Vrops import Vrops
from resources.Host import Host


class Cluster:

    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid
        self.hosts = list()

    def add_host(self, host):
        self.hosts.append(Host(host.get('name'), host.get('uuid')))
