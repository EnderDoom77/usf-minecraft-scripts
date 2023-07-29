import yaml

class Price:
    def __init__(self, buy: float, sell: float):
        if abs(buy) < abs(sell):
            buy = sell
        self.buy:float = buy
        self.sell:float = sell
        
    def __add__(self, other: "Price"):
        return Price(self.buy + other.buy, self.sell + other.sell)
    def __mul__(self, num: float):
        return Price(self.buy * num, self.sell * num)

def global_name(s:str):
    return s.lower().replace(' ', '').replace('_', '')

def item_name(s:str):
    return s.upper().replace(' ', '_')

def group_name(group:list[str]):
    return item_name(group[0])

def humanize(s:str):
    result = "&r"
    lastSpace = True
    for c in s:
        if c in [' ', '_']:
            lastSpace = True
            result += ' '
            continue
        
        result += c.upper() if lastSpace else c
        lastSpace = False
    return result

def get_price(gn:str) -> Price:
    result = prices.get(gn, None)
    if result == None:
        alias = config["aliases"].get(gn, "")
        if alias != "":
            result = prices.get(alias, None)
    if result == None:
        print(f"UNKNOWN PRICE: {gn}")
        return Price(0, 100000)
    return result

def get_sell_price(gn:str) -> float:
    result = get_price(gn)
    if result != None:
        return result.sell
    return 0       

def get_buy_price(gn: str) -> float:
    result = get_price(gn)
    if result != None:
        return result.buy
    return 100000

prices: dict[str,Price] = None
def load_prices(file:str = "worth.yml") -> dict[str,Price]:
    global prices
    if config == None:
        raise Exception("You must load configuration before attempting to load other data")
    
    if prices != None:
        return prices
    
    prices = dict()
    with open(file, 'r') as worth:
        sell_prices = yaml.safe_load(worth)["worth"]
        defaultbf = config["prices"]["default_buy_price_factor"]
        for (name, sellp) in sell_prices.items():
            gn = global_name(name)
            buyp = 10000
            if gn in config["prices"]["buy_prices"]:
                buyp = config["prices"]["buy_prices"][gn]
            elif gn in config["prices"]["buy_factors"]:
                buyp = sellp * config["prices"]["buy_factors"][gn]
            else:
                buyp = sellp * defaultbf
            prices[gn] = Price(buyp, sellp)
    return prices
                
def load_prices_from_full(file:str = "full_worth.yml") -> dict[str, Price]:
    global prices
    with open(file, 'r') as fworth:
        prices = yaml.safe_load(fworth)
        prices = {global_name(name): Price(price["buy"], price["sell"]) for name, price in prices.items()}
    return prices
                
config = None
def load_config(file:str = "itemizer_config.yml") -> object:
    global config
    if config != None:
        return config
    
    with open(file) as f:
        data = yaml.safe_load(f)
        config = data
    return config
