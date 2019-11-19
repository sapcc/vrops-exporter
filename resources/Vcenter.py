from tools.get_resources import get_resources
from resources.Cluster import Cluster


class Vcenter:

    def __init__(self):
        self.uuid = get_resources(self, resourcetype='adapter')['uuid']
        self.name = get_resources(self, resourcetype='adapter')['name']
        self.clusters = list()
        self.datacenter = get_resources(self, resourcetype='resources', resourcekind='datacenter', parentid=self.uuid)

    def add_cluster(self):
        self.datacenter = get_resources(self, resourcetype='resources', resourcekind='datacenter')

        for cluster in get_resources(self, resourcetype='resources', resourcekind='ClusterComputeResource'):
            self.clusters.append(Cluster(cluster['name'], cluster['uuid']))


