class Vcenter:

    def __init__(self, vcenter, datacenter):
        # we need to fetch the uuids before
        self.uuid = vcenter
        self.clusters = list()
        self.datacenter = datacenter

    def add_cluster(self):
        pass

