from .modules import *
# from . import devices
# from . import keymaps

# modules_dir = build_dir.joinpath("modules")

# modules = {}

# class Dependency(object):
#     def __init__(self, name, path, type='local'):
#         self.name = name
#         self.path = path
#         self.type = type
#         modules[self.name] = self

#     @classmethod
#     def from_name_version(self, name, version, update):
#         version_re = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')
#         if version_re.match(version) is not None:
#             if name in registry_example:
#                 cli.log.info(f"Found registry module: {name}")
#                 return RegistryDependency(name, registry_example[name].url, version, update)
#             else:
#                 cli.log.error("Cannot find dependency in registry")
#                 return None
#         else:
#             cli.log.info(f"Found local module: {name} at {version}")
#             return Dependency(name, Path(version).resolve())

# class RegistryDependency(Dependency):
#     def __init__(self, name, url, version, update):
#         super().__init__(name, modules_dir.joinpath(name).resolve(), type='registry')
#         self.url = url
#         if update:
#             if not self.path.joinpath(".git").exists():
#                 self.path.mkdir(exist_ok=True, parents=True)
#                 cli.run(['git', '-b', 'v' + version, 'clone', '--depth', '1', self.url, '.'], cwd=self.path)
#             else:
#                 cur_ver = cli.run(['git', 'describe', '--tags'], cwd=self.path).stdout.strip()
#                 # print(f'{self.name}: {cur_ver}')
#                 if cur_ver != 'v'+version:
#                     # print(f'checking out {version}')
#                     # TODO be smarter about tags & current versions, checking the qmk.json in the latest, etc
#                     cli.run(['git', 'fetch', '--all', '--tags'], cwd=self.path)
#                     cli.run(['git', 'checkout', 'v' + version], cwd=self.path)
