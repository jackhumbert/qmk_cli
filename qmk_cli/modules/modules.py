from glob import glob
import os
import re
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
    qmk_version = None
    if root_module.qmk_version:
        # qmk_version defined in our root qmk_json
        qmk_version = root_module.qmk_version
    else:
        # check dependencies for version
        for module in root_module.dependencies:
            if module.qmk_version:
                # TODO compare via policy
                qmk_version = module.qmk_version

    if not qmk_version:
        cli.log.error("No qmk_version is specified in qmk.json nor its dependencies")

    # if qmk_version == number:
    #     # qmk-managed version
    #     TODO make sure we have the qmk version specified
    # else:
    #     # locally-managed qmk_firmware repo
    path = Path(qmk_version)
    if path.exists():
        return path.resolve()    


class Module:
    def __init__(self, json, path):
        self._path = path
        self._json = json

        validate(json, 'qmk.module.v1')

        self._qmk_version = self.json['qmk_version']

    @classmethod
    def from_json_path(self, json_path, name=None):
        json = json_load(json_path)
        if 'type' in json:
            if json['type'] == 'device':
                # allow overriding of module name via root
                if not name and 'module_name' in json:
                    name = json["module_name"]
                return DeviceModule(json, name, json_path.parent)
            elif json['type'] == 'user':
                return UserModule(json, json_path.parent)
            # elif qmk_json['type'] == 'feature'
            
    @classmethod
    def from_dependency(self, name, version, update):
        version_re = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')
        if version_re.match(version) is not None:
            entry = registry.get_entry(name)
            if entry:
                cli.log.info(f"Found registry module: {name}")
                return Module.from_json_path(entry.resolve(version, update).joinpath("qmk.json"))
            else:
                cli.log.error("Cannot find dependency in registry")
                return None
        else:
            cli.log.info(f"Found local module: {name} at {version}")
            return Module.from_json_path(Path(version).resolve().joinpath("qmk.json"), name)

    @property
    def path(self):
        return self._path
    
    @property
    def json(self):
        return self._json
    
    @property
    def qmk_version(self):
        return self._qmk_version

class DeviceModule(Module):
    def __init__(self, json, name, path):
        super().__init__(json, path)
        validate(json, 'qmk.device_module.v1')
        self._name = name
        # if not self.name is json['module_name']:
            # cli.log.warn(f"Name specified in qmk.json ({json['module_name']}) does not match dependency name ({self.name})")
        modules[self.name] = self
        
        device_wildcard = os.path.join(self.path, "**", "rules.mk")
        paths = [path for path in glob(device_wildcard, recursive=True) if os.path.sep + 'keymaps' + os.path.sep not in path]
        self.devices = []
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
                module = Module.from_dependency(name, version, True)
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

    @property
    def name(self):
        return self._name

if qmk_json_path.exists():
    os.environ['QMK_JSON'] = str(qmk_json_path)
    root_module = Module.from_json_path(qmk_json_path)
    # if 'dependencies' in qmk_json:
    #     for name, version in qmk_json['dependencies'].items():
    #         Module.from_dependency(name, version, True)