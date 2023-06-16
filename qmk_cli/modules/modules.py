from glob import glob
from io import BytesIO
import os
import re
from urllib.request import urlopen
from zipfile import ZipFile
import jsonschema

from pathlib import Path
from qmk_cli.json import json_load, validate
from milc import cli

from . import devices
from . import keymaps
from qmk_cli import registry

modules = {}
root_module = None


build_dir = Path(os.path.join(os.getcwd(), ".build"))

qmk_json_path = Path(os.path.join(os.getcwd(), "qmk.json"))

def _is_version_str(version):
    version_re = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')
    return version_re.match(version) is not None

def get_module(name):
    return modules[name]

def has_qmk_json():
    return qmk_json_path.exists()

def get_paths():
    paths = []
    for module in modules.values():
        paths.append(cli.run(['cygpath', '-u', str(module.path)]).stdout.strip())
    return ";".join(paths)

def get_user_module():
    if isinstance(root_module, UserModule):
        return cli.run(['cygpath', '-u', str(root_module.path)]).stdout.strip()
    else:
        return None

def get_qmk_location():
    qmk_location = None
    qmk_version = None

    if root_module.qmk_location:
        qmk_location = root_module.qmk_location
    elif root_module.qmk_version:
        qmk_version = root_module.qmk_version
    else:
        for module in root_module.dependencies:
            if module.qmk_location:
                # TODO compare via policy
                qmk_location = module.qmk_location
            else:
                # TODO compare via policy
                qmk_version = module.qmk_version

    if not qmk_location and qmk_version:
        qmk_location = build_dir.joinpath("qmk_firmware", qmk_version)
        if not qmk_location.exists():
            response = urlopen(f"https://github.com/jackhumbert/qmk_firmware_personal/releases/download/v{qmk_version}/qmk_firmware.zip")
            zipfile = ZipFile(BytesIO(response.read()))
            zipfile.extractall(path=qmk_location)
    elif not qmk_location:
        cli.log.error("No qmk_version is specified in qmk.json nor its dependencies")

    path = Path(qmk_location)
    if path.exists():
        return path.resolve()    


class Module:
    def __init__(self, json, path):
        validate(json, 'qmk.module.v1')
        self._path = path
        self._json = json
        version = self.json.get('qmk_version', None)
        self._qmk_version = version if version and _is_version_str(version) else None
        self._qmk_location = version if version and not _is_version_str(version) else None

    @classmethod
    def from_json_path(self, json_path, name=None, devices=None):
        json = json_load(json_path)
        if 'type' in json:
            if json['type'] == 'device':
                # allow overriding of module name via root
                if not name and 'module_name' in json:
                    name = json["module_name"]
                return DeviceModule(json, name, json_path.parent, devices)
            elif json['type'] == 'user':
                return UserModule(json, json_path.parent)
            # elif qmk_json['type'] == 'feature'
            
    @classmethod
    def from_dependency(self, name, version, update, devices=None):
        if _is_version_str(version):
            entry = registry.get_entry(name)
            if entry:
                cli.log.info(f"Found registry module: {name}")
                return Module.from_json_path(entry.resolve(version, update).joinpath("qmk.json"), devices=devices)
            else:
                cli.log.error("Cannot find dependency in registry")
                return None
        else:
            cli.log.info(f"Found local module: {name} at {version}")
            return Module.from_json_path(Path(version).resolve().joinpath("qmk.json"), name, devices=devices)

    @property
    def path(self):
        return self._path
    
    @property
    def json(self):
        return self._json
    
    @property
    def qmk_version(self):
        return self._qmk_version
    
    @property
    def qmk_location(self):
        return self._qmk_location

class DeviceModule(Module):
    def __init__(self, json, name, path, device_list):
        super().__init__(json, path)
        validate(json, 'qmk.device_module.v1')
        self._name = name
        # if not self.name is json['module_name']:
            # cli.log.warn(f"Name specified in qmk.json ({json['module_name']}) does not match dependency name ({self.name})")
        modules[self.name] = self
        
        self.devices = []
        if device_list:
            for device_name in device_list:
                if self.path.joinpath(device_name, "rules.mk").exists:
                    device = devices.ModuleDevice(name + "/" + device_name, device_name, self)
                    self.devices.append(device)
                    devices.add(device)
                else:
                    cli.log.error(f"Device {device_name} does not exist in {path}")
        else:
            device_wildcard = os.path.join(self.path, "**", "rules.mk")
            paths = [path for path in glob(device_wildcard, recursive=True) if os.path.sep + 'keymaps' + os.path.sep not in path]
            for path in sorted(set(paths)):
                folder = path.replace(str(self.path) + os.path.sep, "").replace(os.path.sep + "rules.mk", "")
                device = devices.ModuleDevice(name + "/" + folder, folder, self)
                self.devices.append(device)
                devices.add(device)
        if 'module_version' in json:
            self._version = json['module_version']

    @property
    def name(self):
        return self._name
    
    @property
    def version(self):
        return self._version

class UserModule(Module):
    def __init__(self, json, path):
        super().__init__(json, path)
        validate(json, 'qmk.user_module.v1')
        if 'dependencies' in json:
            # print("loading dependencies")
            self.dependencies = []
            for name, version in json['dependencies'].items():
                if isinstance(version, str):
                    module = Module.from_dependency(name, version, True)
                elif isinstance(version, object):
                    if 'devices' in version:
                        module = Module.from_dependency(name, version['version'], True, version['devices'])
                    else:
                        module = Module.from_dependency(name, version['version'], True)
                if module:
                    self.dependencies.append(module)
                # else:
                    # print(f"Cannot find dependency '{name}': '{version}' (looked at '{str(dep_json_path)}')")
                    

        if 'keymaps' in json:
            for device, value in json['keymaps'].items():
                keymap_list = value if isinstance(value, list) else [value]
                for keymap in keymap_list:
                    keymap_wildcard = os.path.join(self.path, keymap, "**", "keymap.c")
                    keymap_cs = glob(keymap_wildcard, recursive=True)
                    for keymap_c in sorted(set(keymap_cs)):
                        path = str(Path(keymap_c).resolve().parent)
                        name = path.replace(str(self.path) + os.path.sep, "")
                        keymaps.add(device, name, path)

if qmk_json_path.exists():
    os.environ['QMK_JSON'] = str(qmk_json_path)
    root_module = Module.from_json_path(qmk_json_path)
    # if 'dependencies' in qmk_json:
    #     for name, version in qmk_json['dependencies'].items():
    #         Module.from_dependency(name, version, True)