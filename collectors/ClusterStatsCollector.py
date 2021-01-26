from BaseCollector import BaseCollector
from tools.Vrops import Vrops
import logging

logger = logging.getLogger('vrops-exporter')


class ClusterStatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'cluster'
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__

    def collect(self):
        logger.info(f'{ self.name } starts with collecting the metrics')

        token = self.get_target_tokens()
        token = token.setdefault(self.target, None)

        if not token:
            logger.warning(f'skipping { self.target } in { self.name }, no token')
            return

        http_response_code, http_gauge = self.create_http_response_metric(self.target, token, self.name)
        logger.debug(f'HTTP response code in {self.name} for {self.target}: {http_response_code}')
        yield http_gauge

        gauges = self.generate_gauges('stats', self.name, self.vrops_entity_name,
                                      ['vcenter', 'vccluster', 'datacenter'])
        if not gauges and http_response_code > 200:
            logger.critical(f'HTTP response code in {self.name} for {self.target}: {http_response_code}, no return')
            return

        uuids = self.get_clusters_by_target()
        for metric_suffix in gauges:
            statkey = gauges[metric_suffix]['statkey']
            values = Vrops.get_latest_stat_multiple(self.target, token, uuids, statkey, self.name)
            if not values:
                logger.warning(f'Skipping statkey: {statkey} in {self.name} , no return')
                continue

            for value_entry in values:
                metric_value = value_entry['stat-list']['stat'][0]['data']
                if metric_value:
                    metric_value = metric_value[0]
                    cluster_id = value_entry['resourceId']
                    gauges[metric_suffix]['gauge'].add_metric(
                            labels=[self.clusters[cluster_id]['vcenter'],
                                    self.clusters[cluster_id]['name'],
                                    self.clusters[cluster_id]['parent_dc_name'].lower()],
                            value=metric_value)

        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']
