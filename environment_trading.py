#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import os
import argparse
import pandas as pd
import numpy as np
import json
import time
import math
import traceback
from datetime import datetime
from binance.client import Client
from binance.websockets import BinanceSocketManager

api_key="Inisert api key"
api_secret="Insert secret"

client=0

val=0
next_val=0
percent =0
fee=0
count=0
money=0
granularity=0
state='S'
real=False
stable_coin=1000
crypto_coin=0
last_order_price=0
asset =""
stable=""
# dataframe_index=0

date = "01/05/2018"
ts = time.mktime(datetime.strptime(date, "%d/%m/%Y").timetuple())
 
df = pd.read_csv("bitstampUSD_1-min_data_2012-01-01_to_2020-04-22.csv")
df['AA'] = df['Weighted_Price'].isnull()
df1=df[df['AA']==True]
df.drop(df1.index,inplace=True)
df.drop('AA',axis=1,inplace=True)
df=df[df['Timestamp']>ts]
df.reset_index(drop=True,inplace=True)


df1=df[df['Weighted_Price']==0]
df.drop(df1.index,inplace=True)
df=df[df['Timestamp']>ts]
df.reset_index(drop=True,inplace=True)

print(df)

def toggle_real():
    if real:
        real = False
        print( "You are now using historical data")
    else:
        real= True
        print("You are now trading on Binance")
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
	
	
def buy(client,symbol,quantity,safe_balance,stable,avg_price):
    if real:
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
    else:
        last_order_price=avg_price
        return ((stable/avg_price)*(1-0.001)) #0.1 is the fee
	
def sell(client,symbol,quantity,safe_balance,crypto,avg_price):
    if real:
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
    else:
        last_order_price=avg_price
        return (crypto*avg_price)*(1-0.001) #0.1 is the fee
	
def get_price(client,symbol,dataframe_index):
    if real:
        try:
            avg_price= client.get_avg_price(symbol=symbol)
        except:
            traceback.print_exc()
            time.sleep(30)
            avg_price=client.get_avg_price(symbol=symbol)
        return float(avg_price["price"])
    else:
        total=0
        if dataframe_index==0:
            print(df.loc[dataframe_index,"Weighted_Price"])
            total=df.loc[dataframe_index,"Weighted_Price"]	

        elif dataframe_index >=5:
            for i in range(0,4):
	    	
                total = total + df.loc[dataframe_index-i,"Weighted_Price"]
            total/5
        else:
            for i in range(0,dataframe_index):
	    	
                total = total + float(df.loc[dataframe_index-i,"Weighted_Price"])
                total = total/dataframe_index
            
        return total
	
def get_order(client,symbol,limit):
    if real:
        order = client.get_all_orders(symbol=symbol,limit=limit)
        price = float(order[0]['cummulativeQuoteQty'])/float(order[0]['executedQty'])
        return price
    else:
        return last_order_price
#NOT USED FOR NOW
# def check_order_status(client,symbol,orderId):

    # order = client.get_order(
    # symbol=symbol,
    # orderId=orderId)
    # print(order)
    # return order["status"]
	
def wait_time (s,data_index):
    if real:
	
        time.sleep(s)
    else:
        data_index+=s #In fake scenario s is minutes
        return data_index
def get_balance(client,asset):
    if real:
        try:
            balance = client.get_asset_balance(asset=asset)
        except:
            traceback.print_exc()
            time.sleep(30)
            balance = client.get_asset_balance(asset=asset)
        return balance["free"]
    else:
        if asset!="USDT":
            return crypto_coin
        else:
            return stable_coin
		
