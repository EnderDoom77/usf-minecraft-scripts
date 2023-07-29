import sys
import json
import yaml
from bzlib import *

if __name__ == "__main__":
    config = load_config()
    prices = load_prices_from_full(sys.argv[1])
            
    formal_names:dict[str,str] = {} # global name to formal name
    categories:dict[str,list[list[str]]] = {} # category name to set of groups
    groups:dict[str,list[str]] = {} # group name to list of formal names
    categories_inv:dict[str,str] = {} # global name to category name
    groups_inv:dict[str,str] = {} # global name to group name
    custom_items:set[str] = set()

    custom_item_data = {}
    with open("created_items.yml", 'r') as f:
        data = yaml.safe_load(f)
        custom_item_data = data
        for (name, itemdata) in data["items"].items():
            custom_items.add(name)

    with open("category_structure.yml", 'r') as categoryFile:
        categories = yaml.safe_load(categoryFile)
        for (cat, content) in categories.items():
            cat = cat.lower()
            for items in content:
                group = group_name(items)
                groups[group] = items
                for i in items:
                    if i in custom_items: # only set group to custom items
                        custom_item_data["items"][i]["group"] = group
                        continue
                    gn = global_name(i)
                    formal_names[gn] = i
                    categories_inv[gn] = cat
                    groups_inv[gn] = group
                    
    items_result = {}
    max_price_factor = config["prices"]["default_max_price_factor"]
    for (gn, fn) in formal_names.items():
        price = get_price(gn)
        sp = price.sell
        bp = price.buy
        items_result[item_name(fn)] = {
            "material": fn.upper(),
            "group": groups_inv[gn],
            "category": categories_inv[gn],
            "data": 0,
            "prices": {
                "buy": bp,
                "sell": sp
            },
            "max_prices": {
                "buy": bp + max_price_factor * (bp - sp),
                "sell": max_price_factor * sp
            },
            "name": humanize(fn),
            "placeable": True,
            "normal": True
        }

    groups_result = {}
    for (group, items) in groups.items():
        if (len(items) < 2): continue
        
        item_list = []
        for (i, name) in enumerate(items):
            slot = config["group_slots"][len(items)][i]
            item = f"{item_name(name)}:{slot}"
            item_list.append(item)
        groups_result[group] = {
            "main_item": item_name(items[0]),
            "item_list": item_list
        }

    current = {}
    with open("categories.yml") as f:
        current = yaml.safe_load(f)

    for (name, itemdata) in custom_item_data["items"].items():
        print(f"Loading custom item data from {name}")
        items_result[name] = itemdata

    with open('out/items.yml', 'w') as out:
        yaml.dump({
            "items": items_result,
            "groups": groups_result
        }, out)
        
    with open('out/categories.yml', 'w') as out:
        for (cat, groups) in categories.items():
            cat_items_result = []
            cat_slots_result = []
            i = 0
            page = 1
            slots = len(config["main_slots"])
            for g in groups:
                rep = f"{group_name(g)}:{page}"
                cat_items_result.append(rep)
                #cat_items_result.append(groupName(g))
                cat_slots_result.append(config["main_slots"][i])
                i += 1
                if i >= slots:
                    page += 1
                    i = 0 
            current[cat]["items"] = cat_items_result
            current[cat]["slots"] = cat_slots_result
            current[cat]["page"] = max(1, page - 1 if i == 0 else page)
        yaml.dump(current, out)
