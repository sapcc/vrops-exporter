from BaseCollector import BaseCollector
from tools.Vrops import Vrops
import logging

logger = logging.getLogger('vrops-exporter')


class VCenterStatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'vcenter'
        self.name = self.__class__.__name__
        self.wait_for_inventory_data()

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

        gauges = self.generate_gauges('stats', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name])

        vc = self.get_vcenters(self.target)
        uuid = [vc[uuid]['uuid'] for uuid in vc][0]
        for metric_suffix in gauges:
            statkey = gauges[metric_suffix]['statkey']
            values = Vrops.get_latest_stat(self.target, token, uuid, statkey, self.name)
            if not values:
                logger.warning(f'Skipping statkey: {statkey} in {self.name} , no return')
                continue
            metric_value = float(values)
            gauges[metric_suffix]['gauge'].add_metric(labels=[self.vcenters[uuid]['name']],
                                                      value=metric_value)

        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']
