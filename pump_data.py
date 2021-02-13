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
import dateparser
from datetime import datetime
from binance.client import Client
from binance.websockets import BinanceSocketManager

api_key=""
api_secret=""

client = Client(api_key, api_secret)


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
	
	
def buy(client,symbol,quantity,decimals):
    success= False
    res="{}"
    while not success:
        try:
            print("Trying to buy: "+ str(round_decimals_down(quantity,decimals)))
            res=client.order_market_buy(
            symbol=symbol,
            quantity=round_decimals_down(quantity,decimals))
            success = True
        except:
            success = False
            time.sleep(5)
            traceback.print_exc()
    return float(res["price"])
		
def sell(client,symbol,quantity,decimals):
    success=False
    res="{}"
    while not success:
        try:
            print("Trying to sell: "+str(round_decimals_down(quantity*0.99,decimals)))
            res=client.order_market_sell(
            symbol=symbol,
            quantity=round_decimals_down(quantity*0.99,decimals))
            success = True
        except:
            traceback.print_exc()
            success = False
            time.sleep(5)
    return float(res["price"])   
def get_price(client,symbol):
    try:
        price=0
        count=0
        trades = client.get_recent_trades(symbol=symbol, limit = 1)
        for t in trades:
            price= price + float(t["price"])
            count = count +1
#        avg_price= client.get_avg_price(symbol=symbol)
        avg_price = price / count
    except:
        traceback.print_exc()
        time.sleep(30)
        avg_price=client.get_avg_price(symbol=symbol)
    return float(avg_price)
    
def get_order(client,symbol,limit):
    time.sleep(1)
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
    return float(balance["free"])
    	
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
def get_candle(client,symbol):
    candle = {}
    kline = client.get_historical_klines(symbol=symbol,interval=client.KLINE_INTERVAL_1HOUR,start_str="20 days ago UTC",end_str="now UTC",limit = 500)
    return kline

			
if __name__ == '__main__':
#    asset = input("Insert Symbol")
    asset = "BTC"
    symbol = asset + "USDC"
    info = client.get_symbol_info(symbol)
    print(info["filters"][2])
    price = get_price(client,symbol)
    
    
    balanceUSDT= get_balance(client,"USDC")
    tobuy = (balanceUSDT-2)/price
    round_decimals_down(tobuy,1)
#    buy(client,symbol,tobuy,1)

    all_prices = []
    symbols = []
    all_prices = client.get_all_tickers()
    for p in all_prices:
        if p["symbol"].find(asset) != -1:
           symbols.append(p["symbol"])
#            symbols.append(p["symbol"].lower()+"@depth5@1000ms")
#        elif p["symbol"].find("XRP") != -1:
#            symbols.append(p["symbol"].lower()+"@depth5")
#        elif p["symbol"].find("ETH") != -1:
#            symbols.append(p["symbol"].lower()+"@depth5")
    print( "Numero di coppie con BTC: " + str(len(symbols)))
    print(symbols)
    percentincrease = 5
    price_increase= 2
    for s in symbols:
        count=0
        avg_vol = 0
        kline=get_candle(client,s)
#        candle["Open"] = float(kline[0][1])
#        candle["High"] = float(kline[0][2])
#        candle["Low"] = float(kline[0][3])
#        candle["Close"] = float(kline[0][4])
        volumes = []
        prices = []
        f = open("data/"+s+".csv","a")
        f.write("Timestamp,Date,Open,High,Low,Close,Volume,MA_High,MA_Volume,P_Anomaly,V_Anomaly\n")
        f.close()
        for k in kline:
            vol = float(k[5])
            price = float(k[2])
            date = float(k[0])
            if count < 12:           
                volumes.append(vol)
                prices.append(price)
            else:
                volumes.pop(0)
                volumes.append(vol)
                prices.pop(0)
                prices.append(price)
                
            ma_vol = sum(volumes)/len(volumes)
            ma_price= sum(prices)/len(prices)
            count = count +1
            vol_anomaly=False
            price_anomaly=False
            if vol > ma_vol * percentincrease:
                vol_anomaly= True
            if price > price_increase * ma_price:
                price_anomaly =True
            if price_anomaly and vol_anomaly:
                print("Possibile Pump")
                print("Symbol : " + s)
                print(datetime.fromtimestamp(date/1000))
            f = open("data/"+s+".csv","a")
            f.write(str(k[0])+","+str(datetime.fromtimestamp(date/1000))+","+str(k[1])+","+str(k[2])+","+str(k[3])+","+str(k[4])+","+str(k[5])+","+str(ma_price)+","+str(ma_vol)+","+str(price_anomaly)+","+str(vol_anomaly)+"\n")
            f.close()
#    get_candle(client,symbol)

    input("press enter to sell")
    to_sell = get_balance(client,asset)
#    sell(client,symbol,to_sell,1)
    print("Sold all")
    balance = get_balance(client,asset)
    balanceUSDT= get_balance(client,"USDC")
    print("Balance("+asset+"):")
    print(balance)
    print("Balance (USD)")
    print(balanceUSDT)
