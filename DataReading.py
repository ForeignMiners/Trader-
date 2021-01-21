import pandas as pd 

df=pd.read_csv("coinbaseUSD_1-min_data_2014-12-01_to_2019-01-09.csv")

print(df)

df['el']=df.Open.isnull()


df2=df[df['el']==True]
df.drop(df2.index,inplace=True)


df=df[df['Timestamp']>1536609432]

#df['WPmean']=df['Weighted_Price'].rolling(2)
#df['Open']
#df['Cmean']=df['Close'].rolling(2)

#df['percdif']=((df.Close / df.Open ) -1)*100

df['percdif']=((df.Close.rolling(2) ) -1)*100

print(df)

##result['aaaa']=result.Groups_y.isnull()

##print(result)

##df2=result[result['aaaa']==False]
##print("to BE dropped")
##print(df2)

##result.drop(df2.index,inplace=True)
