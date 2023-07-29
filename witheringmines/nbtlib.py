import yaml
import json
import re

units = {}
def configure_units(new_units: dict[str,str]):
    global units
    units = new_units

def preprocess_nbt(data: dict | list, depth: int = 0):
    if isinstance(data, list):
        for item in data:
            preprocess_nbt(item, depth + 1)
        return
    
    if not isinstance(data, dict):
        return
            
    original_keys = list(data.keys())
    for key in original_keys:
        print("  " * depth + f"Preprocessing {key}")
        preprocess_nbt(data[key], depth + 1)                    
        
        if key.endswith('Stringify'):
            new_key = key[:(-len('Stringify'))]
            new_val = data[key]
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

def dict_to_nbt(data: dict) -> str:
    print("------------------------------")
    print("Beginning NBT Preprocessing...")
    print("------------------------------")
    preprocess_nbt(data)
    print("====RESULT====")
    nbt = json.dumps(data)
    nbt = postprocess_nbt(nbt)
    print(nbt)
    return nbt
    
    