# Data Source Adapters

## Overview

The data source adapters provide a unified interface for fetching market data from multiple providers. This abstraction allows the Calgo system to seamlessly switch between data sources or implement failover strategies.

## Architecture

All data source adapters implement the `DataSourceAdapter` abstract base class, which defines two core methods:

- `fetch_historical(symbol, start_date, end_date)` - Fetch historical price data for a time range
- `fetch_realtime(symbol)` - Fetch current real-time price data

Both methods return a `Result` type that contains either the requested data or a descriptive error.

## Supported Data Sources

### Yahoo Finance

**Class:** `YahooFinanceAdapter`

**Features:**
- Free access (no API key required)
- Historical data with daily granularity
- Real-time quotes during market hours
- Wide coverage of stocks and ETFs

**Usage:**
```python
from src.data_sources import YahooFinanceAdapter
from datetime import datetime, timedelta

adapter = YahooFinanceAdapter()

# Fetch historical data
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
result = adapter.fetch_historical("AAPL", start_date, end_date)

if result.is_ok():
    price_data_list = result.unwrap()
    for data in price_data_list:
        print(f"{data.timestamp}: ${data.close}")
else:
    error = result.unwrap_err()
    print(f"Error: {error}")

# Fetch real-time data
result = adapter.fetch_realtime("AAPL")
if result.is_ok():
    price_data = result.unwrap()
    print(f"Current price: ${price_data.close}")
```

### Alpaca

**Class:** `AlpacaAdapter`

**Features:**
- Requires API credentials (free tier available)
- Historical data with multiple timeframes
- Real-time market data
- Paper trading support
- Professional-grade data quality

**Usage:**
```python
from src.data_sources import AlpacaAdapter
from datetime import datetime, timedelta

adapter = AlpacaAdapter(
    api_key="your_api_key",
    api_secret="your_api_secret"
)

# Fetch historical data
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
result = adapter.fetch_historical("AAPL", start_date, end_date)

if result.is_ok():
    price_data_list = result.unwrap()
    for data in price_data_list:
        print(f"{data.timestamp}: ${data.close}")

# Fetch real-time data
result = adapter.fetch_realtime("AAPL")
if result.is_ok():
    price_data = result.unwrap()
    print(f"Current price: ${price_data.close}")
```

## Data Format

All adapters normalize data into the `PriceData` model:

```python
@dataclass
class PriceData:
    symbol: str           # Stock/ETF ticker symbol
    timestamp: datetime   # Data timestamp
    open: Decimal        # Opening price
    high: Decimal        # High price
    low: Decimal         # Low price
    close: Decimal       # Closing price
    volume: int          # Trading volume
    source: DataSource   # Data source identifier
```

## Error Handling

All methods return a `Result` type that encapsulates success or failure:

```python
result = adapter.fetch_realtime("AAPL")

if result.is_ok():
    # Success case
    price_data = result.unwrap()
    process_data(price_data)
else:
    # Error case
    error = result.unwrap_err()
    log_error(error)
```

Common error scenarios:
- Network timeouts or connection failures
- Invalid symbol or no data available
- API rate limits exceeded
- Authentication failures (Alpaca)
- Malformed API responses

## Extensibility

To add a new data source:

1. Create a new class that inherits from `DataSourceAdapter`
2. Implement `fetch_historical()` and `fetch_realtime()` methods
3. Normalize the provider's data format into `PriceData`
4. Handle provider-specific errors and return descriptive `DataError` messages

Example:

```python
class NewProviderAdapter(DataSourceAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def fetch_historical(self, symbol, start_date, end_date):
        try:
            # Fetch data from provider
            raw_data = self._fetch_from_api(symbol, start_date, end_date)
            
            # Normalize to PriceData format
            price_data_list = self._normalize_data(raw_data)
            
            return Result.ok(price_data_list)
        except Exception as e:
            return Result.err(DataError(f"Error: {e}"))
    
    def fetch_realtime(self, symbol):
        # Similar implementation
        pass
```

## Configuration

Data source adapters are configured through the main configuration file:

```json
{
  "data_sources": [
    {
      "source": "yahoo_finance",
      "priority": 1
    },
    {
      "source": "alpaca",
      "api_key": "your_key",
      "api_secret": "your_secret",
      "priority": 2
    }
  ]
}
```

The `priority` field determines the order for failover attempts (lower number = higher priority).

## Testing

Run the test suite:

```bash
pytest tests/test_data_sources.py -v
```

Run the demo:

```bash
python examples/data_source_demo.py
```

## Market Data Ingester

The `MarketDataIngester` class provides high-level data fetching with automatic failover and retry logic.

**Features:**
- Automatic failover to alternative sources on failure
- Exponential backoff retry for transient errors (network timeouts, rate limits)
- Priority-based source selection
- Automatic data validation
- Comprehensive error reporting

**Usage:**
```python
from src.market_data_ingester import MarketDataIngester
from src.data_sources import YahooFinanceAdapter, AlpacaAdapter
from src.models import DataSource
from src.config_models import DataSourceConfig

# Create adapters
yahoo_adapter = YahooFinanceAdapter()
alpaca_adapter = AlpacaAdapter(api_key="key", api_secret="secret")

# Configure sources with priorities (lower = higher priority)
configs = [
    DataSourceConfig(DataSource.YAHOO_FINANCE, "", priority=1),  # Primary
    DataSourceConfig(DataSource.ALPACA, "key", priority=2)       # Fallback
]

adapters = {
    DataSource.YAHOO_FINANCE: yahoo_adapter,
    DataSource.ALPACA: alpaca_adapter
}

# Create ingester
ingester = MarketDataIngester(adapters, configs)

# Fetch with automatic failover
result = ingester.fetch_realtime("AAPL")
if result.is_ok():
    price_data = result.unwrap()
    print(f"Price: ${price_data.close} from {price_data.source.value}")
else:
    print(f"All sources failed: {result.unwrap_err()}")
```

**Retry Behavior:**
- Transient errors (timeouts, network issues) trigger exponential backoff retry
- Default: 3 attempts with 1s, 2s, 4s delays
- Non-transient errors (invalid symbol, auth failures) fail immediately
- After max retries, fails over to next configured source

**Validation:**
- All fetched data is automatically validated
- Invalid data points are filtered out
- Validation failures trigger failover to alternative sources

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 1.1**: Supports multiple data sources (Yahoo Finance and Alpaca)
- **Requirement 1.2**: Retrieves historical price data for specified symbols and time ranges
- **Requirement 1.3**: Retrieves real-time price data within 5 seconds
- **Requirement 1.4**: Implements automatic failover to alternative sources on failure
- **Requirement 1.5**: Normalizes price data into consistent PriceData format
- **Requirement 1.6**: Validates data completeness and flags invalid data points
