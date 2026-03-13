"""Unit tests for Market Data Ingester with failover logic"""
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch
from src.market_data_ingester import MarketDataIngester
from src.data_sources import DataSourceAdapter, DataError
from src.models import PriceData, DataSource
from src.config_models import DataSourceConfig
from src.result import Result


class MockAdapter(DataSourceAdapter):
    """Mock adapter for testing"""
    
    def __init__(self, historical_result=None, realtime_result=None):
        self.historical_result = historical_result
        self.realtime_result = realtime_result
        self.historical_call_count = 0
        self.realtime_call_count = 0
    
    def fetch_historical(self, symbol, start_date, end_date):
        self.historical_call_count += 1
        return self.historical_result
    
    def fetch_realtime(self, symbol):
        self.realtime_call_count += 1
        return self.realtime_result


class TestMarketDataIngesterFailover:
    """Test failover logic"""
    
    def test_primary_source_success(self):
        """Test successful fetch from primary source"""
        # Create valid price data
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        # Primary adapter succeeds
        primary_adapter = MockAdapter(
            historical_result=Result.ok([price_data])
        )
        
        # Secondary adapter (should not be called)
        secondary_adapter = MockAdapter(
            historical_result=Result.ok([price_data])
        )
        
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1),
            DataSourceConfig(DataSource.ALPACA, "key2", priority=2)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: primary_adapter,
            DataSource.ALPACA: secondary_adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        result = ingester.fetch_historical("AAPL", datetime.now(), datetime.now())
        
        assert result.is_ok()
        assert len(result.unwrap()) == 1
        assert primary_adapter.historical_call_count >= 1
        assert secondary_adapter.historical_call_count == 0
    
    def test_failover_to_secondary_source(self):
        """Test failover when primary source fails"""
        # Create valid price data
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.ALPACA
        )
        
        # Primary adapter fails
        primary_adapter = MockAdapter(
            historical_result=Result.err(DataError("Primary source unavailable"))
        )
        
        # Secondary adapter succeeds
        secondary_adapter = MockAdapter(
            historical_result=Result.ok([price_data])
        )
        
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1),
            DataSourceConfig(DataSource.ALPACA, "key2", priority=2)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: primary_adapter,
            DataSource.ALPACA: secondary_adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        result = ingester.fetch_historical("AAPL", datetime.now(), datetime.now())
        
        assert result.is_ok()
        assert len(result.unwrap()) == 1
        assert result.unwrap()[0].source == DataSource.ALPACA
        assert primary_adapter.historical_call_count >= 1
        assert secondary_adapter.historical_call_count >= 1
    
    def test_all_sources_fail(self):
        """Test error when all sources fail"""
        # Both adapters fail
        primary_adapter = MockAdapter(
            historical_result=Result.err(DataError("Primary source error"))
        )
        
        secondary_adapter = MockAdapter(
            historical_result=Result.err(DataError("Secondary source error"))
        )
        
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1),
            DataSourceConfig(DataSource.ALPACA, "key2", priority=2)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: primary_adapter,
            DataSource.ALPACA: secondary_adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        result = ingester.fetch_historical("AAPL", datetime.now(), datetime.now())
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Failed to fetch historical data" in str(error)
        assert "all sources" in str(error)
        assert "Primary source error" in str(error)
        assert "Secondary source error" in str(error)
    
    def test_priority_ordering(self):
        """Test that sources are tried in priority order"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.ALPACA
        )
        
        # Lower priority adapter (should be tried first)
        low_priority_adapter = MockAdapter(
            historical_result=Result.ok([price_data])
        )
        
        # Higher priority adapter (should not be called)
        high_priority_adapter = MockAdapter(
            historical_result=Result.ok([price_data])
        )
        
        # Note: priority 1 is higher than priority 10
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=10),
            DataSourceConfig(DataSource.ALPACA, "key2", priority=1)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: high_priority_adapter,
            DataSource.ALPACA: low_priority_adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        result = ingester.fetch_historical("AAPL", datetime.now(), datetime.now())
        
        assert result.is_ok()
        # Alpaca (priority 1) should be tried first
        assert low_priority_adapter.historical_call_count >= 1
        assert high_priority_adapter.historical_call_count == 0


class TestMarketDataIngesterRetry:
    """Test retry with exponential backoff"""
    
    def test_retry_on_transient_error(self):
        """Test retry on network timeout"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        # Adapter fails twice with transient error, then succeeds
        call_count = 0
        def fetch_func(symbol, start, end):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return Result.err(DataError("Network timeout"))
            return Result.ok([price_data])
        
        adapter = Mock(spec=DataSourceAdapter)
        adapter.fetch_historical = fetch_func
        
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = ingester.fetch_historical("AAPL", datetime.now(), datetime.now())
        
        assert result.is_ok()
        assert call_count == 3  # Should retry twice before success
    
    def test_no_retry_on_permanent_error(self):
        """Test no retry on non-transient error"""
        # Adapter fails with permanent error
        adapter = MockAdapter(
            historical_result=Result.err(DataError("Invalid symbol"))
        )
        
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        result = ingester.fetch_historical("AAPL", datetime.now(), datetime.now())
        
        assert result.is_err()
        # Should only try once (no retries for permanent errors)
        assert adapter.historical_call_count == 1
    
    def test_max_retries_exhausted(self):
        """Test that retries stop after max attempts"""
        # Adapter always fails with transient error
        adapter = MockAdapter(
            historical_result=Result.err(DataError("Connection timeout"))
        )
        
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = ingester.fetch_historical("AAPL", datetime.now(), datetime.now())
        
        assert result.is_err()
        # Should try max_retries times (default 3)
        assert adapter.historical_call_count == 3
    
    def test_exponential_backoff(self):
        """Test exponential backoff timing"""
        adapter = MockAdapter(
            historical_result=Result.err(DataError("Network timeout"))
        )
        
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        
        sleep_calls = []
        def mock_sleep(seconds):
            sleep_calls.append(seconds)
        
        with patch('time.sleep', side_effect=mock_sleep):
            result = ingester.fetch_historical("AAPL", datetime.now(), datetime.now())
        
        assert result.is_err()
        # Should have exponential backoff: 1s, 2s (no sleep after last attempt)
        assert len(sleep_calls) == 2
        assert sleep_calls[0] == 1
        assert sleep_calls[1] == 2


