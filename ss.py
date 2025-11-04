import requests
import json
import pandas as pd
import time
from datetime import datetime

# 1. Define Parameters
BASE_URL = "https://data-api.polymarket.com/trades"
MARKET_SLUG = "nobel-peace-prize-winner-2025"
START_TIMESTAMP = 1719888000 # July 1, 2025
END_TIMESTAMP = 1728556800   # Oct 10, 2025 (Announcement day)

# 2. Construct the Payload/Query Parameters
params = {
    'market_slug': MARKET_SLUG,
    'start_time': START_TIMESTAMP,
    'end_time': END_TIMESTAMP,
    'type': 'TRADE',  # Only pull trade (buy/sell) events, not funding or other noise
    'limit': 100,     # Start with 100, we'll need to use pagination later for the full set
    'sort_by': 'timestamp',
    'direction': 'asc'
}
MARKET_CONDITION_ID = "0x33d54cba21c85c98282d0819a380cc5031cbeec65570e6a58558237ba8f05f61"
# 3. Plan the GET Request
LIMIT = 500
MAX_REQUESTS = 100
all_activities = []

print(f"Starting data collection for market: {MARKET_SLUG}")

for i in range(MAX_REQUESTS):
    offset = i * LIMIT
    # print(f"Requesting batch {i+1} (offset: {offset})...") # Comment out for cleaner output
    
    # 1. Define the Query Parameters
    params = {
        'market': MARKET_CONDITION_ID, # CRITICAL: The correct parameter name
        'start': START_TIMESTAMP,
        'end': END_TIMESTAMP,
        'limit': LIMIT,
        'offset': offset,
        'sortDirection': 'ASC' 
    }

    try:
        # 2. Execute the Request
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status() # Catches 400 or 404 errors
        data = response.json()
        
        # 3. Extract Activities (Trades)
        # Assuming trade data is directly in the list or under a key like 'trades'
        activities = data.get('trades', data) if isinstance(data, dict) else data

        if not activities:
            print("Received empty list. Pagination complete.") # Comment out for cleaner output
            break
        
        all_activities.extend(activities)
        print(f"Successfully retrieved {len(activities)} trades. Total trades so far: {len(all_activities)}") # Comment out for cleaner output
        time.sleep(0.5) 
        
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during trade request: {e}")
        break

if all_activities:
    df = pd.DataFrame(all_activities)
    print("\nDataFrame created successfully!")
    print(f"Total rows (trades) in DataFrame: {len(df)}")
    
    # Cleaning Step 1: Convert Unix Timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    
    # Cleaning Step 2: Select/Rename Columns
    essential_cols = ['timestamp', 'maker', 'taker', 'side', 'usdcSize', 'price', 'outcomeIndex', 'conditionId']
    
    # Filter columns
    df_cleaned = df[[col for col in essential_cols if col in df.columns]]
    
    print("\nSample of Cleaned Data:")
    print(df_cleaned.head())
    
    # Final Action: Save to a CSV
    df_cleaned.to_csv(f'{MARKET_SLUG}_trades.csv', index=False)
    print(f"\nData successfully saved to {MARKET_SLUG}_trades.csv")
else:
    print("Failed to retrieve any activities.")