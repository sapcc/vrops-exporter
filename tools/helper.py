def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def yaml_read(path):
    import yaml
    yml = dict()
    with open(path, 'r') as stream:
        try:
            yml = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return yml
