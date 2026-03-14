"""Unit tests for Configuration Manager"""
import json
import tempfile
from pathlib import Path
from decimal import Decimal
from datetime import time

import pytest

from src.config_manager import ConfigurationManager, ConfigError
from src.config_models import Config, DataSourceConfig, RiskParameters, TradingSchedule
from src.models import DataSource, ExecutionMode


def create_valid_config_dict():
    """Create a valid configuration dictionary for testing"""
    return {
        "execution_mode": "simulation",
        "data_sources": [
            {
                "source": "alpaca",
                "api_key": "test_key",
                "priority": 1
            }
        ],
        "risk_parameters": {
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10,
            "max_position_size_pct": 0.20,
            "max_drawdown_pct": 0.15,
            "max_portfolio_value": 100000.00
        },
        "active_models": [
            {
                "model_id": "test_model",
                "model_type": "moving_average",
                "parameters": {"window": 20},
                "enabled": True
            }
        ],
        "trading_schedule": {
            "market_open": "09:30",
            "market_close": "16:00",
            "data_fetch_interval_seconds": 300,
            "trading_days": ["MON", "TUE", "WED", "THU", "FRI"]
        },
        "broker_config": {
            "broker_name": "alpaca",
            "api_key": "broker_key",
            "api_secret": "broker_secret",
            "base_url": "https://paper-api.alpaca.markets"
        },
        "logging_config": {
            "log_directory": "./logs",
            "log_level": "INFO",
            "rotation_policy": "daily"
        }
    }


def test_load_valid_json_config():
    """Test loading a valid JSON configuration file"""
    config_dict = create_valid_config_dict()
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        # Create a dummy config for initialization
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )
        
        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        
        assert result.is_ok()
        config = result.unwrap()
        assert config.execution_mode == ExecutionMode.SIMULATION
        assert len(config.data_sources) == 1
        assert config.data_sources[0].source == DataSource.ALPACA
        assert config.risk_parameters.stop_loss_pct == Decimal("0.05")
    finally:
        Path(temp_path).unlink()


def test_load_config_file_not_found():
    """Test loading a non-existent configuration file"""
    dummy_config = Config(
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
        broker_config=None,
        logging_config=None
    )
    
    manager = ConfigurationManager(dummy_config)
    result = manager.load_config("nonexistent_file.json")
    
    assert result.is_err()
    error = result.unwrap_err()
    assert "not found" in str(error)


def test_load_config_invalid_json():
    """Test loading a malformed JSON file"""
    # Create temporary file with invalid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{invalid json content")
        temp_path = f.name
    
    try:
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )
        
        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid JSON" in str(error)
    finally:
        Path(temp_path).unlink()


def test_validate_config_missing_execution_mode():
    """Test validation fails when execution_mode is missing"""
    config_dict = create_valid_config_dict()
    del config_dict['execution_mode']
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )
        
        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "execution_mode" in str(error)
    finally:
        Path(temp_path).unlink()


def test_validate_config_invalid_execution_mode():
    """Test validation fails with invalid execution_mode value"""
    config_dict = create_valid_config_dict()
    config_dict['execution_mode'] = "invalid_mode"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )
        
        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid execution_mode" in str(error)
    finally:
        Path(temp_path).unlink()


def test_validate_config_negative_stop_loss():
    """Test validation fails with negative stop_loss_pct"""
    config_dict = create_valid_config_dict()
    config_dict['risk_parameters']['stop_loss_pct'] = -0.05
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )
        
        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "stop_loss_pct must be non-negative" in str(error)
    finally:
        Path(temp_path).unlink()


def test_validate_config_invalid_position_size():
    """Test validation fails with invalid max_position_size_pct"""
    config_dict = create_valid_config_dict()
    config_dict['risk_parameters']['max_position_size_pct'] = 1.5  # > 100%
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )
        
        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "max_position_size_pct must be <= 1.0" in str(error)
    finally:
        Path(temp_path).unlink()


def test_validate_config_negative_portfolio_value():
    """Test validation fails with negative max_portfolio_value"""
    config_dict = create_valid_config_dict()
    config_dict['risk_parameters']['max_portfolio_value'] = -1000
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )
        
        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "max_portfolio_value must be positive" in str(error)
    finally:
        Path(temp_path).unlink()


def test_validate_config_invalid_trading_day():
    """Test validation fails with invalid trading day"""
    config_dict = create_valid_config_dict()
    config_dict['trading_schedule']['trading_days'] = ["MON", "INVALID_DAY"]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )
        
        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid trading day" in str(error)
    finally:
        Path(temp_path).unlink()


def test_validate_config_invalid_log_level():
    """Test validation fails with invalid log level"""
    config_dict = create_valid_config_dict()
    config_dict['logging_config']['log_level'] = "INVALID_LEVEL"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )
        
        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid log_level" in str(error)
    finally:
        Path(temp_path).unlink()


def test_getter_methods():
    """Test all getter methods return correct values"""
    config_dict = create_valid_config_dict()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )
        
        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        
        assert result.is_ok()
        config = result.unwrap()
        
        # Update manager with loaded config
        manager = ConfigurationManager(config)
        
        # Test getters
        assert manager.get_execution_mode() == ExecutionMode.SIMULATION
        assert len(manager.get_data_sources()) == 1
        assert manager.get_data_sources()[0].source == DataSource.ALPACA
        assert manager.get_risk_params().stop_loss_pct == Decimal("0.05")
        assert len(manager.get_active_models()) == 1
        assert manager.get_active_models()[0].model_id == "test_model"
        assert manager.get_trading_schedule().market_open == time(9, 30)
        assert manager.get_broker_config().broker_name == "alpaca"
        assert manager.get_logging_config().log_level == "INFO"
    finally:
        Path(temp_path).unlink()


def test_unsupported_file_format():
    """Test loading a file with unsupported format"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("some content")
        temp_path = f.name
    
    try:
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )
        
        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Unsupported file format" in str(error)
    finally:
        Path(temp_path).unlink()


def test_get_cache_config_returns_defaults_when_absent():
    """Test get_cache_config() returns CacheConfig defaults when cache_config is absent from config"""
    config_dict = create_valid_config_dict()
    # Ensure no cache_config key
    config_dict.pop('cache_config', None)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name

    try:
        from src.config_models import CacheConfig
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )

        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        assert result.is_ok()
        manager = ConfigurationManager(result.unwrap())

        cache_cfg = manager.get_cache_config()
        assert isinstance(cache_cfg, CacheConfig)
        assert cache_cfg.cache_directory == "./cache/historical"
        assert cache_cfg.max_age_days == 1
    finally:
        Path(temp_path).unlink()


def test_get_cache_config_reads_values_from_config():
    """Test get_cache_config() returns values from cache_config section when present"""
    config_dict = create_valid_config_dict()
    config_dict['cache_config'] = {
        "cache_directory": "/tmp/my_cache",
        "max_age_days": 3
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name

    try:
        from src.config_models import CacheConfig
        dummy_config = Config(
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
            broker_config=None,
            logging_config=None
        )

        manager = ConfigurationManager(dummy_config)
        result = manager.load_config(temp_path)
        assert result.is_ok()
        manager = ConfigurationManager(result.unwrap())

        cache_cfg = manager.get_cache_config()
        assert cache_cfg.cache_directory == "/tmp/my_cache"
        assert cache_cfg.max_age_days == 3
    finally:
        Path(temp_path).unlink()
