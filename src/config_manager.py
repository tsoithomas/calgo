"""Configuration Manager for Calgo trading bot"""
import json
from pathlib import Path
from typing import Dict, Any
from decimal import Decimal

from src.config_models import (
    Config, DataSourceConfig, ModelConfig, TradingSchedule,
    BrokerConfig, LoggingConfig, RiskParameters, CacheConfig
)
from src.models import DataSource, ExecutionMode
from src.result import Result
from datetime import time


class ConfigError(Exception):
    """Configuration error"""
    pass


class ConfigurationManager:
    """Manages configuration loading, validation, and access"""
    
    def __init__(self, config: Config):
        self._config = config
    
    def load_config(self, file_path: str) -> Result[Config, ConfigError]:
        """Load configuration from JSON or YAML file
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Result containing Config object or ConfigError
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return Result.err(ConfigError(f"Configuration file not found: {file_path}"))
            
            # Read file content
            with open(path, 'r') as f:
                content = f.read()
            
            # Parse based on file extension
            if path.suffix.lower() == '.json':
                data = json.loads(content)
            elif path.suffix.lower() in ['.yaml', '.yml']:
                try:
                    import yaml
                    data = yaml.safe_load(content)
                except ImportError:
                    return Result.err(ConfigError("PyYAML not installed. Install with: pip install pyyaml"))
            else:
                return Result.err(ConfigError(f"Unsupported file format: {path.suffix}. Use .json or .yaml"))
            
            # Parse configuration
            config = self._parse_config(data)
            
            # Validate configuration
            return self.validate_config(config)
            
        except json.JSONDecodeError as e:
            return Result.err(ConfigError(f"Invalid JSON format: {str(e)}"))
        except Exception as e:
            return Result.err(ConfigError(f"Failed to load configuration: {str(e)}"))
    
    def _parse_config(self, data: Dict[str, Any]) -> Config:
        """Parse configuration dictionary into Config object
        
        Args:
            data: Configuration dictionary
            
        Returns:
            Config object
            
        Raises:
            ConfigError: If required fields are missing or invalid
        """
        # Parse execution mode
        execution_mode_str = data.get('execution_mode')
        if not execution_mode_str:
            raise ConfigError("Missing required field: 'execution_mode'")
        
        try:
            execution_mode = ExecutionMode(execution_mode_str)
        except ValueError:
            raise ConfigError(f"Invalid execution_mode: '{execution_mode_str}'. Must be 'simulation' or 'live'")
        
        # Parse data sources
        data_sources_data = data.get('data_sources')
        if not data_sources_data:
            raise ConfigError("Missing required field: 'data_sources'")
        if not isinstance(data_sources_data, list) or len(data_sources_data) == 0:
            raise ConfigError("'data_sources' must be a non-empty list")
        
        data_sources = []
        for idx, ds in enumerate(data_sources_data):
            try:
                source = DataSource(ds.get('source'))
            except (ValueError, AttributeError):
                raise ConfigError(f"Invalid data source at index {idx}: '{ds.get('source')}'")
            
            if 'api_key' not in ds:
                raise ConfigError(f"Missing 'api_key' for data source at index {idx}")
            if 'priority' not in ds:
                raise ConfigError(f"Missing 'priority' for data source at index {idx}")
            
            data_sources.append(DataSourceConfig(
                source=source,
                api_key=ds['api_key'],
                priority=ds['priority'],
                api_secret=ds.get('api_secret', '')  # Optional, defaults to empty string
            ))
        
        # Parse risk parameters
        risk_data = data.get('risk_parameters')
        if not risk_data:
            raise ConfigError("Missing required field: 'risk_parameters'")
        
        required_risk_fields = ['stop_loss_pct', 'take_profit_pct', 'max_position_size_pct', 
                                'max_drawdown_pct', 'max_portfolio_value']
        for field in required_risk_fields:
            if field not in risk_data:
                raise ConfigError(f"Missing required field in risk_parameters: '{field}'")
        
        risk_parameters = RiskParameters(
            stop_loss_pct=Decimal(str(risk_data['stop_loss_pct'])),
            take_profit_pct=Decimal(str(risk_data['take_profit_pct'])),
            max_position_size_pct=Decimal(str(risk_data['max_position_size_pct'])),
            max_drawdown_pct=Decimal(str(risk_data['max_drawdown_pct'])),
            max_portfolio_value=Decimal(str(risk_data['max_portfolio_value']))
        )
        
        # Parse active models
        models_data = data.get('active_models')
        if models_data is None:
            raise ConfigError("Missing required field: 'active_models'")
        if not isinstance(models_data, list):
            raise ConfigError("'active_models' must be a list")
        
        active_models = []
        for idx, model in enumerate(models_data):
            required_model_fields = ['model_id', 'model_type', 'parameters', 'enabled']
            for field in required_model_fields:
                if field not in model:
                    raise ConfigError(f"Missing required field '{field}' in active_models at index {idx}")
            
            active_models.append(ModelConfig(
                model_id=model['model_id'],
                model_type=model['model_type'],
                parameters=model['parameters'],
                enabled=model['enabled']
            ))
        
        # Parse trading schedule
        schedule_data = data.get('trading_schedule')
        if not schedule_data:
            raise ConfigError("Missing required field: 'trading_schedule'")
        
        required_schedule_fields = ['market_open', 'market_close', 'data_fetch_interval_seconds', 'trading_days']
        for field in required_schedule_fields:
            if field not in schedule_data:
                raise ConfigError(f"Missing required field in trading_schedule: '{field}'")
        
        # Parse time strings (format: "HH:MM")
        try:
            market_open_parts = schedule_data['market_open'].split(':')
            market_open = time(int(market_open_parts[0]), int(market_open_parts[1]))
        except (ValueError, IndexError, AttributeError):
            raise ConfigError(f"Invalid market_open format: '{schedule_data.get('market_open')}'. Use 'HH:MM'")
        
        try:
            market_close_parts = schedule_data['market_close'].split(':')
            market_close = time(int(market_close_parts[0]), int(market_close_parts[1]))
        except (ValueError, IndexError, AttributeError):
            raise ConfigError(f"Invalid market_close format: '{schedule_data.get('market_close')}'. Use 'HH:MM'")
        
        trading_schedule = TradingSchedule(
            market_open=market_open,
            market_close=market_close,
            data_fetch_interval_seconds=schedule_data['data_fetch_interval_seconds'],
            trading_days=schedule_data['trading_days']
        )
        
        # Parse broker config
        broker_data = data.get('broker_config')
        if not broker_data:
            raise ConfigError("Missing required field: 'broker_config'")
        
        required_broker_fields = ['broker_name', 'api_key', 'api_secret', 'base_url']
        for field in required_broker_fields:
            if field not in broker_data:
                raise ConfigError(f"Missing required field in broker_config: '{field}'")
        
        broker_config = BrokerConfig(
            broker_name=broker_data['broker_name'],
            api_key=broker_data['api_key'],
            api_secret=broker_data['api_secret'],
            base_url=broker_data['base_url']
        )
        
        # Parse logging config
        logging_data = data.get('logging_config')
        if not logging_data:
            raise ConfigError("Missing required field: 'logging_config'")
        
        required_logging_fields = ['log_directory', 'log_level', 'rotation_policy']
        for field in required_logging_fields:
            if field not in logging_data:
                raise ConfigError(f"Missing required field in logging_config: '{field}'")
        
        logging_config = LoggingConfig(
            log_directory=logging_data['log_directory'],
            log_level=logging_data['log_level'],
            rotation_policy=logging_data['rotation_policy']
        )
        
        # Parse optional cache config
        cache_data = data.get('cache_config')
        if cache_data:
            cache_config = CacheConfig(
                cache_directory=cache_data.get('cache_directory', './cache/historical'),
                max_age_days=cache_data.get('max_age_days', 1)
            )
        else:
            cache_config = CacheConfig()

        return Config(
            execution_mode=execution_mode,
            data_sources=data_sources,
            risk_parameters=risk_parameters,
            active_models=active_models,
            trading_schedule=trading_schedule,
            broker_config=broker_config,
            logging_config=logging_config,
            cache_config=cache_config
        )
    
    def validate_config(self, config: Config) -> Result[Config, ConfigError]:
        """Validate configuration parameters
        
        Args:
            config: Configuration object to validate
            
        Returns:
            Result containing validated Config or ConfigError
        """
        errors = []
        
        # Validate risk parameters
        if config.risk_parameters.stop_loss_pct < 0:
            errors.append("stop_loss_pct must be non-negative")
        if config.risk_parameters.stop_loss_pct > 1:
            errors.append("stop_loss_pct must be <= 1.0 (100%)")
        
        if config.risk_parameters.take_profit_pct < 0:
            errors.append("take_profit_pct must be non-negative")
        
        if config.risk_parameters.max_position_size_pct <= 0:
            errors.append("max_position_size_pct must be positive")
        if config.risk_parameters.max_position_size_pct > 1:
            errors.append("max_position_size_pct must be <= 1.0 (100%)")
        
        if config.risk_parameters.max_drawdown_pct < 0:
            errors.append("max_drawdown_pct must be non-negative")
        if config.risk_parameters.max_drawdown_pct > 1:
            errors.append("max_drawdown_pct must be <= 1.0 (100%)")
        
        if config.risk_parameters.max_portfolio_value <= 0:
            errors.append("max_portfolio_value must be positive")
        
        # Validate data sources
        if not config.data_sources:
            errors.append("At least one data source must be configured")
        
        for idx, ds in enumerate(config.data_sources):
            if ds.priority < 0:
                errors.append(f"Data source at index {idx} has negative priority")
            if not ds.api_key or ds.api_key.strip() == "":
                errors.append(f"Data source at index {idx} has empty api_key")
        
        # Validate trading schedule
        if config.trading_schedule.data_fetch_interval_seconds <= 0:
            errors.append("data_fetch_interval_seconds must be positive")
        
        if not config.trading_schedule.trading_days:
            errors.append("trading_days must contain at least one day")
        
        valid_days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        for day in config.trading_schedule.trading_days:
            if day not in valid_days:
                errors.append(f"Invalid trading day: '{day}'. Must be one of {valid_days}")
        
        # Validate broker config
        if not config.broker_config.broker_name or config.broker_config.broker_name.strip() == "":
            errors.append("broker_name cannot be empty")
        if not config.broker_config.api_key or config.broker_config.api_key.strip() == "":
            errors.append("broker api_key cannot be empty")
        if not config.broker_config.api_secret or config.broker_config.api_secret.strip() == "":
            errors.append("broker api_secret cannot be empty")
        if not config.broker_config.base_url or config.broker_config.base_url.strip() == "":
            errors.append("broker base_url cannot be empty")
        
        # Validate logging config
        if not config.logging_config.log_directory or config.logging_config.log_directory.strip() == "":
            errors.append("log_directory cannot be empty")
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.logging_config.log_level not in valid_log_levels:
            errors.append(f"Invalid log_level: '{config.logging_config.log_level}'. Must be one of {valid_log_levels}")
        
        # Validate models
        for idx, model in enumerate(config.active_models):
            if not model.model_id or model.model_id.strip() == "":
                errors.append(f"Model at index {idx} has empty model_id")
            if not model.model_type or model.model_type.strip() == "":
                errors.append(f"Model at index {idx} has empty model_type")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
            return Result.err(ConfigError(error_msg))
        
        return Result.ok(config)
    
    # Getter methods
    def get_execution_mode(self) -> ExecutionMode:
        """Get execution mode"""
        return self._config.execution_mode
    
    def get_data_sources(self) -> list[DataSourceConfig]:
        """Get data sources"""
        return self._config.data_sources
    
    def get_risk_params(self) -> RiskParameters:
        """Get risk parameters"""
        return self._config.risk_parameters
    
    def get_active_models(self) -> list[ModelConfig]:
        """Get active models"""
        return self._config.active_models
    
    def get_trading_schedule(self) -> TradingSchedule:
        """Get trading schedule"""
        return self._config.trading_schedule
    
    def get_broker_config(self) -> BrokerConfig:
        """Get broker configuration"""
        return self._config.broker_config
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration"""
        return self._config.logging_config

    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration, returning defaults when absent"""
        return self._config.cache_config
