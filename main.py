import requests
import json
from pprint import pprint

# --- Configuration ---
GAMMA_API_URL = "https://gamma-api.polymarket.com"
DATA_API_URL = "https://data-api.polymarket.com"
MARKET_SLUG = "nobel-peace-prize-winner-2025"
TOP_N = 50 # The total number of top holders you want to see
HOLDERS_PER_MARKET_LIMIT = 100 # Fetch the top 100 from each market to ensure the overall top 50 are captured

print(f"Starting to find the overall Top {TOP_N} holders across all outcomes in '{MARKET_SLUG}'...")

# 1. FETCH THE MAIN EVENT DATA TO GET ALL MARKET IDs
event_url = f"{GAMMA_API_URL}/events/slug/{MARKET_SLUG}"
try:
    event_response = requests.get(event_url)
    event_response.raise_for_status()
    event_data = event_response.json()
except requests.exceptions.RequestException as e:
    print(f"ERROR: Could not fetch event data: {e}")
    exit()

markets = event_data.get('markets', [])

if not markets:
    print("Error: No individual markets found within the event.")
    exit()

print(f"Found {len(markets)} individual market outcomes to check.")
all_top_holders = []
def fetch_trades_for_market(condition_id, limit=10, offset=0):
    url = "https://data-api.polymarket.com/trades"
    params = {
        "limit": limit,
        "offset": offset,
        "market": condition_id
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


# 2. ITERATE THROUGH EACH MARKET TO FETCH TOP HOLDERS
for market in markets:
    condition_id = market.get('conditionId')
    market_question = market.get('question')
    trades = fetch_trades_for_market(condition_id, limit=10, offset=0)
    print(f"Fetched {len(trades)} trades for market {condition_id}")
    print()

    for i, trade in enumerate(trades, start=1):
        ts = trade.get("timestamp")
        try:
            dt = datetime.fromtimestamp(ts/1000) if ts > 1e12 else datetime.fromtimestamp(ts)
        except Exception:
            dt = None

        side = trade.get("side")
        outcome = trade.get("outcome")
        price = trade.get("price")
        size = trade.get("size")

        maker = trade.get("maker") or trade.get("proxyWallet")
        taker = trade.get("taker")

        total_cost = None
        if price is not None and size is not None:
            try:
                total_cost = float(price) * float(size)
            except (TypeError, ValueError):
                pass

        print(f"Trade #{i}")
        print(f"  Time: {dt} (raw {ts})")
        print(f"  Side: {side}")
        print(f"  Outcome: {outcome}")
        print(f"  Price: {price}")
        print(f"  Size: {size}")
        if total_cost is not None:
            print(f"  Total Bet Value: {total_cost:.4f} USDC")
        print(f"  Maker Wallet: {maker}")
        print(f"  Taker Wallet: {taker}")
        print(f"  Transaction Hash: {trade.get('transactionHash')}")
        print("-" * 60)
    
    


# 4. SORT THE ENTIRE LIST AND TAKE THE TOP N
if not all_top_holders:
    print("\nNo holder data was successfully retrieved from any market.")
    exit()

# Sort the entire combined list by 'amount_float' (the final payout size) in descending order
final_top_holders = sorted(
    all_top_holders, 
    key=lambda h: h.get('amount_float', 0), 
    reverse=True
)[:TOP_N] # Slice to get only the Top 50

# 5. DISPLAY THE RESULTS
print(f"\n--- Overall Top {TOP_N} Holders Across All Market Outcomes ---")
# Adjust column widths for better readability, especially the 'Market' column
print("{:<5} {:<15} {:<20} {:<30} {:>10}".format("Rank", "Username", "Wallet Prefix", "Market Outcome", "Position $"))
print("-" * 80)

for i, holder in enumerate(final_top_holders):
    # Truncate market question to fit in the column
    market_display = holder['market_question'].replace("Will ", "").replace(" win the Nobel Peace Prize in 2025?", "").strip()
    
    # Get a short prefix of the wallet address
    wallet_prefix = holder.get('proxyWallet', 'N/A')[:10] + "..."
    
    print("{:<5} {:<15} {:<20} {:<30} ${:>9,.2f}".format(
        i + 1, 
        holder['username'][:14], 
        wallet_prefix, 
        market_display[:28], # Truncate market text
        holder['amount_float']
    ))

print("-" * 80)
print(f"Displaying the largest {TOP_N} positions by final payout value (shares * $1.00).")