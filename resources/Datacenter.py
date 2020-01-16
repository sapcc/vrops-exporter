from tools.Resources import Resources
from resources.Cluster import Cluster


class Datacenter(Resources):

    def __init__(self, target, name, uuid):
        self.target = target
        self.name = name
        self.uuid = uuid
        self.clusters = list()

    def add_cluster(self):
        for cluster in Resources.get_cluster(self, target=self.target, parentid=self.uuid):
            self.clusters.append(Cluster(target=self.target, name=cluster['name'], uuid=cluster['uuid']))
