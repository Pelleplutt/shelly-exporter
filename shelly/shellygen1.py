import requests
from . import shellymetrics

def shellygen1factory(ip):
    g1url = f'http://{ip}/shelly'
    r = requests.get(g1url)
    if r.status_code == 200:
        json = r.json()

        if json.get('type') is not None:
            if json['type'] == 'SHPLG-S':
                return ShellyPlugS(ip, shellyjson=json)

    return None

class ShellyGen1(object):
    def __init__(self, ip, shellyjson=None):
        self.ip = ip
        self.reinit(shellyjson)

    def __str__(self) -> str:
        return f'{self.ip} is a {self.model} running on {self.fw} with {self.num_meters} meters and {self.num_outputs} outputs'

    def reinit(self, shellyjson=None):
        if shellyjson is None:
            shellyjson = self.apiget_shellyjson()

        self.mac = shellyjson.get('mac')
        self.fw = shellyjson.get('fw')
        self.num_outputs = shellyjson.get('num_outputs')
        self.num_meters = shellyjson.get('num_meters')

        if shellyjson.get('auth'):
            raise AssertionError('Device has authentication, cannot handle that')

    def apicall(self, call, params=None):
        g1url = f'http://{self.ip}/{call}'
        r = requests.get(g1url)
        return r.json()

    # {
    #	"type": "SHPLG-S",
    #	"mac": "C8C9A3890E06",
    #	"auth": false,
    #	"fw": "20230109-114426/v1.12.2-g32055ee",
    #	"discoverable": false,
    #	"num_outputs": 1,
    #	"num_meters": 1
    #}
    def apiget_shellyjson(self):
        return self.apicall('shelly')

    # {
    # 	"wifi_sta": {
    # 		"connected": true,
    # 		"ssid": "TNet",
    # 		"ip": "192.168.30.212",
    # 		"rssi": -61
    # 	},
    # 	"cloud": {
    # 		"enabled": false,
    # 		"connected": false
    # 	},
    # 	"mqtt": {
    # 		"connected": true
    # 	},
    # 	"time": "08:42",
    # 	"unixtime": 1674286970,
    # 	"serial": 165,
    # 	"has_update": false,
    # 	"mac": "C8C9A3890E06",
    # 	"cfg_changed_cnt": 3,
    # 	"actions_stats": {
    # 		"skipped": 0
    # 	},
    # 	"relays": [{
    # 		"ison": true,
    # 		"has_timer": false,
    # 		"timer_started": 0,
    # 		"timer_duration": 0,
    # 		"timer_remaining": 0,
    # 		"overpower": false,
    # 		"source": "input"
    # 	}],
    # 	"meters": [{
    # 		"power": 11.92,
    # 		"overpower": 0.00,
    # 		"is_valid": true,
    # 		"timestamp": 1674290570,
    # 		"counters": [11.933, 11.950, 11.985],
    # 		"total": 25383
    # 	}],
    # 	"temperature": 24.55,
    # 	"overtemperature": false,
    # 	"tmp": {
    # 		"tC": 24.55,
    # 		"tF": 76.19,
    # 		"is_valid": true
    # 	},
    # 	"update": {
    # 		"status": "idle",
    # 		"has_update": false,
    # 		"new_version": "20230109-114426/v1.12.2-g32055ee",
    # 		"old_version": "20230109-114426/v1.12.2-g32055ee"
    # 	},
    # 	"ram_total": 52064,
    # 	"ram_free": 38480,
    # 	"fs_size": 233681,
    # 	"fs_free": 166162,
    # 	"uptime": 128166
    # }
    def apiget_status(self):
        return self.apicall('status')

    def get_metrics(self):
        status = self.apiget_status()
        metrics = []
        metrics.extend([
            shellymetrics.ShellyMetricSysstat(self, 
                uptime=status.get('uptime'),
                ram_size=status.get('ram_total'),
                ram_free=status.get('ram_free'),
                fs_size=status.get('fs_size'),
                fs_free=status.get('fs_free')),
            shellymetrics.ShellyMetricWifi(self,
                connected=status['wifi_sta'].get('connected'),
                rssi=status['wifi_sta'].get('rssi')),
            shellymetrics.ShellyMetricDeviceTemperature(self,
                temperature=status['tmp'].get('tC'))
        ])

        for relay_id in range(len(status['relays'])):
            labels = {'id': str(relay_id)}
            metrics.append( 
                shellymetrics.ShellyMetricPowerMeter(self, labelvalues=labels,
                    output=status['relays'][relay_id]['ison'],
                    apower=status['meters'][relay_id]['power'],
                    energy_total=float(status['meters'][relay_id]['total']) / 1000 / 60, # values supplied in watt minutes
                )
            )

        return metrics


class ShellyPlugS(ShellyGen1):
    model = 'Shelly Plug S'
    pass