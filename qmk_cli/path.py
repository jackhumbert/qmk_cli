import platform
from pathlib import Path

def get_os_path(path):  
    """Get msys cli-compatible path
    """
    platform_id = platform.platform().lower()

    if 'windows' in platform_id:
        from milc import cli
        return cli.run(['cygpath', '-u', str(path)]).stdout.strip()
    else:
        return str(path)
    
def get_qmk_path():
    return get_os_path(Path(__file__).parent.parent / 'qmk')