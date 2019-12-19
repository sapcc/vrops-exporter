import tools.Resources
import resources.Host



class Cluster:

    def __init__(self, target, name, uuid):
        self.target = target
        self.name = name
        self.uuid = uuid
        self.hosts = list()

    def add_host(self):
        for hosts in Resources.get_hosts(target=self.target, parentid=self.uuid):
            self.hosts.append(Host(target=self.target, name=hosts['name'],
                                   uuid=hosts['uuid']))
