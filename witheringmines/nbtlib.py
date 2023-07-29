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
                data[key] = get_key(saved_key)
        
        if key.endswith('Stringify'):
            new_key = key[:(-len('Stringify'))]
            if isinstance(new_val, list):
                data[new_key] = [f"[{json.dumps(item)}]" for item in new_val]
            else:
                print(f"No list found, using value {new_val}")
                data[new_key] = f"[{json.dumps(new_val)}]"
                
            del data[key]
            print("  " * depth + f"Resulting Stringify -> {data}")

def postprocess_nbt(nbt: str) -> str:
    for u, suff in units.items():
        nbt = re.sub(rf'(\\?"{u}\\?":\s?[0-9.]+)', f"\\1{suff}", nbt)
        nbt = re.sub(rf"('{u}':\s?[0-9.]+)", f"\\1{suff}", nbt)
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
    nbt = json.dumps(data)
    nbt = postprocess_nbt(nbt)
    print(nbt)
    return nbt
    
    