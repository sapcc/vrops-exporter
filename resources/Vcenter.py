from tools import get_resources
from resources.Datacenter import Datacenter


class Vcenter:

    def __init__(self, target, user, password, name, uuid):
        self._target = target
        self._user = user
        self._password = password
        self.uuid = uuid
        self.name = name
        self.datacenter = list()

    def add_datacenter(self):
        for dc in get_resources(self, target=self._target, user=self._user, password=self._password,
                                resourcetype='resources', resourcekind='Datacenter', parentid=self.uuid):
            self.datacenter.append(Datacenter(target=self._target, user=self._user, password=self._password,
                                              name=dc['name'], uuid=dc['uuid']))


