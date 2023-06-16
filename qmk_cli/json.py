"""JSON helpers
"""
import json
import hjson
from pathlib import Path
import jsonschema

from milc import cli

def _dict_raise_on_duplicates(ordered_pairs):
    """Reject duplicate keys."""
    d = {}
    for k, v in ordered_pairs:
        if k in d:
            raise ValueError("duplicate key: %r" % (k,))
        else:
            d[k] = v
    return d

def json_load(json_file, strict=True):
    """Load a json file from disk.
    Note: file must be a Path object.
    """
    try:
        # Get the IO Stream for Path objects
        # Not necessary if the data is provided via stdin
        if isinstance(json_file, Path):
            json_file = json_file.open(encoding='utf-8')
        return hjson.load(json_file, object_pairs_hook=_dict_raise_on_duplicates if strict else None)

    except (json.decoder.JSONDecodeError, hjson.HjsonDecodeError) as e:
        cli.log.error('Invalid JSON encountered attempting to load {fg_cyan}%s{fg_reset}:\n\t{fg_red}%s', json_file, e)
        exit(1)
    except Exception as e:
        cli.log.error('Unknown error attempting to load {fg_cyan}%s{fg_reset}:\n\t{fg_red}%s', json_file, e)
        exit(1)
    
def load_jsonschema(schema_name):
    """Read a jsonschema file from disk.
    """
    if Path(schema_name).exists():
        return json_load(schema_name)

    schema_path = Path(f'data/schemas/{schema_name}.jsonschema')

    if not schema_path.exists():
        schema_path = Path('data/schemas/false.jsonschema')

    return json_load(schema_path)

def validate(json, schema):
    resolver = jsonschema.RefResolver.from_schema(schema_store[schema], store=schema_store)
    validate_json = jsonschema.Draft202012Validator(schema_store[schema], resolver=resolver).validate
    try:
        validate_json(json)
    except jsonschema.ValidationError as e:
        print('Error:', e.message)
        return False
    return True

schema_store = {}
root_path = Path(__file__).parent
schema_store['qmk.module.v1'] = load_jsonschema(root_path / "data/schemas/module.jsonschema")
schema_store['qmk.user_module.v1'] = load_jsonschema(root_path / "data/schemas/user_module.jsonschema")
schema_store['qmk.device_module.v1'] = load_jsonschema(root_path / "data/schemas/device_module.jsonschema")