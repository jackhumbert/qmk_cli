devices = {}

class ModuleDevice(object):
    def __init__(self, name, folder, module):
        self.name = name
        self.folder = folder
        self.module = module

def exists(device_name):
    return device_name in devices

def add(device):
    devices[device.name] = device

def get(device_name):
    return devices[device_name]