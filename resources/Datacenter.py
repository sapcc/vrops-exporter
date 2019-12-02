from tools import get_resources
from resources import *


class Datacenter:

    def __init__(self, vcenter, name, uuid):
        self.vcenter = vcenter
        self.name = name
        self.uuid = uuid
        self.clusters = list()

    def add_cluster(self, vc):
        for cluster in get_resources(target=self.vcenter.target,
                                     resourcetype='resources',
                                     resourcekind='ClusterComputeResource',
                                     parentid=self.uuid):
            self.clusters.append(Cluster(vcenter=vc, name=cluster['name'], uuid=cluster['uuid']))

    """
        def get_project_ids(self):
        # collect project_ids

        for project in get_resources(resourcetype='resources',
                                                  resourcekind='VMFolder',
                                                  parentid=self.uuid):
            if project['name'].startswith('Project'):
                p_ids = dict()
                p_ids['project_id'] = project['name'][project['name'].find("(") + 1:project['name'].find(")")]
                p_ids['uuid'] = project['uuid']
                self.project_ids.append(p_ids)

        return self.project_ids
    """

