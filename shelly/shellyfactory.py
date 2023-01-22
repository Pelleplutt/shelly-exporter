from . import shellygen1, shellygen2

def factory(ip):
    shelly = shellygen2.shellygen2factory(ip)
    if shelly is not None:
        return shelly
    shelly = shellygen1.shellygen1factory(ip)
    if shelly is not None:
        return shelly
