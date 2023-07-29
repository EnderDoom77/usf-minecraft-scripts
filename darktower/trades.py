import argparse
from typing_extensions import override
import yaml
import termcolor
import time
import re

parser = argparse.ArgumentParser()

parser.add_argument('-c', '--config', dest='config', default='trades.yml',
                    help='The path to the file with all worth equations')
parser.add_argument('-o', '--out', dest='out', default='out/commands.txt',
                    help="The path to the output file created from these values")
parser.add_argument('-w', '--worth', dest='worth', default='worth.yml',
                    help="The path to the file containing all default worth values")
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                    help="Whether to print a detailed report of the resolution process")

args = parser.parse_args()

data = {}
with open(args.config) as f:
    data = yaml.safe_load(f)
    
config = data["config"]
villagers = data["villagers"]
recipes = data["recipes"]
essence_info = data["essence"]
damage_map: dict[str, int] = {}

class Recipe:
    def __init__(self, enchantment: str, costs: list[str]):
        self.enchantment = enchantment
        self.costs = []
        for rawcost in costs:
            cnt, item = tuple(rawcost.split())
            cnt = int(cnt)
            self.costs.append((cnt, item))
            
    def get_trades(self, config: dict) -> list[str]:
        result = []
        buyA = r"{id:book, Count:1}"
        lvl = 1
        if config['mode'] == "essence":
            for (cnt, item) in self.costs:
                # CREATE THE ESSENCE TRADES FIRST
                pass
        
        for (cnt, item) in self.costs:
            if config['mode'] == "essence":
                # TO BE COMPLETED, BOOK + ESSENCE = ENCHANTED BOOK
                continue
            sell = f"{{id:enchanted_book,Count:1,tag:{{StoredEnchantments:[{{id:\"minecraft:{self.enchantment}\",lvl:{lvl}}}]}}}}"
            buyB = f"{{id:{item},Count:{cnt}}}"
            result.append(f"{{maxUses:{config['max_uses']},rewardExp:{config['reward_exp']}b,priceMultiplier:0,buy:{buyA},buyB:{buyB},sell:{sell}}}")
            lvl += 1
            if config['mode'] == "progressive":
                buyA = sell
            
        return result
    
class BaseEssenceRecipe(Recipe):
    def __init__(self, cost: str):
        cntstr, material = cost.split()
        self.cnt = int(cntstr)
        self.item = material
    
    @override
    def get_trades(self, config: dict) -> list[str]:
        # TO DO
        pass
            
parsed_recipes: dict[str,Recipe] = {}
for ench_name, ench_costs in recipes.items():
    parsed_recipes[ench_name] = Recipe(ench_name, ench_costs)

if config["mode"] == "essence":
    # Create base essence trade
    parsed_recipes["base"] = BaseEssenceRecipe()

resulting_cmds = []
for villager in villagers:
    position = tuple(float(x) for x in villager["position"])
    rotation = float(villager["rotation"])
    offers = []
    for trade in villager["trades"]:
        offers.extend(parsed_recipes[trade].get_trades(config))
    cmd_base = f"/summon villager {' '.join(f'{x:.1f}' for x in position)}"
    nbt = {prop:"1b" for prop in config['properties']}
    nbt["VillagerData"] = f"{{type:{config['villager_type']},profession:{config['villager_profession']},level:{config['villager_level']}}}"
    nbt["Offers"] = f"{{Recipes:[{','.join(offers)}]}}"
    nbt["Rotation"] = f"[{rotation:.1f}f]"
    new_cmd = f"{cmd_base} {{{','.join(f'{tag}:{val}' for tag,val in nbt.items())}}}"
    resulting_cmds.append(new_cmd)
    print(termcolor.colored(new_cmd, "blue"))
    print()
    
with open(args.out, 'w') as f:
    f.writelines(resulting_cmds)


"""
/summon minecraft:villager ~ ~ ~ {VillagerData:{type:swamp,profession:cleric,level:5},Offers:{Recipes:[{maxUses:-1,rewardExp:0b,priceMultiplier:0,buy:{id:book,Count:1},buyB:{id:diamond,Count:8},sell:{id:enchanted_book,Count:1,tag:{StoredEnchantments:[{id:mending,lvl:1}]}}},{maxUses:-1,priceMultiplier:0,buy:{id:book,Count:1},buyB:{id:iron_ingot,Count:3},sell:{id:enchanted_book,Count:1,tag:{StoredEnchantments:[{id:unbreaking,lvl:1}]}}},{buy:{id:enchanted_book,Count:1,tag:{StoredEnchantments:[{id:unbreaking,lvl:1}]}},sell:{id:enchanted_book,Count:1,tag:{StoredEnchantments:[{id:unbreaking,lvl:2}]}}}]},Invulnerable:1b,NoAI:1b,PersistenceRequired:1b,Silent:1b,Rotation:[1f]}
"""