import yaml
import json
import re

units = {}
def configure_units(new_units: dict[str,str]):
    global units
    units = new_units
    
replace_keys = {}
def set_key(key: str, value: any):
    global replace_keys
    replace_keys[key] = value

def get_key(key: str, default = None):
    return replace_keys.get(key, default)

INTERPOLATION_CHAR = '%'
def stringify(value: dict | list, prefix: str = "", suffix: str = "") -> str:
    if isinstance(value, list):
        return [f"{prefix}{dict_to_nbt(item)}{suffix}" for item in value]
    else:
        return f"{prefix}{dict_to_nbt(value)}{suffix}"
        
stringify_modes = [
    ('Stringify[]', '[', ']'),
    ('Stringify{}', '{', '}'),
    ('Stringify()', '(', ')'),
    ('Stringify', '', '')
]
def preprocess_nbt(data: dict | list, depth: int = 0):
    if isinstance(data, list):
        for item in data:
            preprocess_nbt(item, depth + 1)
        return
    
    if not isinstance(data, dict):
        return
            
    original_keys = list(data.keys())
    for key in original_keys:
        new_val = data[key]
        preprocess_nbt(new_val, depth + 1)
        
        if isinstance(new_val, str):
            if new_val.startswith(INTERPOLATION_CHAR) and new_val.endswith(INTERPOLATION_CHAR):
                saved_key = new_val[1:-1]
                new_val = get_key(saved_key)
                data[key] = new_val
        
        for flag, prefix, suffix in stringify_modes:
            if key.endswith(flag):
                new_key = key[:(-len(flag))]
                data[new_key] = stringify(new_val, prefix, suffix)
                del data[key]
        

def postprocess_nbt(nbt: str) -> str:
    for u, suff in units.items():
        for pattern in [rf'(\\?"{u}\\?":\s?[0-9.]+)', rf"('{u}':\s?[0-9.]+)"]:
            nbt = re.sub(pattern, f"\\1{suff}", nbt)
        for pattern in [rf'(\\?"{u}\\?":\s?)\[([^]{suff}]+)\]', rf"('{u}':\s?)\[([^{suff}]]+)\]"]:
            all_matches = re.findall(pattern, nbt)
            for match in all_matches:
                print(f"Running nbt list reformatter for key {u} -> {match}")
                vals = (val.strip() for val in match[1].split(','))
                repl = ', '.join(f'{val}{suff}' for val in vals)
                nbt = nbt.replace(f"{match[0]}[{match[1]}]", f"{match[0]}[{repl}]")
            
    nbt = re.sub(rf'(\\?"UUID\\?":\s?\[)', f"\\1I; ", nbt)
    nbt = re.sub(rf"('UUID':\s?\[)", f"\\1I; ", nbt)
    return nbt

def dict_to_nbt(data: dict, preprocess = True) -> str:
    print("------------------------------")
    print("Beginning NBT Preprocessing...")
    print("------------------------------")
    if preprocess: 
        preprocess_nbt(data)
    print("====RESULT====")
    nbt = json.dumps(data, sort_keys=True)
    nbt = postprocess_nbt(nbt)
    print(nbt)
    return nbt
    
    