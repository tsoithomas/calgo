"""Configuration data models for Calgo trading bot"""
from dataclasses import dataclass
from datetime import time
from decimal import Decimal
from typing import Any, Dict, List

from src.models import DataSource, ExecutionMode


@dataclass
class DataSourceConfig:
    """Data source configuration with priority"""
    source: DataSource
    api_key: str
    priority: int  # Lower number = higher priority
    api_secret: str = ""  # Optional, required for some sources like Alpaca


@dataclass
class ModelConfig:
    """AI model configuration"""
    model_id: str
    model_type: str
    parameters: Dict[str, Any]
    enabled: bool


@dataclass
class TradingSchedule:
    """Market hours and trading intervals"""
    market_open: time
    market_close: time
    data_fetch_interval_seconds: int
    trading_days: List[str]  # e.g., ["MON", "TUE", "WED", "THU", "FRI"]


@dataclass
class BrokerConfig:
    """Broker API credentials and configuration"""
    broker_name: str
    api_key: str
    api_secret: str
    base_url: str


@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_directory: str
    log_level: str
    rotation_policy: str


@dataclass
class RiskParameters:
    """Risk management thresholds"""
    stop_loss_pct: Decimal  # e.g., 0.05 for 5% loss
    take_profit_pct: Decimal  # e.g., 0.10 for 10% gain
    max_position_size_pct: Decimal  # e.g., 0.20 for 20% of portfolio
    max_drawdown_pct: Decimal  # e.g., 0.15 for 15% drawdown
    max_portfolio_value: Decimal


@dataclass
class CacheConfig:
    """Cache configuration for historical price data"""
    cache_directory: str = "./cache/historical"
    max_age_days: int = 1


@dataclass
class Config:
    """Main configuration container"""
    execution_mode: ExecutionMode
    data_sources: List[DataSourceConfig]
    risk_parameters: RiskParameters
    active_models: List[ModelConfig]
    trading_schedule: TradingSchedule
    broker_config: BrokerConfig
    logging_config: LoggingConfig
    cache_config: CacheConfig = None

    def __post_init__(self):
        if self.cache_config is None:
            self.cache_config = CacheConfig()
