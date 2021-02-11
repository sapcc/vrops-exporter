from resources.Cluster import Cluster


class Datacenter:

    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid
        self.clusters = list()

    def add_cluster(self, cluster):
        self.clusters.append(Cluster(cluster.get('name'), cluster.get('uuid')))

