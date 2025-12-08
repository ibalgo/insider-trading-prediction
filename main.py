import requests
import json
import time
import pandas as pd
from py_clob_client.clob_types import TradeParams
from py_clob_client.client import ClobClient
CLOB_API = "https://clob.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
TOKEN_ID = ""
SLUG = "nobel-peace-prize-winner-2025"
params = {
    'slug': SLUG,
    'closed': 'true',
    'ascending' : 'true'
}
req = requests.get(f"{GAMMA_API}/events", params = params)
req.raise_for_status()
events = req.json()
eventIds = []
for event in events:
    eventIds.append(event.get('id'))

print(eventIds)
offset = 0
trades = [] 
limit = 500
while (len(trades) < 5000):
    params2 = {
        'eventId': eventIds,
        'limit' : limit,
        'offset' : offset,
        'sort_by' : 'time',
        'ascending' : 'true'
    }
    resp = requests.get(f"{DATA_API}/trades", params=params2)
    resp.raise_for_status()
    trades_chunk = resp.json()
    trades.extend(trades_chunk) 
    if len(trades_chunk) < limit:
        
        break
    offset += 500

df = pd.DataFrame(trades)

output_filename = 'polymarket_trades.csv'
df.to_csv(output_filename, index=False)