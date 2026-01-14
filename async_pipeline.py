import asyncio
import aiohttp
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
# Create a master logger
logger = logging.getLogger("PolymarketIngestor")
logger.setLevel(logging.DEBUG)  # Capture everything at the source

# Create a "Console Handler" 
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO) 
console_format = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_format)

# Create a "File Handler" 
file_handler = logging.FileHandler('pipeline_debug.log')
file_handler.setLevel(logging.DEBUG)  
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)

# Add both handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
class PolymarketDataPipeline:
    """
    An asynchronous pipeline to ingest and normalize trade data from Polymarket.
    Demonstrates: Async I/O, Error Handling with Backoff, and Modular Design.
    """
    
    GAMMA_API = "https://gamma-api.polymarket.com"
    DATA_API = "https://data-api.polymarket.com"

    def __init__(self, markets_limit: int = 100, trades_per_market: int = 500):
        self.markets_limit = markets_limit
        self.trades_per_market = trades_per_market
        self.all_trades: List[Dict[str, Any]] = []

    async def fetch_json(self, session: aiohttp.ClientSession, url: str, params: Dict, retries: int = 3) -> Optional[List]:
        """Fetch helper with Exponential Backoff for resilience."""
        for i in range(retries):
            try:
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status == 429:  # Rate limited
                        wait_time = (i + 1) * 2
                        logger.warning(f"Rate limited (429). Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                logger.error(f"Attempt {i+1} failed for {url}: {e}")
                if i == retries - 1:
                    return None
        return None

    async def get_trades_for_market(self, session: aiohttp.ClientSession, market: Dict):
        """Asynchronously fetches trades for a specific market condition."""
        condition_id = market.get('conditionId')
        question = market.get('question', 'Unknown')
        
        offset = 0
        limit = 50
        market_trades = []

        while offset < self.trades_per_market:
            params = {
                'market': condition_id,
                'limit': limit,
                'offset': offset
            }
            chunk = await self.fetch_json(session, f"{self.DATA_API}/trades", params)
            
            if not chunk:
                break
            
            market_trades.extend(chunk)
            offset += len(chunk)
            
            if len(chunk) < limit:
                break
        
        logger.info(f"Successfully ingested {len(market_trades)} trades for: {question[:50]}")
        return market_trades

    async def run_pipeline(self):
        """Main execution entry point using an async context."""
        async with aiohttp.ClientSession() as session:
            # Fetch Markets
            market_params = {
                'order': 'startDate',
                'closed': 'true',
                'ascending': 'false',
                'limit': self.markets_limit,
                'offset': 0,
                'resolved': 'true',
                'active': 'false',
                'volume_num_min': 10000
            }
            
            logger.info("Fetching markets...")
            markets = await self.fetch_json(session, f"{self.GAMMA_API}/markets", market_params)
            
            if not markets:
                logger.error("Failed to retrieve markets. Exiting.")
                return

            # Concurrency - Fetch all trades at once using gather
            logger.info(f"Starting concurrent trade ingestion for {len(markets)} markets...")
            tasks = [self.get_trades_for_market(session, m) for m in markets]
            results = await asyncio.gather(*tasks)

            # Flatten list of lists
            self.all_trades = [trade for market_list in results for trade in market_list]
            self.process_and_save()

    def process_and_save(self):
        """Normalization and Persistence Layer."""
        if not self.all_trades:
            logger.warning("No data found to save.")
            return

        df = pd.DataFrame(self.all_trades)
        
        # Data Transformation
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
        df['timestamp'] = df['timestamp'].dt.tz_convert('US/Eastern').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        cols = ['timestamp', 'title', 'name', 'size', 'price', 'side', 'asset', 'conditionId', 'proxyWallet', 'outcome']
        existing_cols = [c for c in cols if c in df.columns]
        
        output_file = f"historical_trades_{datetime.now().strftime('%Y%m%d')}.csv"
        df[existing_cols].to_csv(output_file, index=False)
        logger.info(f"Pipeline complete. {len(df)} records saved to {output_file}.")

if __name__ == "__main__":
    pipeline = PolymarketDataPipeline(markets_limit=200, trades_per_market=10000)
    asyncio.run(pipeline.run_pipeline())