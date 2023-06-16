import os
from pathlib import Path
from milc import cli

modules_dir = Path(os.path.join(os.getcwd(), ".build", "modules"))

class RegistryEntry:
    def __init__(self, name, description, url):
        self.name = name
        self.description = description
        self.url = url
        self.path = modules_dir.joinpath(name)

    def resolve(self, version, update):
        if update:
            if not self.path.joinpath(".git").exists():
                self.path.mkdir(exist_ok=True, parents=True)
                cli.run(['git', 'clone', '-b', 'v' + version, '--depth', '1', self.url, '.'], cwd=self.path)
            else:
                cur_ver = cli.run(['git', 'describe', '--tags'], cwd=self.path).stdout.strip()
                # print(f'{self.name}: {cur_ver}')
                if cur_ver != 'v'+version:
                    # print(f'checking out {version}')
                    # TODO be smarter about tags & current versions, checking the qmk.json in the latest, etc
                    cli.run(['git', 'fetch', '--all', '--tags'], cwd=self.path)
                    cli.run(['git', 'checkout', 'v' + version], cwd=self.path)
        if not self.path.joinpath("qmk.json").exists():
            print(f"Could not resolve {self.name}@{version}")
        return self.path
