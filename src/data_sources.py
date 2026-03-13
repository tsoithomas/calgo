"""Data source adapters for market data ingestion"""
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
import requests
from src.models import PriceData, DataSource
from src.result import Result


class DataError(Exception):
    """Error during data fetching or processing"""
    pass


class ValidationError(Exception):
    """Error during data validation"""
    pass


def normalize_data(raw_data: Dict[str, Any], source: DataSource, symbol: str) -> Result[PriceData, DataError]:
    """
    Normalize raw API response data into standard PriceData format.
    
    Args:
        raw_data: Raw data dictionary from API response
        source: Data source identifier (YAHOO_FINANCE or ALPACA)
        symbol: Stock/ETF ticker symbol
        
    Returns:
        Result containing normalized PriceData or DataError
    """
    try:
        if source == DataSource.YAHOO_FINANCE:
            # Yahoo Finance format
            price_data = PriceData(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(raw_data.get("timestamp", 0)),
                open=Decimal(str(raw_data.get("open", 0))),
                high=Decimal(str(raw_data.get("high", 0))),
                low=Decimal(str(raw_data.get("low", 0))),
                close=Decimal(str(raw_data.get("close", 0))),
                volume=int(raw_data.get("volume", 0)),
                source=source
            )
        elif source == DataSource.ALPACA:
            # Alpaca format
            timestamp_str = raw_data.get("t", "")
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                timestamp = datetime.now()
            
            price_data = PriceData(
                symbol=symbol,
                timestamp=timestamp,
                open=Decimal(str(raw_data.get("o", 0))),
                high=Decimal(str(raw_data.get("h", 0))),
                low=Decimal(str(raw_data.get("l", 0))),
                close=Decimal(str(raw_data.get("c", 0))),
                volume=int(raw_data.get("v", 0)),
                source=source
            )
        else:
            return Result.err(DataError(f"Unsupported data source: {source}"))
        
        return Result.ok(price_data)
        
    except (ValueError, TypeError, KeyError) as e:
        return Result.err(DataError(f"Failed to normalize data from {source}: {str(e)}"))


def validate_data(data: PriceData) -> Result[PriceData, ValidationError]:
    """
    Validate price data for completeness and correctness.
    
    Checks for:
    - Missing timestamp
    - Negative prices (open, high, low, close)
    - Invalid price relationships (high < low, etc.)
    - Missing or negative volume
    
    Args:
        data: PriceData object to validate
        
    Returns:
        Result containing validated PriceData or ValidationError
    """
    errors = []
    
    # Check for missing timestamp
    if data.timestamp is None:
        errors.append("Missing timestamp")
    
    # Check for negative prices
    if data.open < 0:
        errors.append(f"Negative open price: {data.open}")
    if data.high < 0:
        errors.append(f"Negative high price: {data.high}")
    if data.low < 0:
        errors.append(f"Negative low price: {data.low}")
    if data.close < 0:
        errors.append(f"Negative close price: {data.close}")
    
    # Check for invalid price relationships
    if data.high < data.low:
        errors.append(f"High price ({data.high}) is less than low price ({data.low})")
    if data.open < data.low or data.open > data.high:
        errors.append(f"Open price ({data.open}) is outside high-low range")
    if data.close < data.low or data.close > data.high:
        errors.append(f"Close price ({data.close}) is outside high-low range")
    
    # Check for negative volume
    if data.volume < 0:
        errors.append(f"Negative volume: {data.volume}")
    
    # Check for missing symbol
    if not data.symbol or data.symbol.strip() == "":
        errors.append("Missing or empty symbol")
    
    if errors:
        error_msg = f"Data validation failed for {data.symbol}: {'; '.join(errors)}"
        return Result.err(ValidationError(error_msg))
    
    return Result.ok(data)


