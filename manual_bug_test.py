#!/usr/bin/env python3
"""
Manual bug condition verification script

This script manually tests the bug condition by:
1. Loading config.json (which is missing api_secret for Alpaca)
2. Initializing AlpacaAdapter with those credentials
3. Attempting to fetch market data
4. Documenting the 401 Unauthorized error (proving bug exists)
"""

import sys
from src.config_manager import ConfigManager
from src.data_sources import AlpacaAdapter
from src.models import DataSource

def main():
    print("=" * 70)
    print("BUG CONDITION EXPLORATION TEST")
    print("=" * 70)
    print()
    
    # Load config
    print("1. Loading config/config.json...")
    config_manager = ConfigManager("config/config.json")
    config_result = config_manager.load_config()
    
    if config_result.is_err():
        print(f"   ERROR: Failed to load config: {config_result.unwrap_err()}")
        return 1
    
    config = config_result.unwrap()
    print("   ✓ Config loaded successfully")
    print()
    
    # Find Alpaca data source
    print("2. Finding Alpaca data source configuration...")
    alpaca_config = None
    for ds_config in config.data_sources:
        if ds_config.source == DataSource.ALPACA:
            alpaca_config = ds_config
            break
    
    if alpaca_config is None:
        print("   ERROR: Alpaca data source not found in config")
        return 1
    
    print(f"   ✓ Found Alpaca data source")
    print(f"     - api_key: {alpaca_config.api_key[:10]}...")
    print(f"     - api_secret: '{alpaca_config.api_secret}' (length: {len(alpaca_config.api_secret)})")
    print()
    
    # Verify bug condition
    print("3. Verifying bug condition...")
    print(f"   - api_key present: {alpaca_config.api_key != ''}")
    print(f"   - api_secret empty: {alpaca_config.api_secret == ''}")
    
    if alpaca_config.api_key != "" and alpaca_config.api_secret == "":
        print("   ✓ BUG CONDITION CONFIRMED: api_key present but api_secret is empty")
    else:
        print("   ✗ Bug condition NOT present (config may already be fixed)")
        return 0
    print()
    
    # Initialize adapter
    print("4. Initializing AlpacaAdapter with config credentials...")
    adapter = AlpacaAdapter(
        api_key=alpaca_config.api_key,
        api_secret=alpaca_config.api_secret
    )
    print("   ✓ Adapter initialized")
    print(f"     - Headers APCA-API-KEY-ID: {adapter.headers['APCA-API-KEY-ID'][:10]}...")
    print(f"     - Headers APCA-API-SECRET-KEY: '{adapter.headers['APCA-API-SECRET-KEY']}'")
    print()
    
    # Attempt to fetch data
    print("5. Attempting to fetch real-time data for AAPL...")
    print("   (This will make an actual API call to Alpaca)")
    result = adapter.fetch_realtime("AAPL")
    print()
    
    # Check result
    print("6. Analyzing result...")
    if result.is_ok():
        print("   ✗ UNEXPECTED: Authentication succeeded!")
        print("   This means the bug may already be fixed or the API accepted empty secret.")
        price_data = result.unwrap()
        print(f"   Received data: {price_data.symbol} @ ${price_data.close}")
        return 0
    else:
        error = result.unwrap_err()
        error_msg = str(error)
        print(f"   ✓ EXPECTED: Authentication failed as expected")
        print(f"   Error: {error_msg}")
        
        if "401" in error_msg or "Unauthorized" in error_msg or "authentication" in error_msg.lower():
            print()
            print("=" * 70)
            print("BUG CONFIRMED!")
            print("=" * 70)
            print()
            print("COUNTEREXAMPLE FOUND:")
            print(f"  - Symbol: AAPL")
            print(f"  - Operation: fetch_realtime()")
            print(f"  - Result: 401 Unauthorized")
            print(f"  - Root Cause: Missing api_secret in Alpaca data source config")
            print()
            print("This proves the bug exists. The test will pass after adding")
            print("api_secret to the Alpaca data source in config/config.json")
            print("=" * 70)
            return 0
        else:
            print(f"   ? Unexpected error type: {error_msg}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
