import json
import os
import importlib
import sys
sys.path.append('./module')
from prometheus_client import CollectorRegistry
from prometheus_client.exposition import MetricsHandler, choose_encoder
from urllib.parse import urlparse, parse_qs
import tools.get_modules


def do_GET(self):
    registry = CollectorRegistry()
    params = parse_qs(urlparse(self.path).query)
    print(params)
    if len(params.keys()) != 0:
        try:
            print(params['target'])
            collector = VropsCollector(params['target'][0])
        except Exception as e:
            print("obviously missing params: " + json.dumps(params))
            print(e)
            return
        try:
            registry.register(collector)
        except Exception as e:
            print("failed to register: " + json.dumps(params))
            print(e)
            return

    encoder, content_type = choose_encoder(self.headers.get('Accept'))
    if 'name[]' in params:
        registry = registry.restricted_registry(params['name[]'])
    try:
        output = encoder(registry)
    except:
        self.send_error(500, 'error generating metric output')
        raise
    self.send_response(200)
    self.send_header('Content-Type', content_type)
    self.end_headers()
    self.wfile.write(output)


MetricsHandler.do_GET = do_GET


class VropsCollector:

    def __init__(self, target):
        self._target = target
        self._user = os.environ['USER']
        self._password = os.environ['PASSWORD']
        modules = tools.get_modules.get_modules()
        self._modules = modules[1]
        self._modules_dict = dict()
        for module in self._modules:
            self._modules_dict[module] = importlib.import_module(module, modules[0])

    def collect(self):
        for module in self._modules_dict.keys():
            imported_module = self._modules_dict[module]
            func = getattr(imported_module, module)
            res = func(self._target, self._user, self._password).collect()
            for i in res:
                yield i
