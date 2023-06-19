# from . import get_entry
from .entry import RegistryEntry

registry_example = {
    "olkb": RegistryEntry("olkb", "OLKB", "https://github.com/jackhumbert/olkb_keyboards.git"),
    "reform_ortho": RegistryEntry("reform_ortho", "Reform Ortho", "https://github.com/olkb/reform_ortho_firmware.git")
}

def get_entry(name):
    return registry_example[name] if name in registry_example else None