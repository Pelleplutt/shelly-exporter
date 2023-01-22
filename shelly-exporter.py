#!/usr/bin/env python

import argparse
import logging
import os
import pprint
import re
import time

from shelly import shellyfactory
from shelly.shellymetrics import *
from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY

PORT = 9111


class ShellyCollector(object):
    def __init__(self, shelly_list):

        self.shellies = {}
        for ip in shelly_list:
            shelly = shellyfactory.factory(ip)
            if shelly is not None:
                self.shellies[ip] = shellyfactory.factory(ip)
                logging.info(f'Shelly at {ip} is {self.shellies[ip]}')
            else:
                logging.warning(f'Input {ip} cannot be resolved to a usable shelly, ignoring')

    def collect(self):
        logging.info('Collect')

        self.metrics = {}
        setup_metrics(self.metrics)

        for ip, shelly in self.shellies.items():
            shelly_metrics = shelly.get_metrics()
            for metric in shelly_metrics:
                metric.add_to_metrics(self.metrics)

        for key, val in self.metrics.items():
            yield val
        logging.info('Collect DONE')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Tibber Prometheus exporter')
    parser.add_argument('--port', dest='port', default=PORT, help='Port to listen to')
    parser.add_argument('--log', dest='log', default='INFO', help='Loglevel, one of DEBUG, INFO, WARNING, ERROR in decreasing detail')

    args = parser.parse_args()

    numeric_loglevel = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_loglevel, int):
        raise ValueError(f'Invalid log level: {args.log}')

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=numeric_loglevel,
        datefmt='%Y-%m-%d %H:%M:%S')


    if os.environ.get('SHELLY_LIST') is None:
        raise AssertionError('Missing SHELLY_LIST environment variable with list of shelly devices')

    shelly_list = []
    for ip in re.split(' |,|;', os.environ['SHELLY_LIST']):
        if not len(ip):
            next
        shelly_list.append(ip)

    REGISTRY.register(ShellyCollector(shelly_list))
    start_http_server(args.port)
    logging.info(f'HTTP server started on {args.port}')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.warning("Break")
exit(0)