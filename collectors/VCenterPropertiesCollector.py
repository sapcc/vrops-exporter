from BaseCollector import BaseCollector
from tools.Vrops import Vrops
import logging

logger = logging.getLogger('vrops-exporter')


class VCenterPropertiesCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__
        self.vrops_entity_name = 'vcenter'

    def collect(self):
        logger.info(f'{self.name} starts with collecting the metrics')

        token = self.get_target_tokens()
        token = token.setdefault(self.target, None)

        if not token:
            logger.warning(f'skipping {self.target} in {self.name}, no token')
            return

        http_response_code, http_gauge = self.create_http_response_metric(self.target, token, self.name)
        logger.debug(f'HTTP response code in {self.name} for {self.target}: {http_response_code}')
        yield http_gauge

        if http_response_code > 200:
            logger.critical(f'HTTP response code in {self.name} for {self.target}: {http_response_code}, no return')
            return

        gauges = self.generate_gauges('property', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name])
        infos = self.generate_infos(self.name, self.vrops_entity_name,
                                    [self.vrops_entity_name])
        states = self.generate_states(self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'state'])

        vc = self.get_vcenters(self.target)
        uuid = [vc[uuid]['uuid'] for uuid in vc][0]
        for metric_suffix in gauges:
            propkey = gauges[metric_suffix]['property']
            metric_value = Vrops.get_property(self.target, token, uuid, propkey, self.name)
            if not metric_value:
                logging.warning(f'Skipping {propkey}, no value in respond')
                continue
            gauges[metric_suffix]['gauge'].add_metric(
                labels=[self.vcenters[uuid]['name']],
                value=metric_value)

        for metric_suffix in states:
            propkey = states[metric_suffix]['property']
            value = Vrops.get_property(self.target, token, uuid, propkey, self.name)
            if not value:
                logging.warning(f'Skipping {propkey}, no value in respond')
                continue
            metric_value = (1 if states[metric_suffix]['expected'] == value else 0)
            states[metric_suffix]['state'].add_metric(
                labels=[self.vcenters[uuid]['name'],
                        value],
                value=metric_value)

        for metric_suffix in infos:
            propkey = infos[metric_suffix]['property']
            info_value = Vrops.get_property(self.target, token, uuid, propkey, self.name)
            if not info_value:
                logging.warning(f'Skipping {propkey}, no value in respond')
                continue
            infos[metric_suffix]['info'].add_metric(
                labels=[self.vcenters[uuid]['name']],
                value={metric_suffix: info_value})

        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']
        for metric_suffix in infos:
            yield infos[metric_suffix]['info']
        for metric_suffix in states:
            yield states[metric_suffix]['state']
