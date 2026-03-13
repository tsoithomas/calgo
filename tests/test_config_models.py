"""Unit tests for configuration data models"""
from datetime import time
from decimal import Decimal

from src.config_models import (
    Config, DataSourceConfig, ModelConfig, TradingSchedule,
    BrokerConfig, LoggingConfig, RiskParameters
)
from src.models import DataSource, ExecutionMode


def test_data_source_config_creation():
    """Test DataSourceConfig dataclass creation"""
    config = DataSourceConfig(
        source=DataSource.YAHOO_FINANCE,
        api_key="test_key_123",
        priority=1
    )
    assert config.source == DataSource.YAHOO_FINANCE
    assert config.api_key == "test_key_123"
    assert config.priority == 1


def test_model_config_creation():
    """Test ModelConfig dataclass creation"""
    config = ModelConfig(
        model_id="ma_crossover_v1",
        model_type="moving_average",
        parameters={"short_window": 20, "long_window": 50},
        enabled=True
    )
    assert config.model_id == "ma_crossover_v1"
    assert config.model_type == "moving_average"
    assert config.parameters["short_window"] == 20
    assert config.enabled is True


def test_trading_schedule_creation():
    """Test TradingSchedule dataclass creation"""
    schedule = TradingSchedule(
        market_open=time(9, 30),
        market_close=time(16, 0),
        data_fetch_interval_seconds=60,
        trading_days=["MON", "TUE", "WED", "THU", "FRI"]
    )
    assert schedule.market_open == time(9, 30)
    assert schedule.market_close == time(16, 0)
    assert schedule.data_fetch_interval_seconds == 60
    assert len(schedule.trading_days) == 5


def test_broker_config_creation():
    """Test BrokerConfig dataclass creation"""
    config = BrokerConfig(
        broker_name="alpaca",
        api_key="test_api_key",
        api_secret="test_api_secret",
        base_url="https://paper-api.alpaca.markets"
    )
    assert config.broker_name == "alpaca"
    assert config.api_key == "test_api_key"
    assert config.api_secret == "test_api_secret"
    assert config.base_url == "https://paper-api.alpaca.markets"


def test_logging_config_creation():
    """Test LoggingConfig dataclass creation"""
    config = LoggingConfig(
        log_directory="./logs",
        log_level="INFO",
        rotation_policy="daily"
    )
    assert config.log_directory == "./logs"
    assert config.log_level == "INFO"
    assert config.rotation_policy == "daily"


def test_risk_parameters_creation():
    """Test RiskParameters dataclass creation"""
    params = RiskParameters(
        stop_loss_pct=Decimal("0.05"),
        take_profit_pct=Decimal("0.10"),
        max_position_size_pct=Decimal("0.20"),
        max_drawdown_pct=Decimal("0.15"),
        max_portfolio_value=Decimal("100000.00")
    )
    assert params.stop_loss_pct == Decimal("0.05")
    assert params.take_profit_pct == Decimal("0.10")
    assert params.max_position_size_pct == Decimal("0.20")
    assert params.max_drawdown_pct == Decimal("0.15")
    assert params.max_portfolio_value == Decimal("100000.00")


def test_config_creation():
    """Test Config dataclass creation with all components"""
    data_source = DataSourceConfig(
        source=DataSource.ALPACA,
        api_key="test_key",
        priority=1
    )
    
    model = ModelConfig(
        model_id="test_model",
        model_type="ml_classifier",
        parameters={},
        enabled=True
    )
    
    schedule = TradingSchedule(
        market_open=time(9, 30),
        market_close=time(16, 0),
        data_fetch_interval_seconds=300,
        trading_days=["MON", "TUE", "WED", "THU", "FRI"]
    )
    
    broker = BrokerConfig(
        broker_name="alpaca",
        api_key="key",
        api_secret="secret",
        base_url="https://paper-api.alpaca.markets"
    )
    
    logging = LoggingConfig(
        log_directory="./logs",
        log_level="INFO",
        rotation_policy="daily"
    )
    
    risk = RiskParameters(
        stop_loss_pct=Decimal("0.05"),
        take_profit_pct=Decimal("0.10"),
        max_position_size_pct=Decimal("0.20"),
        max_drawdown_pct=Decimal("0.15"),
        max_portfolio_value=Decimal("100000.00")
    )
    
    config = Config(
        execution_mode=ExecutionMode.SIMULATION,
        data_sources=[data_source],
        risk_parameters=risk,
        active_models=[model],
        trading_schedule=schedule,
        broker_config=broker,
        logging_config=logging
    )
    
    assert config.execution_mode == ExecutionMode.SIMULATION
    assert len(config.data_sources) == 1
    assert config.data_sources[0].source == DataSource.ALPACA
    assert config.risk_parameters.stop_loss_pct == Decimal("0.05")
    assert len(config.active_models) == 1
    assert config.trading_schedule.market_open == time(9, 30)
    assert config.broker_config.broker_name == "alpaca"
    assert config.logging_config.log_level == "INFO"


