from tools.get_resources import get_resources
from resources.Host import Host


class Cluster:

    def __init__(self, target, user, password, name, uuid):
        self._target = target
        self._user = user
        self._password = password
        self.uuid = uuid
        self.name = name
        self.hosts = list()

    def add_host(self):

        for hosts in get_resources(self, target=self._target, user=self._user, password=self._password,
                                   resourcetype='resources', resourcekind='HostSystem', parentid=self.uuid):
            self.hosts.append(Host(target=self._target,user=self._user, password=self._password,
                                   name=hosts['name'], uuid=hosts['uuid']))


