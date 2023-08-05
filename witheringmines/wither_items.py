import json
import yaml
import argparse
import sys

sys.path.append(sys.path[0] + '/..')
import nbtlib as nbtlib

parser = argparse.ArgumentParser()

parser.add_argument('-c', '--config', default='config.yml', dest='config', help='configuration file')
parser.add_argument('-o', '--output', default='out/result.txt', dest='output', help="the name of the output file")

args = parser.parse_args()

config_file = args.config
output_file = args.output

with open(config_file, 'r') as f:
    config = yaml.safe_load(f)

nbtconfig = config['postprocessing']
nbtlib.configure_units(nbtconfig['units'])
result = {}
trades_result = {}

for item, data in config['materials'].items():
    currency = data['currency']
    currency_mat = currency['material']
    nbt = currency['nbt']
    nbtlib.preprocess_nbt(nbt)
    nbtlib.set_key(item, nbt)
    nbt_str = nbtlib.dict_to_nbt(nbt, preprocess=False)
    result[item] = f"{item} -> {currency_mat}{nbt_str}"
    trades_result[item] = []
    trades = data['trades']
    for t in trades:
        new_trade = {}
        cost = t['cost']
        new_trade['buy'] = {'id': currency_mat, 'Count': cost, 'tag': nbt}
        new_trade['sell'] = t['sell']
        if 'other' in t:
            new_trade['buyB'] = t['other']
        trades_result[item].append(new_trade)

villagers = config['villagers']
static_trade_nbt = villagers['trades']
villager_offset = villagers['offset']
villager_offset_str = ' '.join(f'~{x}' for x in villager_offset)
for tlist in trades_result.values():
    for t in tlist:
        for k,v in static_trade_nbt.items():
            t[k] = v

villagers_result = []
for tlist in trades_result.values():
    new_villager = {'Offers': {'Recipes': tlist}}
    for k,v in villagers['nbt'].items():
        new_villager[k] = v
    villagers_result.append(nbtlib.dict_to_nbt(new_villager))
    
loot_tables = config['loot_tables']
for name, loot_table in loot_tables.items():
    nbtlib.preprocess_nbt(loot_table)
    with open(f'out/loot_tables/{name}.json', 'w') as f:
        json.dump(loot_table, f, indent=2)

enemy_data = config['enemies']
enemy_config = enemy_data['config']
enemy_summon_offset = enemy_config['offset']
enemy_summon_offset_str = ' '.join(f'~{x}' for x in enemy_summon_offset)
enemy_types = enemy_data['enemy_types']
default_enemy_nbt = enemy_config['enemy_defaults']

for enemy_name, enemy in enemy_types.items():
    nbtlib.preprocess_nbt(enemy)
    for k,v in default_enemy_nbt.items():
        enemy[k] = v
    nbtlib.set_key(enemy_name, enemy)
    
spawner_nbts = []
default_spawner_nbt = enemy_data['spawner_defaults']
for spawner in enemy_data['spawners']:
    for k,v in default_spawner_nbt.items():
        spawner[k] = v
    spawner_nbt = nbtlib.dict_to_nbt(spawner)
    spawner_nbts.append(spawner_nbt)

with open(output_file, 'w') as f:
    for item, value in result.items():
        f.write(f"{value}\n")
    for v in villagers_result:
        f.write(f"/summon villager {villager_offset_str} {v}\n")
    for s in spawner_nbts:
        f.write(f"/setblock {enemy_summon_offset_str} minecraft:spawner{s}\n")