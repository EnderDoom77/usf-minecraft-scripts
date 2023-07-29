import yaml
import argparse
import nbtlib as nbtlib

parser = argparse.ArgumentParser()

parser.add_argument('-c', '--config', default='config.yml', dest='config', help='configuration file')
parser.add_argument('-o', '--output', default='out/result.txt', dest='output', help="the name of the output file")

args = parser.parse_args()

config_file = args.config
output_file = args.output

with open(config_file, 'r') as f:
    config = yaml.safe_load(f)

result = {}
trades_result = {}

for item, data in config['materials'].items():
    currency = data['currency']
    currency_mat = currency['material']
    nbt = nbtlib.dict_to_nbt(currency['nbt'])
    result[item] = f"{item} -> {currency_mat}{nbt}"
    trades_result[item] = []
    trades = data['trades']
    for t in trades:
        new_trade = {}
        cost = t['cost']
        new_trade['buy'] = {'id': currency_mat, 'Count': cost, 'tag': currency['nbt']}
        new_trade['sell'] = t['sell']
        if 'other' in t:
            new_trade['buyB'] = t['other']
        trades_result[item].append(new_trade)

nbtconfig = config['postprocessing']
nbtlib.configure_units(nbtconfig['units'])

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

with open(output_file, 'w') as f:
    for item, value in result.items():
        f.write(f"{value}\n")
    for v in villagers_result:
        f.write(f"/summon villager {villager_offset_str} {v}\n")