def get_total_balance(client,asset,stable,price):
    crypt=get_balance(client,asset)
    stabl=get_balance(client,"USDT")
    print("BALACNCE $$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    print(crypt)
    print(stabl)
    balance = (crypt * price)+ stabl
    return balance
 
def print_status(state,avg_price,decimals):
    money = get_balance(client,asset)
    usdc = get_balance (client,stable)
    ret =0
    if real:
        print("Balance "+asset+": "+str(money["free"]))
        print("Balance USDT: "+str(usdc["free"]))
 	
        if state=="B":
            ret= round_decimals_down(float(money["free"]),decimals)
        if state =="S":
            if decimals==0:
                ret = math.floor(float(usdc["free"])/avg_price)
            else:
                ret = round_decimals_down(float(usdc["free"])/avg_price,decimals)
    else:
        if state =="B":
            ret=money
        else:
            ret=usdc/avg_price
    return ret

#NOT USED FOR NOW	
# def wait_for_order(client,orderId):
    # orderStatus = check_order_status(client,symbol,orderId)
    # while orderStatus!="FILLED":
        # orderStatus = check_order_status(client,symbol,orderId)
        # time.sleep(1)
		
def deep_checking(variation,old_price,state,client,symbol,decimals,deep_percent,t,df_ind):
    avg_price = get_price(client,symbol,df_ind)   
    new_variation = avg_price/old_price-1
    new_variation = new_variation * 100
    max_variation = new_variation
    min_variation = new_variation
    if state=='B':
        while new_variation > max_variation-deep_percent:
            #print("###############DEEP SELLING CHECKING##################")
            avg_price = get_price(client,symbol,df_ind)
            variation=new_variation
            df_ind=wait_time(t/2,df_ind)
            new_variation = (avg_price/old_price)-1
            new_variation = new_variation * 100	
            if max_variation <new_variation:
                max_variation = new_variation			
            quantity= print_status(state,avg_price,decimals)
            # print("MONEY")
            # print(money)
            # print("Avarage Price: ")
            # print(avg_price)
            # print("Max Variation:")
            # print(max_variation)
            # print("Variation(%) :")
            # print(new_variation)
            # print("Last step Variation:")
            # print(variation)
    
    if state=='S':
        while new_variation < min_variation+deep_percent:
#            print("###############DEEP BUYING CHECKING##################")
            avg_price = get_price(client,symbol,df_ind)
            variation=new_variation 
            df_ind=wait_time(t/2,df_ind)
            new_variation = avg_price/old_price-1
            new_variation = new_variation * 100
            if min_variation>new_variation:
                min_variation = new_variation
            quantity= print_status(state,avg_price,decimals)
            # print("MONEY")
            # print(money)
            # print("Avarage Price: ")
            # print(avg_price)
            # print("Max Variation:")
            # print(min_variation)
            # print("Variation(%) :")
            # print(new_variation)
            # print("Last step Variation:")
            # print(variation)
    return avg_price, df_ind
	
# def run_environment(prcnt,ast,stbl,t,dataframe_index):
if __name__ == '__main__':
    variation =0
    index=0
    asset= "BTC"
    stable="USDT"
    symbol = asset+stable
    percent =  0.9
    deep_percent = percent/3
    t=240
    dataframe_index=0
    decimals = 2
    exclude = 3
    excludeS = 4
    state = "S"  # State of last action S =sell B=buy
    avg_price = get_price(client,symbol,dataframe_index)
    quantity=print_status(state,avg_price,decimals)
    money=stable_coin
    while(True):
        avg_price = get_price(client,symbol,dataframe_index)
        if index ==0 :
            old_price=  avg_price
            last_order_price=avg_price
            variation = (avg_price/old_price)-1
            variation = variation * 100
            crypto=get_balance(client,asset)
            usdcoin= get_balance(client,stable)
            if float(crypto) *avg_price > float(usdcoin) :
                state = "B"
            else:
                state="S"
        else:
            variation = (avg_price/old_price)-1
            variation = variation * 100
        if state=='S' and avg_price > old_price:
            old_price=avg_price
        #print("#################################")
        quantity= print_status(state,avg_price,decimals)
        # print("MONEY")
        # print(money)
        # print("Variation(%) :")
        # print(variation)
        # print("InitPrice :")
        # print(old_price)
        # print("AvgPrice :")
        # print(avg_price)
        #if state =="S":
            #print("Quantity to buy ("+symbol+")")
            #print(quantity)
        #if state =="B":
            #print("Quantity to sell ("+symbol+")")
            #print(quantity)

        #print("#################################")

        if (variation < -percent and state =="S") :
            #print("BUYING STATE")
            price ,dataframe_index= deep_checking(variation,old_price,state,client,symbol,decimals,deep_percent,t,dataframe_index)
            quantity= print_status(state,avg_price,decimals)
            remove = exclude/price
            crypto_coin=buy(client,symbol,quantity,remove,stable_coin,price)
            stable_coin=remove
            state = "B"

            old_price=price
            #print("OLD PRICE")
            #print(old_price)
            index2=0
            money= get_total_balance(client,asset,stable,price)
            timestamp = df.loc[dataframe_index,'Timestamp']
            dt_object = datetime.fromtimestamp(timestamp)
            print("DATA: ", dt_object)
            print("MONEY: ")
            print(money)

            #print("MONEY")            
            #print(money)
            # return money
			
        if ( variation > percent and state=="B"):
            #print("SELLING STATE")
            price,dataframe_index = deep_checking(variation,old_price,state,client,symbol,decimals,deep_percent,t,dataframe_index)
            removeS = excludeS/price
            quantity= print_status(state,avg_price,decimals)
            stable_coin=sell(client,symbol,quantity,removeS,crypto_coin,price)
            crypto_coin=removeS
            state = "S"

            old_price=price
            #print("OLD PRICE")
            #print(old_price)
            index2=0
            money= get_total_balance(client,asset,stable,price)
            timestamp = df.loc[dataframe_index,'Timestamp']
            dt_object = datetime.fromtimestamp(timestamp)
            print("DATA: ", dt_object)
            print("MONEY: ")
            print(money)

            #print("MONEY")
            #print(money)
			# return money

        if ( variation < -3 and state=="B"):
            print("SAFE SELLING STATE")
            price,dataframe_index = deep_checking(variation,old_price,state,client,symbol,decimals,deep_percent,t,dataframe_index)
            quantity= print_status(state,avg_price,decimals)
            removeS = excludeS/price
            stable_coin=sell(client,symbol,quantity,removeS,crypto_coin,price)
            crypto_coin=removeS
            state = "S"
            old_price=price
            #print("OLD PRICE")
            #print(old_price)
            index2=0
            money= get_total_balance(client,asset,stable,price)
            #print("MONEY")
            #print(money)
            timestamp = df.loc[dataframe_index,'Timestamp']
            dt_object = datetime.fromtimestamp(timestamp)
            print("DATA: ", dt_object)
            print("MONEY: ")
            print(money)

            # return money, dataframe_index
        dataframe_index=wait_time(t,dataframe_index)
        index = 1



    # dfindx=0
    # while True:
        # money,dfindx = run_environment(0.7,"ETH","USDT",6,dfindx)
        # print("Action performed after "+str(dfindx+1)+" minutes, money: "+str(money))
