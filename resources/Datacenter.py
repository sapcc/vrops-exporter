from tools.Resources import Resources
from resources.Cluster import Cluster


class Datacenter(Resources):

    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid
        self.clusters = list()

    def add_cluster(self):
        for cluster in Resources.get_cluster(self, parentid=self.uuid):
            self.clusters.append(Cluster(name=cluster['name'], uuid=cluster['uuid']))