class DataSourceAdapter(ABC):
    """Abstract interface for data source adapters"""
    
    @abstractmethod
    def fetch_historical(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Result[List[PriceData], DataError]:
        """
        Fetch historical price data for a symbol and time range.
        
        Args:
            symbol: Stock/ETF ticker symbol
            start_date: Start of time range
            end_date: End of time range
            
        Returns:
            Result containing list of PriceData or DataError
        """
        pass
    
    @abstractmethod
    def fetch_realtime(self, symbol: str) -> Result[PriceData, DataError]:
        """
        Fetch current real-time price data for a symbol.
        
        Args:
            symbol: Stock/ETF ticker symbol
            
        Returns:
            Result containing PriceData or DataError
        """
        pass


class YahooFinanceAdapter(DataSourceAdapter):
    """Yahoo Finance data source adapter"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Yahoo Finance adapter.
        
        Args:
            api_key: Optional API key (Yahoo Finance free tier doesn't require one)
        """
        self.api_key = api_key
        self.base_url = "https://query1.finance.yahoo.com/v8/finance"
    
    def fetch_historical(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Result[List[PriceData], DataError]:
        """
        Fetch historical price data from Yahoo Finance.
        
        Args:
            symbol: Stock/ETF ticker symbol
            start_date: Start of time range
            end_date: End of time range
            
        Returns:
            Result containing list of PriceData or DataError
        """
        try:
            # Convert datetime to Unix timestamp
            period1 = int(start_date.timestamp())
            period2 = int(end_date.timestamp())
            
            url = f"{self.base_url}/chart/{symbol}"
            params = {
                "period1": period1,
                "period2": period2,
                "interval": "1d",
                "includePrePost": "false"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse Yahoo Finance response
            if "chart" not in data or "result" not in data["chart"]:
                return Result.err(DataError("Invalid response format from Yahoo Finance"))
            
            results = data["chart"]["result"]
            if not results or len(results) == 0:
                return Result.err(DataError(f"No data found for symbol {symbol}"))
            
            result = results[0]
            timestamps = result.get("timestamp", [])
            quotes = result.get("indicators", {}).get("quote", [{}])[0]
            
            if not timestamps:
                return Result.err(DataError(f"No price data available for {symbol}"))
            
            # Build PriceData list
            price_data_list = []
            for i, ts in enumerate(timestamps):
                try:
                    price_data = PriceData(
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(ts),
                        open=Decimal(str(quotes["open"][i])),
                        high=Decimal(str(quotes["high"][i])),
                        low=Decimal(str(quotes["low"][i])),
                        close=Decimal(str(quotes["close"][i])),
                        volume=int(quotes["volume"][i]),
                        source=DataSource.YAHOO_FINANCE
                    )
                    price_data_list.append(price_data)
                except (KeyError, IndexError, ValueError, TypeError) as e:
                    # Skip invalid data points
                    continue
            
            if not price_data_list:
                return Result.err(DataError(f"Failed to parse price data for {symbol}"))
            
            return Result.ok(price_data_list)
            
        except requests.exceptions.RequestException as e:
            return Result.err(DataError(f"Network error fetching data from Yahoo Finance: {str(e)}"))
        except Exception as e:
            return Result.err(DataError(f"Unexpected error fetching Yahoo Finance data: {str(e)}"))
    
    def fetch_realtime(self, symbol: str) -> Result[PriceData, DataError]:
        """
        Fetch real-time price data from Yahoo Finance.
        
        Args:
            symbol: Stock/ETF ticker symbol
            
        Returns:
            Result containing PriceData or DataError
        """
        try:
            url = f"{self.base_url}/quote"
            params = {"symbols": symbol}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse Yahoo Finance quote response
            if "quoteResponse" not in data or "result" not in data["quoteResponse"]:
                return Result.err(DataError("Invalid response format from Yahoo Finance"))
            
            results = data["quoteResponse"]["result"]
            if not results or len(results) == 0:
                return Result.err(DataError(f"No data found for symbol {symbol}"))
            
            quote = results[0]
            
            # Extract price data
            try:
                price_data = PriceData(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    open=Decimal(str(quote.get("regularMarketOpen", quote.get("previousClose", 0)))),
                    high=Decimal(str(quote.get("regularMarketDayHigh", quote.get("regularMarketPrice", 0)))),
                    low=Decimal(str(quote.get("regularMarketDayLow", quote.get("regularMarketPrice", 0)))),
                    close=Decimal(str(quote.get("regularMarketPrice", 0))),
                    volume=int(quote.get("regularMarketVolume", 0)),
                    source=DataSource.YAHOO_FINANCE
                )
                return Result.ok(price_data)
            except (KeyError, ValueError, TypeError) as e:
                return Result.err(DataError(f"Failed to parse quote data for {symbol}: {str(e)}"))
            
        except requests.exceptions.RequestException as e:
            return Result.err(DataError(f"Network error fetching real-time data from Yahoo Finance: {str(e)}"))
        except Exception as e:
            return Result.err(DataError(f"Unexpected error fetching Yahoo Finance real-time data: {str(e)}"))


class AlpacaAdapter(DataSourceAdapter):
    """Alpaca data source adapter"""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://data.alpaca.markets"):
        """
        Initialize Alpaca adapter.
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            base_url: Alpaca API base URL (defaults to production data API)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret
        }
    
    def fetch_historical(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Result[List[PriceData], DataError]:
        """
        Fetch historical price data from Alpaca.
        
        Args:
            symbol: Stock/ETF ticker symbol
            start_date: Start of time range
            end_date: End of time range
            
        Returns:
            Result containing list of PriceData or DataError
        """
        try:
            url = f"{self.base_url}/v2/stocks/{symbol}/bars"
            params = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "timeframe": "1Day",
                "limit": 10000
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse Alpaca response
            if "bars" not in data:
                return Result.err(DataError("Invalid response format from Alpaca"))
            
            bars = data["bars"]
            if not bars:
                return Result.err(DataError(f"No data found for symbol {symbol}"))
            
            # Build PriceData list
            price_data_list = []
            for bar in bars:
                try:
                    price_data = PriceData(
                        symbol=symbol,
                        timestamp=datetime.fromisoformat(bar["t"].replace("Z", "+00:00")),
                        open=Decimal(str(bar["o"])),
                        high=Decimal(str(bar["h"])),
                        low=Decimal(str(bar["l"])),
                        close=Decimal(str(bar["c"])),
                        volume=int(bar["v"]),
                        source=DataSource.ALPACA
                    )
                    price_data_list.append(price_data)
                except (KeyError, ValueError, TypeError) as e:
                    # Skip invalid data points
                    continue
            
            if not price_data_list:
                return Result.err(DataError(f"Failed to parse price data for {symbol}"))
            
            return Result.ok(price_data_list)
            
        except requests.exceptions.RequestException as e:
            return Result.err(DataError(f"Network error fetching data from Alpaca: {str(e)}"))
        except Exception as e:
            return Result.err(DataError(f"Unexpected error fetching Alpaca data: {str(e)}"))
    
    def fetch_realtime(self, symbol: str) -> Result[PriceData, DataError]:
        """
        Fetch real-time price data from Alpaca.
        
        Args:
            symbol: Stock/ETF ticker symbol
            
        Returns:
            Result containing PriceData or DataError
        """
        try:
            url = f"{self.base_url}/v2/stocks/{symbol}/bars/latest"
            
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse Alpaca latest bar response
            if "bar" not in data:
                return Result.err(DataError("Invalid response format from Alpaca"))
            
            bar = data["bar"]
            
            # Extract price data
            try:
                price_data = PriceData(
                    symbol=symbol,
                    timestamp=datetime.fromisoformat(bar["t"].replace("Z", "+00:00")),
                    open=Decimal(str(bar["o"])),
                    high=Decimal(str(bar["h"])),
                    low=Decimal(str(bar["l"])),
                    close=Decimal(str(bar["c"])),
                    volume=int(bar["v"]),
                    source=DataSource.ALPACA
                )
                return Result.ok(price_data)
            except (KeyError, ValueError, TypeError) as e:
                return Result.err(DataError(f"Failed to parse latest bar data for {symbol}: {str(e)}"))
            
        except requests.exceptions.RequestException as e:
            return Result.err(DataError(f"Network error fetching real-time data from Alpaca: {str(e)}"))
        except Exception as e:
            return Result.err(DataError(f"Unexpected error fetching Alpaca real-time data: {str(e)}"))
