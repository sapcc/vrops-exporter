from tools.Resources import Resources
from resources.Host import Host


class Cluster:

    def __init__(self, target, name, uuid):
        self.target = target
        self.name = name
        self.uuid = uuid
        self.hosts = list()

    def add_host(self):
        res = Resources()
        for hosts in res.get_hosts(target=self.target, parentid=self.uuid):
            self.hosts.append(Host(target=self.target, name=hosts['name'],
                                   uuid=hosts['uuid']))
