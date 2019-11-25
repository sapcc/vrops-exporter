from tools.get_resources import get_resources
from resources.Cluster import Cluster


class Datacenter:

    def __init__(self, target, user, password, name, uuid):
        self._target = target
        self._user = user
        self._password = password
        self.uuid = uuid
        self.name = name
        self.clusters = list()
        self.project_ids = list()

    def add_cluster(self):
        for cluster in get_resources(self, target=self._target, user=self._user, password=self._password,
                                     resourcetype='resources', resourcekind='ClusterComputeResource',
                                     parentid=self.uuid):
            self.clusters.append(Cluster(target=self._target, user=self._user, password=self._password,
                                         name=cluster['name'], uuid=cluster['uuid']))

    def get_project_ids(self):
        # collect project_ids

        for project in get_resources(self, target=self._target, user=self._user, password=self._password,
                                     resourcetype='resources',
                                     resourcekind='VMFolder',
                                     parentid=self.uuid):
            if project['name'].startswith('Project'):
                p_ids = dict()
                p_ids['project_id'] = project['name'][project['name'].find("(") + 1:project['name'].find(")")]
                p_ids['uuid'] = project['uuid']
                self.project_ids.append(p_ids)

        return self.project_ids
