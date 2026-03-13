"""Bug condition exploration test for Alpaca authentication failure

**Validates: Requirements 1.1, 1.4, 2.1, 2.2**

This test encodes the EXPECTED behavior (successful authentication) but is designed
to FAIL on unfixed code where api_secret is missing from the Alpaca data source config.

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
When the test fails with 401 Unauthorized, it proves the bug condition is present.
After the fix (adding api_secret to config), this test should pass.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta, time
from decimal import Decimal
from unittest.mock import patch, Mock
import requests
from src.data_sources import AlpacaAdapter, DataError
from src.config_manager import ConfigurationManager
from src.config_models import Config, RiskParameters, TradingSchedule, BrokerConfig, LoggingConfig
from src.models import DataSource, ExecutionMode


def create_dummy_config():
    """Create a minimal dummy config for ConfigurationManager initialization"""
    return Config(
        execution_mode=ExecutionMode.SIMULATION,
        data_sources=[],
        risk_parameters=RiskParameters(
            stop_loss_pct=Decimal("0.05"),
            take_profit_pct=Decimal("0.10"),
            max_position_size_pct=Decimal("0.20"),
            max_drawdown_pct=Decimal("0.15"),
            max_portfolio_value=Decimal("100000")
        ),
        active_models=[],
        trading_schedule=TradingSchedule(
            market_open=time(9, 30),
            market_close=time(16, 0),
            data_fetch_interval_seconds=300,
            trading_days=["MON"]
        ),
        broker_config=BrokerConfig(
            broker_name="dummy",
            api_key="dummy",
            api_secret="dummy",
            base_url="https://dummy.com"
        ),
        logging_config=LoggingConfig(
            log_directory="./logs",
            log_level="INFO",
            rotation_policy="daily"
        )
    )


class TestAlpacaBugConditionExploration:
    """Exploration tests to surface counterexamples demonstrating the auth bug"""
    
    def test_alpaca_adapter_with_missing_api_secret_fails_auth(self):
        """
        Test that AlpacaAdapter initialized with api_key but empty api_secret fails authentication.
        
        **Validates: Requirements 1.1, 1.4, 2.1, 2.2**
        
        This test loads the current config.json (which is missing api_secret for Alpaca),
        initializes the AlpacaAdapter with those incomplete credentials, and attempts
        to fetch real-time market data.
        
        EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS with 401 Unauthorized error
        (this is correct - it proves the bug exists)
        
        EXPECTED OUTCOME ON FIXED CODE: Test PASSES with successful authentication
        """
        # Load the actual config to get the Alpaca data source configuration
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        
        assert config_result.is_ok(), "Config should load successfully"
        config = config_result.unwrap()
        
        # Find the Alpaca data source configuration
        alpaca_config = None
        for ds_config in config.data_sources:
            if ds_config.source == DataSource.ALPACA:
                alpaca_config = ds_config
                break
        
        assert alpaca_config is not None, "Alpaca data source should be configured"
        
        # Verify bug condition: api_key exists but api_secret is empty
        # This is the bug condition from the design document
        assert alpaca_config.api_key != "", "Alpaca api_key should be present"
        
        # Initialize AlpacaAdapter with the credentials from config
        # On unfixed code: api_secret will be empty string (default value)
        # On fixed code: api_secret will be the actual secret from config
        adapter = AlpacaAdapter(
            api_key=alpaca_config.api_key,
            api_secret=alpaca_config.api_secret
        )
        
        # Attempt to fetch real-time market data for AAPL
        # This will make an actual API call to Alpaca
        result = adapter.fetch_realtime("AAPL")
        
        # EXPECTED BEHAVIOR (from design): Authentication should succeed
        # On unfixed code: This assertion will FAIL with 401 error (bug confirmed)
        # On fixed code: This assertion will PASS (bug is fixed)
        assert result.is_ok(), (
            f"Alpaca authentication should succeed with valid credentials. "
            f"Error: {result.unwrap_err() if result.is_err() else 'None'}"
        )
        
        # If we get here, authentication succeeded - verify we got valid data
        price_data = result.unwrap()
        assert price_data.symbol == "AAPL"
        assert price_data.close > 0, "Should have valid price data"
    
    @given(symbol=st.sampled_from(["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]))
    @settings(
        max_examples=2,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None
    )
    def test_alpaca_realtime_fetch_with_config_credentials(self, symbol):
        """
        Property test: For any stock symbol, Alpaca adapter with config credentials
        should successfully authenticate and fetch market data.
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        **Property 1: Bug Condition** - Alpaca Authentication Failure with Missing api_secret
        
        For any symbol in the test set, when AlpacaAdapter is initialized with
        credentials from config.json:
        - ON UNFIXED CODE: api_secret is empty, authentication fails with 401
        - ON FIXED CODE: api_secret is present, authentication succeeds
        
        EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS with 401 Unauthorized
        EXPECTED OUTCOME ON FIXED CODE: Test PASSES with successful data fetch
        """
        # Load config and get Alpaca credentials
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        assert config_result.is_ok()
        config = config_result.unwrap()
        
        alpaca_config = None
        for ds_config in config.data_sources:
            if ds_config.source == DataSource.ALPACA:
                alpaca_config = ds_config
                break
        
        assert alpaca_config is not None
        
        # Initialize adapter with config credentials
        adapter = AlpacaAdapter(
            api_key=alpaca_config.api_key,
            api_secret=alpaca_config.api_secret
        )
        
        # Attempt to fetch real-time data for the generated symbol
        result = adapter.fetch_realtime(symbol)
        
        # EXPECTED BEHAVIOR: Should successfully authenticate and fetch data
        # On unfixed code: FAILS with 401 (proves bug exists)
        # On fixed code: PASSES (proves bug is fixed)
        assert result.is_ok(), (
            f"Alpaca should authenticate successfully for symbol {symbol}. "
            f"Error: {result.unwrap_err() if result.is_err() else 'None'}"
        )
        
        price_data = result.unwrap()
        assert price_data.symbol == symbol
        assert price_data.source == DataSource.ALPACA
    
    @pytest.mark.xfail(reason="Alpaca paper trading API may not support historical data requests")
    @given(
        symbol=st.sampled_from(["AAPL", "MSFT", "GOOGL"]),
        days_back=st.integers(min_value=7, max_value=30)
    )
    @settings(
        max_examples=2,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None
    )
    def test_alpaca_historical_fetch_with_config_credentials(self, symbol, days_back):
        """
        Property test: For any symbol and date range, Alpaca adapter with config
        credentials should successfully authenticate and fetch historical data.
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        **Property 1: Bug Condition** - Alpaca Authentication Failure with Missing api_secret
        
        For any symbol and date range, when AlpacaAdapter is initialized with
        credentials from config.json:
        - ON UNFIXED CODE: api_secret is empty, authentication fails with 401
        - ON FIXED CODE: api_secret is present, authentication succeeds
        
        EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS with 401 Unauthorized
        EXPECTED OUTCOME ON FIXED CODE: Test PASSES with successful data fetch
        """
        # Load config and get Alpaca credentials
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        assert config_result.is_ok()
        config = config_result.unwrap()
        
        alpaca_config = None
        for ds_config in config.data_sources:
            if ds_config.source == DataSource.ALPACA:
                alpaca_config = ds_config
                break
        
        assert alpaca_config is not None
        
        # Initialize adapter with config credentials
        adapter = AlpacaAdapter(
            api_key=alpaca_config.api_key,
            api_secret=alpaca_config.api_secret
        )
        
        # Use a fixed date range in mid-2024 that we know has market data
        # Avoid holidays and weekends by using dates in the middle of the year
        end_date = datetime(2024, 6, 30)
        start_date = end_date - timedelta(days=days_back)
        
        # Attempt to fetch historical data
        result = adapter.fetch_historical(symbol, start_date, end_date)
        
        # EXPECTED BEHAVIOR: Should successfully authenticate and fetch data
        # On unfixed code: FAILS with 401 (proves bug exists)
        # On fixed code: PASSES (proves bug is fixed)
        assert result.is_ok(), (
            f"Alpaca should authenticate successfully for {symbol} "
            f"from {start_date.date()} to {end_date.date()}. "
            f"Error: {result.unwrap_err() if result.is_err() else 'None'}"
        )
        
        price_data_list = result.unwrap()
        assert len(price_data_list) > 0, "Should have historical data"
        assert all(pd.symbol == symbol for pd in price_data_list)
        assert all(pd.source == DataSource.ALPACA for pd in price_data_list)
    
    def test_alpaca_adapter_headers_contain_api_secret(self):
        """
        Test that AlpacaAdapter headers contain the api_secret from config.
        
        **Validates: Requirements 1.4, 2.2**
        
        This test verifies that the APCA-API-SECRET-KEY header is properly set
        when initializing the AlpacaAdapter with config credentials.
        
        EXPECTED OUTCOME ON UNFIXED CODE: Header contains empty string (bug confirmed)
        EXPECTED OUTCOME ON FIXED CODE: Header contains actual secret (bug fixed)
        """
        # Load config and get Alpaca credentials
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        assert config_result.is_ok()
        config = config_result.unwrap()
        
        alpaca_config = None
        for ds_config in config.data_sources:
            if ds_config.source == DataSource.ALPACA:
                alpaca_config = ds_config
                break
        
        assert alpaca_config is not None
        
        # Initialize adapter
        adapter = AlpacaAdapter(
            api_key=alpaca_config.api_key,
            api_secret=alpaca_config.api_secret
        )
        
        # Verify headers are set correctly
        assert "APCA-API-KEY-ID" in adapter.headers
        assert "APCA-API-SECRET-KEY" in adapter.headers
        
        # EXPECTED BEHAVIOR: api_secret should be non-empty
        # On unfixed code: This will FAIL (api_secret is empty string)
        # On fixed code: This will PASS (api_secret has actual value)
        assert adapter.headers["APCA-API-SECRET-KEY"] != "", (
            "APCA-API-SECRET-KEY header should contain the api_secret from config. "
            "Empty string indicates missing api_secret field in config.json"
        )
        
        # Verify it matches what we expect from config
        assert adapter.headers["APCA-API-SECRET-KEY"] == alpaca_config.api_secret
        assert adapter.headers["APCA-API-KEY-ID"] == alpaca_config.api_key


class TestPreservationProperties:
    """
    Preservation property tests to verify non-Alpaca configuration remains unchanged.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    
    These tests verify that all configuration sections NOT related to the Alpaca
    api_secret field load identically and behave the same way after the fix.
    
    CRITICAL: These tests MUST PASS on UNFIXED code - they establish the baseline
    behavior that must be preserved when we add the api_secret field to Alpaca config.
    """
    
    def test_yahoo_finance_config_unchanged(self):
        """
        Test that Yahoo Finance data source configuration loads correctly.
        
        **Validates: Requirements 3.1**
        
        **Property 2: Preservation** - Non-Alpaca Configuration Unchanged
        
        Yahoo Finance does not require api_secret and should continue to work
        with only api_key field. This test verifies the baseline behavior.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code (establishes baseline)
        """
        # Load config
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        
        assert config_result.is_ok(), "Config should load successfully"
        config = config_result.unwrap()
        
        # Find Yahoo Finance data source
        yahoo_config = None
        for ds_config in config.data_sources:
            if ds_config.source == DataSource.YAHOO_FINANCE:
                yahoo_config = ds_config
                break
        
        assert yahoo_config is not None, "Yahoo Finance should be configured"
        
        # Verify Yahoo Finance configuration (baseline behavior to preserve)
        assert yahoo_config.api_key == "not_required_for_yahoo"
        assert yahoo_config.priority == 2
        assert yahoo_config.api_secret == ""  # Yahoo doesn't need api_secret
    
    def test_broker_config_unchanged(self):
        """
        Test that broker_config section loads correctly with all fields.
        
        **Validates: Requirements 3.2, 3.4**
        
        **Property 2: Preservation** - Non-Alpaca Configuration Unchanged
        
        The broker_config already has api_secret and should remain completely
        unchanged by the fix to data_sources. This test verifies baseline behavior.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code (establishes baseline)
        """
        # Load config
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        
        assert config_result.is_ok()
        config = config_result.unwrap()
        
        # Verify broker config (baseline behavior to preserve)
        broker = config.broker_config
        assert broker.broker_name == "alpaca"
        assert broker.api_key == "PKQ7YTGYJWIEY6G5AGMTDHJUQ3"
        assert broker.api_secret == "HxMG9Lnf2atktpCP4DFbo7jbkVJ79dDGUYiZH6whdgXz"
        assert broker.base_url == "https://paper-api.alpaca.markets"
    
    def test_risk_parameters_unchanged(self):
        """
        Test that risk_parameters section loads correctly.
        
        **Validates: Requirements 3.3, 3.4**
        
        **Property 2: Preservation** - Non-Alpaca Configuration Unchanged
        
        Risk parameters should be completely unaffected by data source changes.
        This test verifies baseline behavior.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code (establishes baseline)
        """
        # Load config
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        
        assert config_result.is_ok()
        config = config_result.unwrap()
        
        # Verify risk parameters (baseline behavior to preserve)
        risk = config.risk_parameters
        assert risk.stop_loss_pct == Decimal("0.05")
        assert risk.take_profit_pct == Decimal("0.10")
        assert risk.max_position_size_pct == Decimal("0.20")
        assert risk.max_drawdown_pct == Decimal("0.15")
        assert risk.max_portfolio_value == Decimal("100000.00")
    
    def test_trading_schedule_unchanged(self):
        """
        Test that trading_schedule section loads correctly.
        
        **Validates: Requirements 3.4**
        
        **Property 2: Preservation** - Non-Alpaca Configuration Unchanged
        
        Trading schedule should be completely unaffected by data source changes.
        This test verifies baseline behavior.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code (establishes baseline)
        """
        from datetime import time
        
        # Load config
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        
        assert config_result.is_ok()
        config = config_result.unwrap()
        
        # Verify trading schedule (baseline behavior to preserve)
        schedule = config.trading_schedule
        assert schedule.market_open == time(9, 30)
        assert schedule.market_close == time(16, 0)
        assert schedule.data_fetch_interval_seconds == 300
        assert schedule.trading_days == ["MON", "TUE", "WED", "THU", "FRI"]
    
    def test_logging_config_unchanged(self):
        """
        Test that logging_config section loads correctly.
        
        **Validates: Requirements 3.4**
        
        **Property 2: Preservation** - Non-Alpaca Configuration Unchanged
        
        Logging configuration should be completely unaffected by data source changes.
        This test verifies baseline behavior.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code (establishes baseline)
        """
        # Load config
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        
        assert config_result.is_ok()
        config = config_result.unwrap()
        
        # Verify logging config (baseline behavior to preserve)
        logging = config.logging_config
        assert logging.log_directory == "./logs"
        assert logging.log_level == "INFO"
        assert logging.rotation_policy == "daily"
    
    def test_active_models_unchanged(self):
        """
        Test that active_models section loads correctly.
        
        **Validates: Requirements 3.4**
        
        **Property 2: Preservation** - Non-Alpaca Configuration Unchanged
        
        Active models configuration should be completely unaffected by data source changes.
        This test verifies baseline behavior.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code (establishes baseline)
        """
        # Load config
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        
        assert config_result.is_ok()
        config = config_result.unwrap()
        
        # Verify active models (baseline behavior to preserve)
        assert len(config.active_models) == 1
        model = config.active_models[0]
        assert model.model_id == "ma_crossover_v1"
        assert model.model_type == "moving_average"
        assert model.parameters == {"short_window": 20, "long_window": 50}
        assert model.enabled is True
    
    def test_data_source_priority_order_unchanged(self):
        """
        Test that data source priority ordering remains correct.
        
        **Validates: Requirements 3.2**
        
        **Property 2: Preservation** - Non-Alpaca Configuration Unchanged
        
        The priority order (Alpaca=1, Yahoo=2) should remain unchanged.
        This test verifies baseline behavior.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code (establishes baseline)
        """
        # Load config
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        
        assert config_result.is_ok()
        config = config_result.unwrap()
        
        # Verify data source count and priority order
        assert len(config.data_sources) == 2
        
        # Sort by priority to verify ordering
        sorted_sources = sorted(config.data_sources, key=lambda ds: ds.priority)
        
        # Alpaca should be first (priority 1)
        assert sorted_sources[0].source == DataSource.ALPACA
        assert sorted_sources[0].priority == 1
        
        # Yahoo Finance should be second (priority 2)
        assert sorted_sources[1].source == DataSource.YAHOO_FINANCE
        assert sorted_sources[1].priority == 2
    
    @given(
        config_field=st.sampled_from([
            "execution_mode",
            "risk_parameters",
            "active_models",
            "trading_schedule",
            "broker_config",
            "logging_config"
        ])
    )
    @settings(max_examples=3, deadline=None)
    def test_non_data_source_fields_load_identically(self, config_field):
        """
        Property test: All non-data-source configuration fields load identically.
        
        **Validates: Requirements 3.3, 3.4, 3.5**
        
        **Property 2: Preservation** - Non-Alpaca Configuration Unchanged
        
        For any configuration field that is NOT in the data_sources array,
        the configuration should load with exactly the same values.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code (establishes baseline)
        """
        # Load config
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        
        assert config_result.is_ok()
        config = config_result.unwrap()
        
        # Verify the field exists and has expected type
        assert hasattr(config, config_field), f"Config should have {config_field}"
        field_value = getattr(config, config_field)
        assert field_value is not None, f"{config_field} should not be None"
        
        # Type checks for each field
        if config_field == "execution_mode":
            from src.models import ExecutionMode
            assert isinstance(field_value, ExecutionMode)
        elif config_field == "risk_parameters":
            from src.config_models import RiskParameters
            assert isinstance(field_value, RiskParameters)
        elif config_field == "active_models":
            assert isinstance(field_value, list)
            assert len(field_value) > 0
        elif config_field == "trading_schedule":
            from src.config_models import TradingSchedule
            assert isinstance(field_value, TradingSchedule)
        elif config_field == "broker_config":
            from src.config_models import BrokerConfig
            assert isinstance(field_value, BrokerConfig)
        elif config_field == "logging_config":
            from src.config_models import LoggingConfig
            assert isinstance(field_value, LoggingConfig)
    
    @given(
        data_source_type=st.sampled_from([DataSource.YAHOO_FINANCE])
    )
    @settings(max_examples=2, deadline=None)
    def test_non_alpaca_data_sources_unchanged(self, data_source_type):
        """
        Property test: Non-Alpaca data sources load with correct configuration.
        
        **Validates: Requirements 3.1**
        
        **Property 2: Preservation** - Non-Alpaca Configuration Unchanged
        
        For any data source that is NOT Alpaca, the configuration should load
        correctly and remain unchanged by the Alpaca api_secret fix.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code (establishes baseline)
        """
        # Load config
        config_manager = ConfigurationManager(create_dummy_config())
        config_result = config_manager.load_config("config/config.json")
        
        assert config_result.is_ok()
        config = config_result.unwrap()
        
        # Find the specified data source
        ds_config = None
        for ds in config.data_sources:
            if ds.source == data_source_type:
                ds_config = ds
                break
        
        assert ds_config is not None, f"{data_source_type} should be configured"
        
        # Verify basic properties
        assert ds_config.api_key != "", "api_key should be present"
        assert ds_config.priority > 0, "priority should be positive"
        
        # Yahoo Finance doesn't need api_secret
        if data_source_type == DataSource.YAHOO_FINANCE:
            assert ds_config.api_secret == "", "Yahoo Finance doesn't need api_secret"
