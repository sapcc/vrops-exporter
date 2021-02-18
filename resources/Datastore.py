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
