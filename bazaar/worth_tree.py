import argparse
import yaml
import termcolor
import time  
import re        

from bzlib import Price, load_config, load_prices, global_name

parser = argparse.ArgumentParser()

parser.add_argument('-f', '--file', dest='file', default='worth_equations.txt',
                    help='The path to the file with all worth equations')
parser.add_argument('-o', '--out', dest='out', default='out/worth_result.yml',
                    help="The path to the output worth file created from these values")
parser.add_argument('-w', '--worth', dest='worth', default='worth.yml',
                    help="The path to the file containing all default worth values")
parser.add_argument('-c', '--config', dest='config', default='itemizer_config.yml',
                    help="The path to a file containing global itemizer configuration parameters")
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                    help="Whether to print a detailed report of the resolution process")
parser.add_argument('-bw', '--base-worth', dest="base_worth", default=None,
                    help="The path to the file where all base prices should be stored for reference or alteration")

args = parser.parse_args()

def timestamp():
    return time.strftime("%T")
def info(str: str):
    print(termcolor.colored(f"[INFO] {timestamp()} | {str}", 'cyan'))
def warn(str: str):
    print(termcolor.colored(f"[WARN] {timestamp()} | {str}", 'yellow'))
def error(str: str):
    print(termcolor.colored(f"[ERROR] {timestamp()} | {str}", "red"))
def msg(str: str, color: str = None, color_bg: str = None):
    print(termcolor.colored(f"\t{str}", color, color_bg))

VERBOSE = args.verbose
if VERBOSE: info("Loading prices...")
load_config(args.config)
default_prices = load_prices(args.worth)
if VERBOSE: info("Finished loading prices.")

class PricedItem:
    def __init__(self, name:str, default_price: Price | None = None, equation: str | None = None, use_default_price_as_min: bool = False):
        self.name = name
        self.price = default_price
        self.resolved = (equation == None)
        self.equation = equation
        self.used_base_price = True
        self.queried = False
        self.use_default_price_as_min = use_default_price_as_min
        
    def get_price(self, price_directory: dict[str, "PricedItem"], flag_as_queried=True) -> Price:
        if not self.resolved:
            self._resolve(price_directory)
        if flag_as_queried:
            self.queried = True
        return self.price       
        
    def _resolve(self, price_directory: dict[str, "PricedItem"]):
        if not self.equation:
            error(f"Unable to parse the price for {self.name}, no default price or equation was found.")
            self.price = Price(0, 0)
            return
        self.used_base_price = self.use_default_price_as_min
        minimizers = self.equation.split("?")
        chosen_price = Price(float('+inf'), float('+inf'))
        if self.use_default_price_as_min:
            if not self.price:
                error(f"Unable to parse the price for {self.name}, no default price was given when equation is self-relative (?=).")
                self.price = Price(0, 0)
                return
            chosen_price = self.price
        for equation in minimizers:
            temp_price = Price(0, 0)
            components = equation.split('+')
            for c in components:
                # Raw prices
                if '|' in c:
                    buy, sell = tuple(float(n) for n in c.split('|'))
                    temp_price += Price(buy, sell)
                    continue
                
                subelems = c.split()
                if len(subelems) == 1: subelems = ["1", subelems[0]]
                quant, item = tuple(subelems)
                if '/' in quant:
                    a, b = tuple(float(n) for n in quant.split('/'))
                    quant = a / b
                else:
                    quant = float(quant)
                
                item_price = price_directory.get(global_name(item), None)
                if item_price == None:
                    error(f"Unable to parse the price for {item}, no default price or equation was found while attempting to calculate value for item {self.name}")
                    continue
                
                try:
                    temp_price += item_price.get_price(price_directory) * quant
                except(RecursionError):
                    error(f"Unable to find pricing for item {item}, recursion limit exceeded while attempting to parse the value for item {self.name}. Ensure your price graph has no loops.")
                    continue
            if temp_price.sell < chosen_price.sell:
                chosen_price = temp_price
        self.price = chosen_price                
        self.resolved = True

def compile_item(raw: dict[str, list[str]], temp: dict[str, list[str]], item: str) -> list[str]:
    start_index = item.find('{')
    end_index = item.find('}')
    if (start_index < 0) != (end_index < 0):
        raise ValueError(f"Invalid set formatting in \"{raw}\", unbalanced braces")
    if start_index < 0:
        return [item]
    
    values = []
    set_name = item[(start_index+1):end_index]
    compile_set(raw, temp, set_name)
    for replacement in temp[set_name]:
        compiled = compile_item(raw, temp, item.replace("{" + set_name + "}", replacement))
        values.extend(compiled)
    return values

def compile_set(raw: dict[str, list[str]], temp: dict[str, list[str]], set_name: str):
    if set_name in temp:
        return
    val = raw.get(set_name, [])
    if val == []:
        error(f"Unable to find set named {set_name}, valid set names are {raw.keys()}")
    set_result = list()
    for item in val:
        to_add = compile_item(raw, temp, item.strip())
        set_result.extend(to_add)
    temp[set_name] = set_result
    if VERBOSE:
        msg(f'compiled set {set_name}, with {len(set_result)} final items', 'green')     