def test_config_with_multiple_data_sources():
    """Test Config with multiple data sources ordered by priority"""
    ds1 = DataSourceConfig(
        source=DataSource.ALPACA,
        api_key="alpaca_key",
        priority=1
    )
    
    ds2 = DataSourceConfig(
        source=DataSource.YAHOO_FINANCE,
        api_key="yahoo_key",
        priority=2
    )
    
    config = Config(
        execution_mode=ExecutionMode.SIMULATION,
        data_sources=[ds1, ds2],
        risk_parameters=RiskParameters(
            stop_loss_pct=Decimal("0.05"),
            take_profit_pct=Decimal("0.10"),
            max_position_size_pct=Decimal("0.20"),
            max_drawdown_pct=Decimal("0.15"),
            max_portfolio_value=Decimal("100000.00")
        ),
        active_models=[],
        trading_schedule=TradingSchedule(
            market_open=time(9, 30),
            market_close=time(16, 0),
            data_fetch_interval_seconds=60,
            trading_days=["MON", "TUE", "WED", "THU", "FRI"]
        ),
        broker_config=BrokerConfig(
            broker_name="alpaca",
            api_key="key",
            api_secret="secret",
            base_url="https://paper-api.alpaca.markets"
        ),
        logging_config=LoggingConfig(
            log_directory="./logs",
            log_level="INFO",
            rotation_policy="daily"
        )
    )
    
    assert len(config.data_sources) == 2
    assert config.data_sources[0].priority == 1
    assert config.data_sources[1].priority == 2


def test_config_with_multiple_models():
    """Test Config with multiple AI models"""
    model1 = ModelConfig(
        model_id="ma_crossover",
        model_type="moving_average",
        parameters={"short": 20, "long": 50},
        enabled=True
    )
    
    model2 = ModelConfig(
        model_id="ml_classifier",
        model_type="machine_learning",
        parameters={"features": ["volume", "price"]},
        enabled=False
    )
    
    config = Config(
        execution_mode=ExecutionMode.LIVE,
        data_sources=[DataSourceConfig(
            source=DataSource.ALPACA,
            api_key="key",
            priority=1
        )],
        risk_parameters=RiskParameters(
            stop_loss_pct=Decimal("0.05"),
            take_profit_pct=Decimal("0.10"),
            max_position_size_pct=Decimal("0.20"),
            max_drawdown_pct=Decimal("0.15"),
            max_portfolio_value=Decimal("100000.00")
        ),
        active_models=[model1, model2],
        trading_schedule=TradingSchedule(
            market_open=time(9, 30),
            market_close=time(16, 0),
            data_fetch_interval_seconds=60,
            trading_days=["MON", "TUE", "WED", "THU", "FRI"]
        ),
        broker_config=BrokerConfig(
            broker_name="alpaca",
            api_key="key",
            api_secret="secret",
            base_url="https://api.alpaca.markets"
        ),
        logging_config=LoggingConfig(
            log_directory="./logs",
            log_level="DEBUG",
            rotation_policy="weekly"
        )
    )
    
    assert len(config.active_models) == 2
    assert config.active_models[0].enabled is True
    assert config.active_models[1].enabled is False
    assert config.execution_mode == ExecutionMode.LIVE