class TestMarketDataIngesterRealtime:
    """Test real-time data fetching"""
    
    def test_realtime_primary_success(self):
        """Test successful real-time fetch from primary source"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        primary_adapter = MockAdapter(
            realtime_result=Result.ok(price_data)
        )
        
        secondary_adapter = MockAdapter(
            realtime_result=Result.ok(price_data)
        )
        
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1),
            DataSourceConfig(DataSource.ALPACA, "key2", priority=2)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: primary_adapter,
            DataSource.ALPACA: secondary_adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        result = ingester.fetch_realtime("AAPL")
        
        assert result.is_ok()
        assert result.unwrap().symbol == "AAPL"
        assert primary_adapter.realtime_call_count >= 1
        assert secondary_adapter.realtime_call_count == 0
    
    def test_realtime_failover(self):
        """Test real-time failover to secondary source"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.ALPACA
        )
        
        primary_adapter = MockAdapter(
            realtime_result=Result.err(DataError("Primary unavailable"))
        )
        
        secondary_adapter = MockAdapter(
            realtime_result=Result.ok(price_data)
        )
        
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1),
            DataSourceConfig(DataSource.ALPACA, "key2", priority=2)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: primary_adapter,
            DataSource.ALPACA: secondary_adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        result = ingester.fetch_realtime("AAPL")
        
        assert result.is_ok()
        assert result.unwrap().source == DataSource.ALPACA
        assert primary_adapter.realtime_call_count >= 1
        assert secondary_adapter.realtime_call_count >= 1
    
    def test_realtime_all_sources_fail(self):
        """Test error when all real-time sources fail"""
        primary_adapter = MockAdapter(
            realtime_result=Result.err(DataError("Primary error"))
        )
        
        secondary_adapter = MockAdapter(
            realtime_result=Result.err(DataError("Secondary error"))
        )
        
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1),
            DataSourceConfig(DataSource.ALPACA, "key2", priority=2)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: primary_adapter,
            DataSource.ALPACA: secondary_adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        result = ingester.fetch_realtime("AAPL")
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Failed to fetch real-time data" in str(error)
        assert "all sources" in str(error)


class TestMarketDataIngesterValidation:
    """Test data validation during failover"""
    
    def test_validation_failure_triggers_failover(self):
        """Test that validation failures trigger failover to next source"""
        # Invalid price data (negative price)
        invalid_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("-150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        # Valid price data
        valid_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.ALPACA
        )
        
        primary_adapter = MockAdapter(
            realtime_result=Result.ok(invalid_data)
        )
        
        secondary_adapter = MockAdapter(
            realtime_result=Result.ok(valid_data)
        )
        
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1),
            DataSourceConfig(DataSource.ALPACA, "key2", priority=2)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: primary_adapter,
            DataSource.ALPACA: secondary_adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        result = ingester.fetch_realtime("AAPL")
        
        assert result.is_ok()
        assert result.unwrap().source == DataSource.ALPACA
        assert primary_adapter.realtime_call_count >= 1
        assert secondary_adapter.realtime_call_count >= 1
    
    def test_partial_validation_failures_in_historical(self):
        """Test that some valid data is returned even if some points fail validation"""
        # Mix of valid and invalid data
        valid_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        invalid_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("-150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        adapter = MockAdapter(
            historical_result=Result.ok([valid_data, invalid_data, valid_data])
        )
        
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1)
        ]
        
        adapters = {
            DataSource.YAHOO_FINANCE: adapter
        }
        
        ingester = MarketDataIngester(adapters, configs)
        result = ingester.fetch_historical("AAPL", datetime.now(), datetime.now())
        
        assert result.is_ok()
        # Should return only the 2 valid data points
        assert len(result.unwrap()) == 2


class TestMarketDataIngesterEdgeCases:
    """Test edge cases"""
    
    def test_missing_adapter(self):
        """Test handling when adapter is not available"""
        configs = [
            DataSourceConfig(DataSource.YAHOO_FINANCE, "key1", priority=1)
        ]
        
        # No adapters provided
        adapters = {}
        
        ingester = MarketDataIngester(adapters, configs)
        result = ingester.fetch_realtime("AAPL")
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Adapter not available" in str(error)
    
    def test_empty_configs(self):
        """Test with no data source configs"""
        adapters = {}
        configs = []
        
        ingester = MarketDataIngester(adapters, configs)
        result = ingester.fetch_realtime("AAPL")
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "all sources" in str(error)
