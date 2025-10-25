import requests
from datetime import datetime

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

def main():
    condition_id = "0x200369a7fc4dad910665c5a77e1c0c0d16237f79c637928bf0c5112cac2db708"
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

if __name__ == "__main__":
    main()
