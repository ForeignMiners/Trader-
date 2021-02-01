#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import os
import argparse
#import pandas as pd
#import numpy as np
import json
import time
import math
import traceback
from datetime import datetime
from binance.client import Client
from binance.websockets import BinanceSocketManager

api_key=""
api_secret=""
#dsds
client = Client(api_key, api_secret)

val=0
next_val=0
percent =0
fee=0
count=0
money=0
granularity=0
state='S'
profit=0
variations = []
values = []


def round_decimals_down(number:float, decimals:int=2):
    """
    Returns a value rounded down to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)

    factor = 10 ** decimals
    return math.floor(number * factor) / factor
	
	
def buy(client,symbol,quantity,safe_balance):
    success= False
    res="{}"
    while not success:
        try:
            print("Trying to buy: "+ str(round_decimals_down(quantity-safe_balance,3)))
            res=client.order_market_buy(
            symbol=symbol,
            quantity=round_decimals_down(quantity-safe_balance,3))
            success = True
        except:
            success = False
            time.sleep(5)
            traceback.print_exc()
    return float(res["price"])
		
def sell(client,symbol,quantity,safe_balance):
    success=False
    res="{}"
    while not success:
        try:
            print("Trying to sell: "+str(round_decimals_down(quantity-safe_balance,3)))
            res=client.order_market_sell(
            symbol=symbol,
            quantity=round_decimals_down(quantity-safe_balance,3))
            success = True
        except:
            traceback.print_exc()
            success = False
            time.sleep(5)
    return float(res["price"])   

def process_message(msg):
    print(msg["s"])
    print(msg["b"])
    print(msg["a"])
    # do something

symbols= []
if __name__ == "__main__":
    bm = BinanceSocketManager(client)
    all_prices = client.get_all_tickers()
    for p in all_prices:
        if p["symbol"].find("USDC") != -1 and len(symbols)<10:
           symbols.append(p["symbol"])
#            symbols.append(p["symbol"].lower()+"@depth5@1000ms")
#        elif p["symbol"].find("XRP") != -1:
#            symbols.append(p["symbol"].lower()+"@depth5")
#        elif p["symbol"].find("ETH") != -1:
#            symbols.append(p["symbol"].lower()+"@depth5")

    for s in symbols:
        diff_key = bm.start_depth_socket(s,process_message)

    bm.start()
    while True:
        p =1
