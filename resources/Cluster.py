from tools.Resources import Resources
from resources.Host import Host


class Cluster:

    def __init__(self, target, token, name, uuid):
        self.target = target
        self.token = token
        self.name = name
        self.uuid = uuid
        self.hosts = list()

    def add_host(self):
        r = Resources()
        for hosts in Resources.get_hosts(r, target=self.target, token=self.token, parentid=self.uuid):
            self.hosts.append(Host(target=self.target, token=self.token, name=hosts['name'],
                                   uuid=hosts['uuid']))
