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
def get_price(client,symbol):
    try:
        avg_price= client.get_avg_price(symbol=symbol)
    except:
        traceback.print_exc()
        time.sleep(30)
        avg_price=client.get_avg_price(symbol=symbol)
    return float(avg_price["price"])
def get_order(client,symbol,limit):
    order = client.get_all_orders(symbol=symbol,limit=limit)
    price = float(order[0]['cummulativeQuoteQty'])/float(order[0]['executedQty'])
    return price
#WEBSOCKETS NOT USED FOR NOW	
#def process_message(msg):
#    print("message type: {}".format(msg['e']))
#    print(msg)
#    # do something
	
def check_order_status(client,symbol,orderId):

    order = client.get_order(
    symbol=symbol,
    orderId=orderId)
    print(order)
    return order["status"]
	
def get_fee(client,symbol):
    fee = 0
    try:
	
        fee= client.get_trade_fee(symbol=symbol)
    except:
	    print("Error in getting the fee for :" + symbol)
    return fee
def get_balance(client,asset):
    try:
        balance = client.get_asset_balance(asset=asset)
    except:
        traceback.print_exc()
        time.sleep(30)
        balance = client.get_asset_balance(asset=asset)
    return balance
	
def print_status(state,avg_price,decimals):
    money = get_balance(client,asset)
    usdc = get_balance (client,stable)
    #fee = get_fee(client,symbol)
    print("Balance "+asset+": "+str(money["free"]))
    print("Balance USDT: "+str(usdc["free"]))
    #print("Fee Eth USDC : "+str(fee))
	
    ret =0
    if state=="B":
        ret= round_decimals_down(float(money["free"]),decimals)
    if state =="S":
        if decimals==0:
            ret = math.floor(float(usdc["free"])/avg_price)
        else:
            ret = round_decimals_down(float(usdc["free"])/avg_price,decimals)
    return ret
	
def wait_for_order(client,orderId):
    orderStatus = check_order_status(client,symbol,orderId)
    while orderStatus!="FILLED":
        orderStatus = check_order_status(client,symbol,orderId)
        time.sleep(1)
		
def deep_checking(variation,old_price,state,client,symbol,decimals):
    avg_price = get_price(client,symbol)   
    new_variation = avg_price/old_price-1
    new_variation = new_variation * 100
    max_variation = new_variation
    min_variation = new_variation
    if state=='B':
        while new_variation > max_variation-0.4 and new_variation <0.07:
            print("###############DEEP CHECKING##################")
            avg_price = get_price(client,symbol)
            variation=new_variation
            time.sleep(900)
            new_variation = avg_price/old_price-1
            new_variation = new_variation * 100	
            if max_variation <new_variation:
                max_variation = new_variation			
            quantity= print_status(state,avg_price,decimals)
            print("Avarage Price: ")
            print(avg_price)
            print("Max Variation:")
            print(max_variation)
            print("Variation(%) :")
            print(new_variation)
            print("Last step Variation:")
            print(variation)
    
    if state=='S':
        while new_variation < min_variation+0.4 and new_variation >0.07:
            print("###############DEEP CHECKING##################")
            avg_price = get_price(client,symbol)
            variation=new_variation 
            time.sleep(900)
            new_variation = avg_price/old_price-1
            new_variation = new_variation * 100
            if min_variation>new_variation:
                min_variation = new_variation
            quantity= print_status(state,avg_price,decimals)
            print("Avarage Price: ")
            print(avg_price)
            print("Max Variation:")
            print(min_variation)
            print("Variation(%) :")
            print(new_variation)
            print("Last step Variation:")
            print(variation)
			
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help="data file path",
                        type=str)
    parser.add_argument('--percent', help="percent variation indicating the sell/buy action",
                        type=float, default=0.005)
    parser.add_argument('--fee',help="fee for buy and sell",
                        type=float, default=0.001)
    parser.add_argument('--money', help="input initial money",
                        type=float,default=1000.0)
    parser.add_argument('--granularity',help="input the timer value to check the percentage (minutes)",
                        type=int,default=1)
    parser.add_argument('--date',help="input the starting date format dd/mm/YYYY",
                        type=str)
    parser.add_argument('--buyprice',help="input the buy price",
                        type=float)
    args = parser.parse_args()
    date = args.date
    #ts = time.mktime(datetime.strptime(date, "%d/%m/%Y").timetuple())
    money=args.money
    percent=args.percent
    fee=args.fee
    granularity=args.granularity
    buyprice=args.buyprice
    variation =0
    index=0
    index2=0
    asset= "ETH"
    stable='USDT'
    symbol = asset+stable
    percent =  0.7
    decimals = 2
    exclude = 1
    excludeS = 1
    state = "B"  # State of last action S =sell B=buy
#	state_variation= "N" # State of the variation N = condition not met (variation > or < than percent) += increasing -= decreasing
    avg_price = get_price(client,symbol)
#Code to start a websocket	
#    bm = BinanceSocketManager(client, user_timeout=60)
#    bm.start_aggtrade_socket('BNBETH', process_message)
#    bm.start()
    quantity=print_status(state,avg_price,decimals)
    while(True):
        avg_price = get_price(client,symbol)
        if index ==0 :
            old_price=  get_order(client,symbol,1)
            variation = avg_price/old_price-1
            variation = variation * 100
            crypto=get_balance(client,asset)
            usdcoin= get_balance(client,stable)
            if float(crypto["free"]) *avg_price > float(usdcoin["free"]) :
                state = "B"
            else:
                state="S"
        else:
            variation = avg_price/old_price-1
            variation = variation * 100
        if state=='S' and avg_price > old_price:
            old_price=avg_price
        print("#################################")
        quantity= print_status(state,avg_price,decimals)
        print("Variation(%) :")
        print(variation)
        print("InitPrice :")
        print(old_price)
        print("AvgPrice :")
        print(avg_price)
        print("Minutes from "+ state +" : "+str(index2))
        if state =="S":
            print("Quantity to buy ("+symbol+")")
            print(quantity)
        if state =="B":
            print("Quantity to sell ("+symbol+")")
            print(quantity)

        print("#################################")

        if (variation < -percent and state =="S") :
            print("BUYING STATE")
            deep_checking(variation,old_price,state,client,symbol,decimals)
            quantity= print_status(state,avg_price,decimals)
            price = get_price(client,symbol)
            remove = exclude/price
            buy(client,symbol,quantity,remove)
            state = "B"
            old_price=get_order(client,symbol,1)
            index2=0
        if ( variation > percent and state=="B"):
            print("SELLING STATE")
            deep_checking(variation,old_price,state,client,symbol,decimals)
            price = get_price(client,symbol)
            removeS = excludeS/price
            quantity= print_status(state,avg_price,decimals)
            sell(client,symbol,quantity,removeS)
            state = "S"
            old_price=get_order(client,symbol,1)
            index2=0

        if ( variation < -3 and state=="B"):
            print("SAFE SELLING STATE")
            deep_checking(variation,old_price,state,client,symbol,decimals)
            quantity= print_status(state,avg_price,decimals)
            price = get_price(client,symbol)
            removeS = excludeS/price
            sell(client,symbol,quantity,removeS)
            state = "S"
            time.sleep(10)
            old_price=get_order(client,symbol,1)
            index2=0
        time.sleep(14400)
        index = 1
        index2= index2+1
