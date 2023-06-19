keymaps = {}

def add(device_name, keymap_name, path):
    if not device_name in keymaps:
        keymaps[device_name] = {}
    keymaps[device_name][keymap_name] = path

def has_keymap(device_name: str, keymap_name: str):
    return device_name in keymaps and keymap_name in keymaps[device_name]

def get_keymaps(device_name: str):
    return keymaps[device_name].keys()

def get_keymap_path(device_name: str, keymap_name: str):
    return keymaps[device_name][keymap_name]

def get_all_keymaps():
    targets = []
    for device, keymap_list in keymaps.items():
        for keymap in keymap_list:
            targets.append((device, keymap))
    return targets