if VERBOSE: info("Processing equations file.")

def process_aliases_word(str: str, aliases: list[tuple[re.Pattern, str]]):
    for regex, repl in aliases:
        str = re.sub(regex, repl, str)
    return str
def process_aliases(str: str, aliases: list[tuple[re.Pattern, str]]):
    return " ".join(process_aliases_word(word, aliases) for word in str.split())

sets: dict[str, list[str]] = dict()
definitions: dict[str, str] = dict()
aliases: list[tuple[re.Pattern, str]] = []
equations: list[str] = []
with open(args.file, 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith("#") or line == "":
            continue
        
        try:
            if line.startswith("DEFINE"):
                key, value = tuple(s.strip() for s in line[7:].split('='))
                definitions[key] = value
            elif line.startswith("SET"):
                key, value = tuple(s.strip() for s in line[4:].split("="))
                value = [s.strip() for s in value.split(',')]
                sets[key] = value
            elif line.startswith("ALIAS"):
                key, value = tuple(s.strip() for s in line[6:].split())
                key = re.compile(f"^{key}$")
                new_tuple = (key, value.replace('$', '\\'))
                aliases.append(new_tuple)
                if VERBOSE: info(f"New alias registered -> {new_tuple}")
            else:
                equations.append(line)
        except ValueError:
            error(f"Improper syntax found when parsing the following line:\n{line}")
    
resulting_items: dict[str, PricedItem] = {}
set_compilation: dict[str, list[str]] = {}
            
if VERBOSE: info("Addressing definitions...")
for key, value in definitions.items():
    gname = global_name(key)
    resulting_items[gname] = PricedItem(key, None, value)
        
if VERBOSE: info("Instantiating items...")
for eq in equations:
    subeqs = compile_item(sets, set_compilation, eq)
    for subeq in subeqs:
        subeq = process_aliases(subeq, aliases)
        try:
            item_name, expr = tuple(s.strip() for s in subeq.split("="))
            use_default = False            
            if item_name.endswith('?'):
                item_name = item_name[:-1].rstrip()
                use_default = True
                if VERBOSE:
                    info(f"Addressing partial definition on item {item_name}, using (sub)equation {subeq}")
            gname = global_name(item_name)
            price = default_prices.get(gname, None)
            if price == None:
                warn(f"No default price for item {item_name}")
            resulting_items[gname] = PricedItem(item_name, price, expr, use_default)
        except ValueError:
            error(f"Unable to parse the following (sub)equation: {subeq}")

if VERBOSE: info("Instantiating default worth values...")
for key, price in default_prices.items():
    gname = global_name(key)
    if gname in resulting_items: continue
    resulting_items[gname] = PricedItem(key, price)
    
if VERBOSE: info("Processing price tree...")
final_prices: dict[str, Price] = {}
for item in resulting_items.values():
    final_prices[item.name] = item.get_price(resulting_items, False)
    
    
root_items: set[str] = {item.name for item in resulting_items.values() if item.used_base_price and item.queried and item.name not in definitions}
if root_items:
    pad_length = max(len(name) for name in root_items) + len("\t: ")
    if VERBOSE:
        info("Printing root items...")
        for ritem in sorted(root_items):
            price = final_prices[ritem]
            print(f"\t{ritem}: ".ljust(pad_length) + termcolor.colored(f"BUY {price.buy:.2f}", "green") + "\t<>\t" + termcolor.colored(f"SELL {price.sell:.2f}", "red"))

unaffected_items: set[str] = {item.name for item in resulting_items.values() if not item.equation and item.name not in definitions}.difference(root_items)
if unaffected_items:
    pad_length = max(len(name) for name in unaffected_items) + len(": ")
    if VERBOSE:
        info("Printing unaffected items...")
        for uitem in sorted(unaffected_items):
            price = final_prices[uitem]
            print(f"\t{uitem}:".ljust(pad_length) + termcolor.colored(f"BUY {price.buy:.2f}", "green") + "\t<>\t" + termcolor.colored(f"SELL {price.sell:.2f}", "red"))
      
with open(args.out, 'w') as f:
    yaml.safe_dump({'worth': {global_name(name): item.sell for name, item in final_prices.items() if name not in definitions.keys()}}, f)
with open(f"out/full_prices.yml", 'w') as f:
    yaml.safe_dump({global_name(name): {"buy": price.buy, "sell": price.sell} for name, price in final_prices.items() if name not in definitions.keys()}, f)
if args.base_worth:
    with open(args.base_worth, 'w') as f:
        base_prices = {ritem: final_prices[ritem] for ritem in root_items.union(unaffected_items)}
        for name, price in sorted(base_prices.items()):
            f.write(f'{name} = {price.buy:.3f}|{price.sell:.3f}\n')