import logging

from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY

class Metric(object):
    def __init__(self, metric, description, labels):
        self.metric = metric
        self.description = description
        self.labels = labels

    def get_labels_for_prometheus_metric(self, all_labels):
        return list(map(lambda x: all_labels[x], self.labels))

class CounterMetric(Metric):
    def __init__(self, metric, description, labels):
        super().__init__(metric, description, labels)

    def get_prometheus_metric(self):
        return CounterMetricFamily(self.metric, self.description, labels=self.labels)


class Gaugemetric(Metric):
    def __init__(self, metric, description, labels):
        super().__init__(metric, description, labels)

    def get_prometheus_metric(self):
        return GaugeMetricFamily(self.metric, self.description, labels=self.labels)

class ShellyMetric(object):
    def __init__(self, shelly, labelvalues):
        self.shelly = shelly
        self.labelvalues = labelvalues

    @classmethod
    def setup_metrics(cls, metrics):
        for name, metric in cls.metrics.items():
            logging.debug(f'Adding metric {name} of type {metric.__class__.__name__} for {cls.__name__}')
            metrics[name] = metric.get_prometheus_metric()

    def get_labels(self):
        if self.labelvalues is not None:
            all_labels = self.labelvalues.copy()
        else:
            all_labels = {}
        all_labels['mac'] = self.shelly.mac
        all_labels['model'] = self.shelly.model

        return all_labels

    def add_to_metrics(self, metrics):
        for key, val in self.data.items():
            all_labels = self.get_labels()
            if val is not None:
                metrics[key].add_metric(self.metrics[key].get_labels_for_prometheus_metric(all_labels), float(val))

class ShellyMetricSysstat(ShellyMetric):
    metrics = {
        'restart_required': Gaugemetric('restart_required', 'Restart is required', 
                ['mac', 'model']),
        'uptime': CounterMetric('uptime_seconds', 'Seconds since last restart', 
                ['mac', 'model']),
        'ram_size': Gaugemetric('ram_size_kb', 'Size of internal ram', 
                ['mac', 'model']),
        'ram_free': Gaugemetric('ram_free_kb', 'Unused amount of internal ram', 
                ['mac', 'model']),
        'fs_size': Gaugemetric('fs_size_kb', 'Size of internal filesystem', 
                ['mac', 'model']),
        'fs_free': Gaugemetric('fs_free_kb', 'Unused amount of internal filesystem', 
                ['mac', 'model']),
    }

    def __init__(self, shelly, labelsvalues=None, restart_required=None, uptime=None, ram_size=None, ram_free=None, fs_size=None, fs_free=None):
        super().__init__(shelly, labelsvalues)
        self.data = {
            'restart_required': restart_required,
            'uptime': uptime,
            'ram_size': ram_size,
            'ram_free': ram_free,
            'fs_size': fs_size,
            'fs_free': fs_free,
        }

class ShellyMetricWifi(ShellyMetric):
    metrics = {
        'connected': Gaugemetric('wifi_connected', 'WiFi is connected', 
                ['mac', 'model']),
        'rssi': Gaugemetric('rssi_db', 'WiFi signal strength', 
                ['mac', 'model']),
    }

    def __init__(self, shelly, labelsvalues=None, connected=None, rssi=None):
        super().__init__(shelly, labelsvalues)
        self.data = {
            'connected': connected,
            'rssi': rssi,
        }