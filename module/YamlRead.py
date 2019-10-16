import yaml


class YamlRead:
    def __init__(self, path):
        self._path = path

    def run(self):
        yml = dict()
        with open(self._path, 'r') as stream:
            try:
                yml = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        return yml
