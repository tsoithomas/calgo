"""Unit tests for data source adapters"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from src.data_sources import (
    DataSourceAdapter,
    YahooFinanceAdapter,
    AlpacaAdapter,
    DataError,
    ValidationError,
    normalize_data,
    validate_data
)
from src.models import PriceData, DataSource


class TestYahooFinanceAdapter:
    """Unit tests for Yahoo Finance adapter"""
    
    def test_fetch_historical_success(self):
        """Test successful historical data fetch"""
        adapter = YahooFinanceAdapter()
        
        # Mock response data
        mock_response = Mock()
        mock_response.json.return_value = {
            "chart": {
                "result": [{
                    "timestamp": [1704067200, 1704153600],
                    "indicators": {
                        "quote": [{
                            "open": [150.0, 151.0],
                            "high": [152.0, 153.0],
                            "low": [149.0, 150.0],
                            "close": [151.0, 152.0],
                            "volume": [1000000, 1100000]
                        }]
                    }
                }]
            }
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 3)
            result = adapter.fetch_historical("AAPL", start_date, end_date)
            
            assert result.is_ok()
            price_data_list = result.unwrap()
            assert len(price_data_list) == 2
            assert price_data_list[0].symbol == "AAPL"
            assert price_data_list[0].source == DataSource.YAHOO_FINANCE
            assert price_data_list[0].close == Decimal("151.0")
    
    def test_fetch_historical_no_data(self):
        """Test historical fetch with no data available"""
        adapter = YahooFinanceAdapter()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "chart": {
                "result": []
            }
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 3)
            result = adapter.fetch_historical("INVALID", start_date, end_date)
            
            assert result.is_err()
            error = result.unwrap_err()
            assert "No data found" in str(error)
    
    def test_fetch_historical_network_error(self):
        """Test historical fetch with network error"""
        adapter = YahooFinanceAdapter()
        
        with patch('requests.get', side_effect=Exception("Connection timeout")):
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 3)
            result = adapter.fetch_historical("AAPL", start_date, end_date)
            
            assert result.is_err()
            error = result.unwrap_err()
            assert "error" in str(error).lower()
    
    def test_fetch_realtime_success(self):
        """Test successful real-time data fetch"""
        adapter = YahooFinanceAdapter()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "quoteResponse": {
                "result": [{
                    "symbol": "AAPL",
                    "regularMarketOpen": 150.0,
                    "regularMarketDayHigh": 152.0,
                    "regularMarketDayLow": 149.0,
                    "regularMarketPrice": 151.0,
                    "regularMarketVolume": 1000000
                }]
            }
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            result = adapter.fetch_realtime("AAPL")
            
            assert result.is_ok()
            price_data = result.unwrap()
            assert price_data.symbol == "AAPL"
            assert price_data.source == DataSource.YAHOO_FINANCE
            assert price_data.close == Decimal("151.0")
            assert price_data.volume == 1000000
    
    def test_fetch_realtime_no_data(self):
        """Test real-time fetch with no data available"""
        adapter = YahooFinanceAdapter()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "quoteResponse": {
                "result": []
            }
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            result = adapter.fetch_realtime("INVALID")
            
            assert result.is_err()
            error = result.unwrap_err()
            assert "No data found" in str(error)
    
    def test_fetch_realtime_network_error(self):
        """Test real-time fetch with network error"""
        adapter = YahooFinanceAdapter()
        
        with patch('requests.get', side_effect=Exception("Connection timeout")):
            result = adapter.fetch_realtime("AAPL")
            
            assert result.is_err()
            error = result.unwrap_err()
            assert "error" in str(error).lower()


class TestAlpacaAdapter:
    """Unit tests for Alpaca adapter"""
    
    def test_initialization(self):
        """Test Alpaca adapter initialization"""
        adapter = AlpacaAdapter(
            api_key="test_key",
            api_secret="test_secret"
        )
        
        assert adapter.api_key == "test_key"
        assert adapter.api_secret == "test_secret"
        assert adapter.headers["APCA-API-KEY-ID"] == "test_key"
        assert adapter.headers["APCA-API-SECRET-KEY"] == "test_secret"
    
    def test_fetch_historical_success(self):
        """Test successful historical data fetch"""
        adapter = AlpacaAdapter(
            api_key="test_key",
            api_secret="test_secret"
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "bars": [
                {
                    "t": "2024-01-01T00:00:00Z",
                    "o": 150.0,
                    "h": 152.0,
                    "l": 149.0,
                    "c": 151.0,
                    "v": 1000000
                },
                {
                    "t": "2024-01-02T00:00:00Z",
                    "o": 151.0,
                    "h": 153.0,
                    "l": 150.0,
                    "c": 152.0,
                    "v": 1100000
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 3)
            result = adapter.fetch_historical("AAPL", start_date, end_date)
            
            assert result.is_ok()
            price_data_list = result.unwrap()
            assert len(price_data_list) == 2
            assert price_data_list[0].symbol == "AAPL"
            assert price_data_list[0].source == DataSource.ALPACA
            assert price_data_list[0].close == Decimal("151.0")
    
    def test_fetch_historical_no_data(self):
        """Test historical fetch with no data available"""
        adapter = AlpacaAdapter(
            api_key="test_key",
            api_secret="test_secret"
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "bars": []
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 3)
            result = adapter.fetch_historical("INVALID", start_date, end_date)
            
            assert result.is_err()
            error = result.unwrap_err()
            assert "No data found" in str(error)
    
    def test_fetch_historical_network_error(self):
        """Test historical fetch with network error"""
        adapter = AlpacaAdapter(
            api_key="test_key",
            api_secret="test_secret"
        )
        
        with patch('requests.get', side_effect=Exception("Connection timeout")):
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 3)
            result = adapter.fetch_historical("AAPL", start_date, end_date)
            
            assert result.is_err()
            error = result.unwrap_err()
            assert "error" in str(error).lower()
    
    def test_fetch_realtime_success(self):
        """Test successful real-time data fetch"""
        adapter = AlpacaAdapter(
            api_key="test_key",
            api_secret="test_secret"
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "bar": {
                "t": "2024-01-01T15:30:00Z",
                "o": 150.0,
                "h": 152.0,
                "l": 149.0,
                "c": 151.0,
                "v": 1000000
            }
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            result = adapter.fetch_realtime("AAPL")
            
            assert result.is_ok()
            price_data = result.unwrap()
            assert price_data.symbol == "AAPL"
            assert price_data.source == DataSource.ALPACA
            assert price_data.close == Decimal("151.0")
            assert price_data.volume == 1000000
    
    def test_fetch_realtime_no_data(self):
        """Test real-time fetch with no data available"""
        adapter = AlpacaAdapter(
            api_key="test_key",
            api_secret="test_secret"
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            result = adapter.fetch_realtime("INVALID")
            
            assert result.is_err()
            error = result.unwrap_err()
            assert "Invalid response format" in str(error)
    
    def test_fetch_realtime_network_error(self):
        """Test real-time fetch with network error"""
        adapter = AlpacaAdapter(
            api_key="test_key",
            api_secret="test_secret"
        )
        
        with patch('requests.get', side_effect=Exception("Connection timeout")):
            result = adapter.fetch_realtime("AAPL")
            
            assert result.is_err()
            error = result.unwrap_err()
            assert "error" in str(error).lower()


class TestDataSourceInterface:
    """Test that adapters implement the DataSourceAdapter interface"""
    
    def test_yahoo_implements_interface(self):
        """Test Yahoo Finance adapter implements DataSourceAdapter"""
        adapter = YahooFinanceAdapter()
        assert isinstance(adapter, DataSourceAdapter)
        assert hasattr(adapter, 'fetch_historical')
        assert hasattr(adapter, 'fetch_realtime')
    
    def test_alpaca_implements_interface(self):
        """Test Alpaca adapter implements DataSourceAdapter"""
        adapter = AlpacaAdapter(api_key="test", api_secret="test")
        assert isinstance(adapter, DataSourceAdapter)
        assert hasattr(adapter, 'fetch_historical')
        assert hasattr(adapter, 'fetch_realtime')


class TestNormalizeData:
    """Unit tests for normalize_data function"""
    
    def test_normalize_yahoo_finance_data(self):
        """Test normalizing Yahoo Finance data format"""
        raw_data = {
            "timestamp": 1704067200,
            "open": 150.0,
            "high": 152.0,
            "low": 149.0,
            "close": 151.0,
            "volume": 1000000
        }
        
        result = normalize_data(raw_data, DataSource.YAHOO_FINANCE, "AAPL")
        
        assert result.is_ok()
        price_data = result.unwrap()
        assert price_data.symbol == "AAPL"
        assert price_data.source == DataSource.YAHOO_FINANCE
        assert price_data.open == Decimal("150.0")
        assert price_data.high == Decimal("152.0")
        assert price_data.low == Decimal("149.0")
        assert price_data.close == Decimal("151.0")
        assert price_data.volume == 1000000
        assert isinstance(price_data.timestamp, datetime)
    
    def test_normalize_alpaca_data(self):
        """Test normalizing Alpaca data format"""
        raw_data = {
            "t": "2024-01-01T15:30:00Z",
            "o": 150.0,
            "h": 152.0,
            "l": 149.0,
            "c": 151.0,
            "v": 1000000
        }
        
        result = normalize_data(raw_data, DataSource.ALPACA, "AAPL")
        
        assert result.is_ok()
        price_data = result.unwrap()
        assert price_data.symbol == "AAPL"
        assert price_data.source == DataSource.ALPACA
        assert price_data.open == Decimal("150.0")
        assert price_data.high == Decimal("152.0")
        assert price_data.low == Decimal("149.0")
        assert price_data.close == Decimal("151.0")
        assert price_data.volume == 1000000
        assert isinstance(price_data.timestamp, datetime)
    
    def test_normalize_missing_fields(self):
        """Test normalizing data with missing fields uses defaults"""
        raw_data = {}
        
        result = normalize_data(raw_data, DataSource.YAHOO_FINANCE, "AAPL")
        
        assert result.is_ok()
        price_data = result.unwrap()
        assert price_data.symbol == "AAPL"
        assert price_data.open == Decimal("0")
        assert price_data.volume == 0
    
    def test_normalize_invalid_data_type(self):
        """Test normalizing data with invalid types"""
        raw_data = {
            "timestamp": "invalid",
            "open": "not_a_number",
            "high": 152.0,
            "low": 149.0,
            "close": 151.0,
            "volume": 1000000
        }
        
        result = normalize_data(raw_data, DataSource.YAHOO_FINANCE, "AAPL")
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Failed to normalize" in str(error)


class TestValidateData:
    """Unit tests for validate_data function"""
    
    def test_validate_valid_data(self):
        """Test validating correct price data"""
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
        
        result = validate_data(price_data)
        
        assert result.is_ok()
        validated = result.unwrap()
        assert validated.symbol == "AAPL"
    
    def test_validate_negative_open_price(self):
        """Test validation fails for negative open price"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("-150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        result = validate_data(price_data)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Negative open price" in str(error)
    
    def test_validate_negative_high_price(self):
        """Test validation fails for negative high price"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("-152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        result = validate_data(price_data)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Negative high price" in str(error)
    
    def test_validate_negative_low_price(self):
        """Test validation fails for negative low price"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("-149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        result = validate_data(price_data)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Negative low price" in str(error)
    
    def test_validate_negative_close_price(self):
        """Test validation fails for negative close price"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("-151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        result = validate_data(price_data)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Negative close price" in str(error)
    
    def test_validate_high_less_than_low(self):
        """Test validation fails when high < low"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("148.0"),
            low=Decimal("149.0"),
            close=Decimal("148.5"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        result = validate_data(price_data)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "High price" in str(error) and "less than low price" in str(error)
    
    def test_validate_open_outside_range(self):
        """Test validation fails when open is outside high-low range"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("160.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        result = validate_data(price_data)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Open price" in str(error) and "outside high-low range" in str(error)
    
    def test_validate_close_outside_range(self):
        """Test validation fails when close is outside high-low range"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("160.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        result = validate_data(price_data)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Close price" in str(error) and "outside high-low range" in str(error)
    
    def test_validate_negative_volume(self):
        """Test validation fails for negative volume"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=-1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        result = validate_data(price_data)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Negative volume" in str(error)
    
    def test_validate_missing_timestamp(self):
        """Test validation fails for missing timestamp"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=None,
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        result = validate_data(price_data)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Missing timestamp" in str(error)
    
    def test_validate_empty_symbol(self):
        """Test validation fails for empty symbol"""
        price_data = PriceData(
            symbol="",
            timestamp=datetime.now(),
            open=Decimal("150.0"),
            high=Decimal("152.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        result = validate_data(price_data)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Missing or empty symbol" in str(error)
    
    def test_validate_multiple_errors(self):
        """Test validation reports multiple errors"""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=None,
            open=Decimal("-150.0"),
            high=Decimal("148.0"),
            low=Decimal("149.0"),
            close=Decimal("151.0"),
            volume=-1000000,
            source=DataSource.YAHOO_FINANCE
        )
        
        result = validate_data(price_data)
        
        assert result.is_err()
        error = result.unwrap_err()
        error_msg = str(error)
        assert "Missing timestamp" in error_msg
        assert "Negative open price" in error_msg
        assert "Negative volume" in error_msg
