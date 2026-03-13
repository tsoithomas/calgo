"""Market Data Ingester with failover and retry logic"""
import time
from datetime import datetime
from typing import List, Dict
from src.data_sources import DataSourceAdapter, DataError, validate_data
from src.models import PriceData, DataSource
from src.config_models import DataSourceConfig
from src.result import Result


class MarketDataIngester:
    """
    Market Data Ingester with automatic failover and retry logic.
    
    Implements:
    - Primary source with fallback to alternatives based on priority
    - Exponential backoff retry for transient errors
    - Comprehensive error reporting
    """
    
    def __init__(self, adapters: Dict[DataSource, DataSourceAdapter], configs: List[DataSourceConfig]):
        """
        Initialize Market Data Ingester.
        
        Args:
            adapters: Dictionary mapping DataSource to adapter instances
            configs: List of data source configurations with priorities
        """
        self.adapters = adapters
        # Sort configs by priority (lower number = higher priority)
        self.configs = sorted(configs, key=lambda c: c.priority)
        
        # Retry configuration
        self.max_retries = 3
        self.initial_backoff_seconds = 1
        self.backoff_multiplier = 2
    
    def fetch_historical(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Result[List[PriceData], DataError]:
        """
        Fetch historical price data with failover and retry logic.
        
        Tries primary source first, then falls back to alternatives on failure.
        Implements exponential backoff for transient errors.
        
        Args:
            symbol: Stock/ETF ticker symbol
            start_date: Start of time range
            end_date: End of time range
            
        Returns:
            Result containing list of validated PriceData or DataError
        """
        errors = []
        
        for config in self.configs:
            adapter = self.adapters.get(config.source)
            if adapter is None:
                errors.append(f"{config.source.value}: Adapter not available")
                continue
            
            # Try fetching with exponential backoff retry
            result = self._fetch_with_retry(
                lambda: adapter.fetch_historical(symbol, start_date, end_date),
                config.source
            )
            
            if result.is_ok():
                # Validate all data points
                price_data_list = result.unwrap()
                validated_list = []
                validation_errors = []
                
                for price_data in price_data_list:
                    validation_result = validate_data(price_data)
                    if validation_result.is_ok():
                        validated_list.append(validation_result.unwrap())
                    else:
                        validation_errors.append(str(validation_result.unwrap_err()))
                
                if validated_list:
                    return Result.ok(validated_list)
                else:
                    errors.append(f"{config.source.value}: All data points failed validation: {'; '.join(validation_errors)}")
            else:
                error = result.unwrap_err()
                errors.append(f"{config.source.value}: {str(error)}")
        
        # All sources failed
        error_msg = f"Failed to fetch historical data for {symbol} from all sources. Errors: {'; '.join(errors)}"
        return Result.err(DataError(error_msg))
    
    def fetch_realtime(self, symbol: str) -> Result[PriceData, DataError]:
        """
        Fetch real-time price data with failover and retry logic.
        
        Tries primary source first, then falls back to alternatives on failure.
        Implements exponential backoff for transient errors.
        
        Args:
            symbol: Stock/ETF ticker symbol
            
        Returns:
            Result containing validated PriceData or DataError
        """
        errors = []
        
        for config in self.configs:
            adapter = self.adapters.get(config.source)
            if adapter is None:
                errors.append(f"{config.source.value}: Adapter not available")
                continue
            
            # Try fetching with exponential backoff retry
            result = self._fetch_with_retry(
                lambda: adapter.fetch_realtime(symbol),
                config.source
            )
            
            if result.is_ok():
                # Validate the data
                price_data = result.unwrap()
                validation_result = validate_data(price_data)
                
                if validation_result.is_ok():
                    return validation_result
                else:
                    error = validation_result.unwrap_err()
                    errors.append(f"{config.source.value}: Validation failed: {str(error)}")
            else:
                error = result.unwrap_err()
                errors.append(f"{config.source.value}: {str(error)}")
        
        # All sources failed
        error_msg = f"Failed to fetch real-time data for {symbol} from all sources. Errors: {'; '.join(errors)}"
        return Result.err(DataError(error_msg))
    
    def _fetch_with_retry(self, fetch_func, source: DataSource) -> Result:
        """
        Execute fetch function with exponential backoff retry.
        
        Retries on transient errors (network timeouts, rate limits).
        
        Args:
            fetch_func: Function to execute (returns Result)
            source: Data source being accessed
            
        Returns:
            Result from fetch function after retries
        """
        last_error = None
        backoff_seconds = self.initial_backoff_seconds
        
        for attempt in range(self.max_retries):
            result = fetch_func()
            
            if result.is_ok():
                return result
            
            # Check if error is transient
            error = result.unwrap_err()
            last_error = error
            error_msg = str(error).lower()
            
            is_transient = any(keyword in error_msg for keyword in [
                'timeout', 'network', 'connection', 'rate limit', 
                'temporarily unavailable', 'service unavailable'
            ])
            
            if not is_transient:
                # Non-transient error, don't retry
                return result
            
            # Transient error, retry with backoff (except on last attempt)
            if attempt < self.max_retries - 1:
                time.sleep(backoff_seconds)
                backoff_seconds *= self.backoff_multiplier
        
        # All retries exhausted
        return Result.err(last_error)
