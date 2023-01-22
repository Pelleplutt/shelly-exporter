import logging
import requests
import pprint
from . import shellymetrics

def shellygen2factory(ip):
    g1url = f'http://{ip}/rpc/Shelly.GetDeviceInfo'
    r = requests.get(g1url)
    if r.status_code == 200:
        json = r.json()

        if json.get('app') is not None:
            if json['app'] == 'Pro1PM':
                return ShellyPro1PM(ip=ip, deviceinfo=json)
            elif json['app'] == 'Plus1PM':
                return ShellyPlus1PM(ip=ip, deviceinfo=json)
            else:
                logging.info(f"There seems to be a shelly of type {json['app']} at {ip}, but cannot handle")

    return None

class ShellyGen2(object):
    def __init__(self, ip, deviceinfo=None):
        self.ip = ip
        self.reinit(deviceinfo)

    def __str__(self) -> str:
        return f'{self.ip} is a {self.model} running on {self.fw}'

    def reinit(self, deviceinfo=None):
        self.supportedmethods = {}

        if deviceinfo is None:
            deviceinfo = self.apiget_shelly_deviceinfo()

        self.mac = deviceinfo.get('mac')
        self.fw = deviceinfo.get('fw_id')
        self.num_outputs = deviceinfo.get('num_outputs')
        self.num_meters = deviceinfo.get('num_meters')

        if deviceinfo.get('auth'):
            raise AssertionError('Device has authentication, cannot handle that')

        supportedmethods = self.apiget_shelly_listmethods()
        self.set_supportedmethods(supportedmethods)
    
    def set_supportedmethods(self, supportedmethods):
        for m in supportedmethods['methods']:
            self.supportedmethods[m] = True

    def apicall(self, family, call, params=None):
        g2url = f'http://{self.ip}/rpc/{family}.{call}'
        r = requests.get(g2url)
        return r.json()

    def apiget_shelly_deviceinfo(self):
        return self.apicall('Shelly', 'DeviceInfo')

    def apiget_shelly_getstatus(self):
        return self.apicall('Shelly', 'GetStatus')

    # {
    # 	"methods": ["Switch.SetConfig", "Switch.GetConfig", ...]
    # } 
    def apiget_shelly_listmethods(self):
        return self.apicall('Shelly', 'ListMethods')

    def get_metrics(self):
        status = self.apiget_shelly_getstatus()
        metrics = []
        metrics.extend([
            shellymetrics.ShellyMetricSysstat(self, 
                uptime=status['sys'].get('uptime'),
                ram_size=status['sys'].get('ram_size'),
                ram_free=status['sys'].get('ram_free'),
                fs_size=status['sys'].get('fs_size'),
                fs_free=status['sys'].get('fs_free')),
            shellymetrics.ShellyMetricWifi(self,
                connected=status['wifi'].get('status')=='got ip',
                rssi=status['wifi'].get('rssi'))
        ])

        for key, val in status.items():
            if key[:7] == 'switch:':
                labels = {'id': str(val['id'])}
                metrics.append( 
                    shellymetrics.ShellyMetricPowerMeter(self, labelvalues=labels,
                        output=val['output'],
                        apower=val['apower'],
                        voltage=val['voltage'],
                        current=val['current'],
                        energy_total=val['aenergy']['total'],
                    )
                )

        return metrics


class ShellyPro1PM(ShellyGen2):
    model = 'Shelly Pro 1PM'
    pass

class ShellyPlus1PM(ShellyGen2):
    model = 'Shelly Plus 1PM'
    pass