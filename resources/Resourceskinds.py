class Vcenter:

    def __init__(self, target, token):
        self.target = target
        self.token = token
        self.datacenter = list()

    def add_datacenter(self, datacenter):
        self.datacenter.append(datacenter)


class Datacenter:

    def __init__(self):
        self.clusters = list()
        self.datastores = list()

    def add_cluster(self, cluster):
        self.clusters.append(cluster)

    def add_datastore(self, datastore):
        self.datastores.append(datastore)


class Cluster:

    def __init__(self, ):
        self.hosts = list()

    def add_host(self, host):
        self.hosts.append(host)


class Datastore:

    def __init__(self):
        self.type = "other"

    def get_type(self, name):
        if "p_ssd" in name:
            self.type = "vmfs_p_ssd"
        if "s_hdd" in name:
            self.type = "vmfs_s_hdd"
        if "eph" in name:
            self.type = "ephemeral"
        if "Management" in name:
            self.type = "Management"
        if "vVOL" in name:
            self.type = "vVOL"
        if "local" in name:
            self.type = "local"
        if "swap" in name:
            self.type = "NVMe"


class Host:

    def __init__(self):
        self.vms = list()

    def add_vm(self, vm):
        self.vms.append(vm)


class VirtualMachine:
    pass


class NSXTMgmtPlane:

    def __init__(self, target, token):
        self.target = target
        self.token = token
        self.adapter = list()

    def add_adapter(self, nsxt_adapter):
        self.adapter.append(nsxt_adapter)


class NSXTAdapterInstance:

    def __init__(self, target, token):
        self.target = target
        self.token = token
        self.management_cluster = list()

    def add_mgmt_cluster(self, mgmt_cluster):
        self.management_cluster.append(mgmt_cluster)


class NSXTManagementCluster:
    pass
