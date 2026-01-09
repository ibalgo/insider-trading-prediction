import requests
import json
import time
import pandas as pd
import ast
import random
from py_clob_client.clob_types import TradeParams
from py_clob_client.client import ClobClient
CLOB_API = "https://clob.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
TOKEN_ID = ""
params = {    
    'order': 'startDate',
    'closed' : 'true',
    'ascending' : 'false',
    'limit' : 50,
    'offset': 200,
    'resolved' : 'true'
}

resp = requests.get("https://polymarket.com/api/geoblock")
print(resp.json())
req = requests.get(f"{GAMMA_API}/markets", params = params)
req.raise_for_status()
markets = req.json()
print(len(markets))
trades = []

for market in markets:
    print(market['question'])
    limit = 50
    offset = 0
    while True:
        params = {
            'market' : market['conditionId'],
            'limit' : limit,
            'offset' : offset
        }  
        req = requests.get(f"{DATA_API}/trades", params=params)
        req.raise_for_status()
        chunk = req.json()
        if not chunk:
            break
        trades.extend(chunk)
        offset += len(chunk)
        
        if offset >= 200:
            break
        time.sleep(random.uniform(0.5, 1.5))
    print(offset)
    
df = pd.DataFrame((trades))
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc = True)
df['timestamp'] = df['timestamp'].dt.tz_convert('US/Eastern').dt.strftime('%Y-%m-%d %H:%M:%S')
cols = ['timestamp','title','name','size','price','side','asset','conditionId','proxyWallet','outcome']
df_filtered = df[cols]
output_filename = 'historical_trades.csv'
df_filtered.to_csv(output_filename, index=False)

# events = req.json()
# eventIds = []
# for event in events:
#     eventIds.append(event.get('id'))

# print(eventIds)
# offset = 0
# trades = [] 
# limit = 500
# while (len(trades) < 5000):
#     params2 = {
#         'eventId': eventIds,
#         'limit' : limit,
#         'offset' : offset,
#         'sort_by' : 'time',
#         'ascending' : 'true'
#     }
#     resp = requests.get(f"{DATA_API}/trades", params=params2)
#     resp.raise_for_status()
#     trades_chunk = resp.json()
#     trades.extend(trades_chunk) 
#     if len(trades_chunk) < limit:
        
#         break
#     offset += 500

# df = pd.DataFrame(trades)

# output_filename = 'polymarket_trades.csv'
# df.to_csv(output_filename, index=False)