import tools.Resources
import resources.Cluster


class Datacenter:

    def __init__(self, target, name, uuid):
        self.target = target
        self.name = name
        self.uuid = uuid
        self.clusters = list()

    def add_cluster(self):
        for cluster in Resources.get_cluster(target=self.target, parentid=self.uuid):
            self.clusters.append(Cluster(target=self.target, name=cluster['name'], uuid=cluster['uuid']))
