import pytest
import pandas as pd
import os
from main import PolymarketDataPipeline 

def test_data_processing_logic():
    """
    Test that the pipeline correctly transforms raw API data 
    into the expected CSV format.
    """
    pipeline = PolymarketDataPipeline()
    
    # Mock raw data as it would come from the API
    pipeline.all_trades = [
        {
            "timestamp": 1704067200, # Jan 1, 2024
            "title": "Test Market",
            "size": 100.5,
            "price": 0.5,
            "side": "BUY",
            "outcome": "Yes",
            "extra_junk": "should_be_filtered"
        }
    ]
    
    # Run the processing logic
    pipeline.process_and_save()
    
    # Find the generated file (it will have today's date)
    files = [f for f in os.listdir('.') if f.startswith('historical_trades_')]
    assert len(files) > 0
    filename = files[0]
    
    # Load the saved CSV to verify contents
    df = pd.read_csv(filename)
    
    # Verify transformations
    assert "extra_junk" not in df.columns  # Column filtering worked
    assert "timestamp" in df.columns
    assert df["size"].iloc[0] == 100.5
    
    # Cleanup
    os.remove(filename)

print("Test passed successfully!")