import yaml
from sys import argv
import re
import bzlib as bz
import uuid

if __name__ == '__main__':
    config = bz.load_config()
    prices = bz.load_prices()
    
    filename = re.split(r'[/\\]', argv[1])[-1]
    
    with open(argv[1], 'r') as f:
        state = yaml.safe_load(f)
        buy_orders: dict[str,list[object]] = dict()
        sell_offers: dict[str,list[object]] = dict()
        
        for id, pdata in state['players'].items():
            for order_id, order in pdata.get('buy_orders', {}).items():
                if not order["item"] in buy_orders:
                    buy_orders[order["item"]] = []
                buy_orders[order["item"]].append(order)
            for offer_id, offer in pdata.get('sell_offers', {}).items():
                if not offer["item"] in sell_offers:
                    sell_offers[offer["item"]] = []
                sell_offers[offer["item"]].append(offer)
                
        for item, orders in buy_orders.items():
            if item not in state["items"]:
                state["items"][item] = {"buy_price": bz.get_buy_price(bz.global_name(item))}
            orders.sort(key=lambda o: o["price"], reverse=True)
            #state["items"][item]["buy_price"] = orders[0]["price"]
            top_level = None
            state["items"][item]["buy_prices"] = dict()
            while orders != []:
                if top_level == None:
                    tlo = orders.pop(0)
                    top_level = {
                        "price": tlo["price"],
                        "item_amount": tlo["amount"] - tlo["filled"],
                        "order_amount": 1
                    }
                    continue
                if orders[0]["price"] == top_level["price"]:
                    tlo = orders.pop(0)
                    top_level["item_amount"] += tlo["amount"] - tlo["filled"]
                    top_level["order_amount"] += 1
                    continue
                state["items"][item]["buy_prices"][str(uuid.uuid4())] = top_level
                top_level = None
            if top_level != None:
                state["items"][item]["buy_prices"][str(uuid.uuid4())] = top_level
        for item, offers in sell_offers.items():
            if item not in state["items"]:
                state["items"][item] = {"sell_price": bz.get_sell_price(bz.global_name(item))}
            offers.sort(key=lambda o: o["price"], reverse=False)
            #state["items"][item]["sell_price"] = offers[0]["price"]
            top_level = None
            state["items"][item]["sell_prices"] = dict()
            while offers != []:
                if top_level == None:
                    tlo = offers.pop(0)
                    top_level = {
                        "price": tlo["price"],
                        "item_amount": tlo["amount"] - tlo["filled"],
                        "offer_amount": 1
                    }
                    continue
                if offers[0]["price"] == top_level["price"]:
                    tlo = offers.pop(0)
                    top_level["item_amount"] += tlo["amount"] - tlo["filled"]
                    top_level["offer_amount"] += 1
                    continue
                state["items"][item]["sell_prices"][str(uuid.uuid4())] = top_level
                top_level = None
            if top_level != None:
                state["items"][item]["sell_prices"][str(uuid.uuid4())] = top_level
    
    with open(f"out/{filename}", 'w') as f:
        yaml.dump(state, f)