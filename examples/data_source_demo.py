"""Demo script showing how to use data source adapters"""
from datetime import datetime, timedelta
from src.data_sources import YahooFinanceAdapter, AlpacaAdapter


def demo_yahoo_finance():
    """Demonstrate Yahoo Finance adapter usage"""
    print("=" * 60)
    print("Yahoo Finance Adapter Demo")
    print("=" * 60)
    
    # Initialize adapter
    adapter = YahooFinanceAdapter()
    
    # Fetch historical data
    print("\n1. Fetching historical data for AAPL...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    result = adapter.fetch_historical("AAPL", start_date, end_date)
    
    if result.is_ok():
        price_data_list = result.unwrap()
        print(f"   ✓ Successfully fetched {len(price_data_list)} data points")
        if price_data_list:
            latest = price_data_list[-1]
            print(f"   Latest: {latest.symbol} @ ${latest.close} on {latest.timestamp.date()}")
    else:
        error = result.unwrap_err()
        print(f"   ✗ Error: {error}")
    
    # Fetch real-time data
    print("\n2. Fetching real-time data for AAPL...")
    result = adapter.fetch_realtime("AAPL")
    
    if result.is_ok():
        price_data = result.unwrap()
        print(f"   ✓ Current price: ${price_data.close}")
        print(f"   Open: ${price_data.open}, High: ${price_data.high}, Low: ${price_data.low}")
        print(f"   Volume: {price_data.volume:,}")
    else:
        error = result.unwrap_err()
        print(f"   ✗ Error: {error}")


def demo_alpaca():
    """Demonstrate Alpaca adapter usage"""
    print("\n" + "=" * 60)
    print("Alpaca Adapter Demo")
    print("=" * 60)
    print("\nNote: Requires valid Alpaca API credentials")
    print("Set ALPACA_API_KEY and ALPACA_API_SECRET environment variables")
    
    # This is just a demonstration of the interface
    # In production, load credentials from config
    try:
        import os
        api_key = os.environ.get("ALPACA_API_KEY", "demo_key")
        api_secret = os.environ.get("ALPACA_API_SECRET", "demo_secret")
        
        adapter = AlpacaAdapter(api_key=api_key, api_secret=api_secret)
        
        print("\n✓ Alpaca adapter initialized")
        print(f"  Base URL: {adapter.base_url}")
        print("\nTo test with real data:")
        print("  1. Sign up for Alpaca account at https://alpaca.markets")
        print("  2. Get your API credentials")
        print("  3. Set environment variables and run this demo")
        
    except Exception as e:
        print(f"\n✗ Error initializing Alpaca adapter: {e}")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("Data Source Adapters Demo")
    print("=" * 60)
    print("\nThis demo shows how to use the Yahoo Finance and Alpaca adapters")
    print("to fetch historical and real-time market data.\n")
    
    # Demo Yahoo Finance (works without credentials)
    demo_yahoo_finance()
    
    # Demo Alpaca (requires credentials)
    demo_alpaca()
    
    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
