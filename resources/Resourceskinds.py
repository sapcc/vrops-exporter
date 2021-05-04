
class Vcenter:

    def __init__(self, target, token, uuid, name):
        self.target = target
        self.token = token
        self.uuid = uuid
        self.name = name
        self.datacenter = list()

    def add_datacenter(self, datacenter):
        self.datacenter.append(Datacenter(datacenter.get('name'), datacenter.get('uuid')))


class Datacenter:

    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid
        self.clusters = list()
        self.datastores = list()

    def add_cluster(self, cluster):
        self.clusters.append(Cluster(cluster.get('name'), cluster.get('uuid')))

    def add_datastore(self, datastore):
        self.datastores.append(Datastore(datastore.get('name'), datastore.get('uuid')))


class Cluster:

    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid
        self.hosts = list()

    def add_host(self, host):
        self.hosts.append(Host(host.get('name'), host.get('uuid')))


class Datastore:

    def __init__(self, name, uuid):
        self.name = str(name)
        self.uuid = uuid
        self.type = self.get_type()

    def get_type(self):
        if "p_ssd" in self.name:
            return "vmfs_p_ssd"
        if "s_hdd" in self.name:
            return "vmfs_s_hdd"
        if "eph" in self.name:
            return "ephemeral"
        if "Management" in self.name:
            return "Management"
        if "vVOL" in self.name:
            return "vVOL"
        if "local" in self.name:
            return "local"
        else:
            return "other"


class Host:

    def __init__(self, name, uuid):
        self.uuid = uuid
        self.name = name
        self.vms = list()

    def add_vm(self, vm):
        self.vms.append(VirtualMachine(vm.get('name'), vm.get('uuid')))


class VirtualMachine:

    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid


class NSX_T_Mgmt_Plane:

    def __init__(self, target, token):
        self.target = target
        self.token = token
        self.adapter = list()

    def add_adapter(self, adapter):
        self.adapter.append(NSX_T_Adapter_Instance(adapter.get('name'), adapter.get('uuid')))


class NSX_T_Adapter_Instance:

    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid
        self.management_cluster = list()

    def add_mgmt_cluster(self, mgmt_cluster):
        self.management_cluster.append(NSX_T_ManagementCluster(mgmt_cluster.get('name'), mgmt_cluster.get('uuid')))


class NSX_T_ManagementCluster:

    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid
