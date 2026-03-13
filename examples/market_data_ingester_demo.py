"""Demo of Market Data Ingester with failover and retry logic"""
from datetime import datetime, timedelta
from src.market_data_ingester import MarketDataIngester
from src.data_sources import YahooFinanceAdapter, AlpacaAdapter
from src.models import DataSource
from src.config_models import DataSourceConfig


def main():
    """Demonstrate Market Data Ingester failover capabilities"""
    
    # Create data source adapters
    yahoo_adapter = YahooFinanceAdapter()
    alpaca_adapter = AlpacaAdapter(
        api_key="YOUR_ALPACA_KEY",
        api_secret="YOUR_ALPACA_SECRET"
    )
    
    # Configure data sources with priorities
    # Lower priority number = higher priority (tried first)
    configs = [
        DataSourceConfig(
            source=DataSource.YAHOO_FINANCE,
            api_key="",  # Yahoo Finance doesn't require API key for basic usage
            priority=1   # Primary source
        ),
        DataSourceConfig(
            source=DataSource.ALPACA,
            api_key="YOUR_ALPACA_KEY",
            priority=2   # Fallback source
        )
    ]
    
    # Create adapter mapping
    adapters = {
        DataSource.YAHOO_FINANCE: yahoo_adapter,
        DataSource.ALPACA: alpaca_adapter
    }
    
    # Initialize Market Data Ingester
    ingester = MarketDataIngester(adapters, configs)
    
    print("=" * 60)
    print("Market Data Ingester Demo")
    print("=" * 60)
    
    # Example 1: Fetch real-time data
    print("\n1. Fetching real-time data for AAPL...")
    result = ingester.fetch_realtime("AAPL")
    
    if result.is_ok():
        price_data = result.unwrap()
        print(f"   ✓ Success!")
        print(f"   Symbol: {price_data.symbol}")
        print(f"   Source: {price_data.source.value}")
        print(f"   Close: ${price_data.close}")
        print(f"   Volume: {price_data.volume:,}")
        print(f"   Timestamp: {price_data.timestamp}")
    else:
        error = result.unwrap_err()
        print(f"   ✗ Error: {error}")
    
    # Example 2: Fetch historical data
    print("\n2. Fetching historical data for AAPL (last 7 days)...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    result = ingester.fetch_historical("AAPL", start_date, end_date)
    
    if result.is_ok():
        price_data_list = result.unwrap()
        print(f"   ✓ Success!")
        print(f"   Retrieved {len(price_data_list)} data points")
        print(f"   Source: {price_data_list[0].source.value}")
        print(f"   Date range: {price_data_list[0].timestamp.date()} to {price_data_list[-1].timestamp.date()}")
        print(f"   First close: ${price_data_list[0].close}")
        print(f"   Last close: ${price_data_list[-1].close}")
    else:
        error = result.unwrap_err()
        print(f"   ✗ Error: {error}")
    
    print("\n" + "=" * 60)
    print("Failover Features:")
    print("=" * 60)
    print("✓ Automatic failover to alternative sources on failure")
    print("✓ Exponential backoff retry for transient errors")
    print("✓ Priority-based source selection")
    print("✓ Automatic data validation")
    print("✓ Descriptive error messages when all sources fail")
    print("=" * 60)


if __name__ == "__main__":
    main()
