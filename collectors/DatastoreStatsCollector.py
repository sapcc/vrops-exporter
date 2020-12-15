from BaseCollector import BaseCollector
from tools.Vrops import Vrops
import logging

logger = logging.getLogger('vrops-exporter')


class DatastoreStatsCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.vrops_entity_name = 'datastore'
        self.wait_for_inventory_data()
        self.name = self.__class__.__name__

    def collect(self):
        logger.info(f'{self.name} starts with collecting the metrics')

        token = self.get_target_tokens()
        token = token.setdefault(self.target, None)

        if not token:
            logger.warning(f'skipping {self.target} in {self.name}, no token')
            return

        gauges = self.generate_gauges('stats', self.name, self.vrops_entity_name,
                                      [self.vrops_entity_name, 'type', 'vcenter', 'datacenter', 'vccluster',
                                       'hostsystem'])

        uuids = self.get_datastores_by_target()
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
                    datastore_id = value_entry['resourceId']
                    gauges[metric_suffix]['gauge'].add_metric(
                        labels=[self.datastores[datastore_id]['name'],
                                self.datastores[datastore_id]['type'],
                                self.datastores[datastore_id]['vcenter'],
                                self.datastores[datastore_id]['datacenter'].lower(),
                                self.datastores[datastore_id]['cluster'],
                                self.datastores[datastore_id]['parent_host_name']],
                        value=metric_value)

        for metric_suffix in gauges:
            yield gauges[metric_suffix]['gauge']
