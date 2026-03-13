# Configuration Manager

The Configuration Manager is responsible for loading, validating, and providing access to the Calgo trading bot configuration.

## Features

- **Multiple Format Support**: Load configuration from JSON or YAML files
- **Comprehensive Validation**: Validates all required fields and parameter ranges
- **Descriptive Errors**: Provides clear error messages when configuration is invalid
- **Type-Safe Access**: Provides typed getter methods for all configuration sections

## Usage

### Loading Configuration

```python
from src.config_manager import ConfigurationManager
from src.config_models import Config, RiskParameters, TradingSchedule
from src.models import ExecutionMode
from datetime import time
from decimal import Decimal

# Create initial dummy config
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

# Load configuration from file
result = manager.load_config("config/config.json")

if result.is_ok():
    config = result.unwrap()
    manager = ConfigurationManager(config)
    print("Configuration loaded successfully!")
else:
    error = result.unwrap_err()
    print(f"Error: {error}")
```

### Accessing Configuration

```python
# Get execution mode
mode = manager.get_execution_mode()

# Get data sources
data_sources = manager.get_data_sources()

# Get risk parameters
risk_params = manager.get_risk_params()

# Get active models
models = manager.get_active_models()

# Get trading schedule
schedule = manager.get_trading_schedule()

# Get broker configuration
broker = manager.get_broker_config()

# Get logging configuration
logging = manager.get_logging_config()
```

## Configuration File Format

### JSON Example

```json
{
  "execution_mode": "simulation",
  "data_sources": [
    {
      "source": "alpaca",
      "api_key": "your_api_key",
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
      "model_id": "ma_crossover_v1",
      "model_type": "moving_average",
      "parameters": {
        "short_window": 20,
        "long_window": 50
      },
      "enabled": true
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
    "api_key": "broker_api_key",
    "api_secret": "broker_api_secret",
    "base_url": "https://paper-api.alpaca.markets"
  },
  "logging_config": {
    "log_directory": "./logs",
    "log_level": "INFO",
    "rotation_policy": "daily"
  }
}
```

### YAML Example

```yaml
execution_mode: simulation

data_sources:
  - source: alpaca
    api_key: your_api_key
    priority: 1

risk_parameters:
  stop_loss_pct: 0.05
  take_profit_pct: 0.10
  max_position_size_pct: 0.20
  max_drawdown_pct: 0.15
  max_portfolio_value: 100000.00

active_models:
  - model_id: ma_crossover_v1
    model_type: moving_average
    parameters:
      short_window: 20
      long_window: 50
    enabled: true

trading_schedule:
  market_open: "09:30"
  market_close: "16:00"
  data_fetch_interval_seconds: 300
  trading_days:
    - MON
    - TUE
    - WED
    - THU
    - FRI

broker_config:
  broker_name: alpaca
  api_key: broker_api_key
  api_secret: broker_api_secret
  base_url: https://paper-api.alpaca.markets

logging_config:
  log_directory: ./logs
  log_level: INFO
  rotation_policy: daily
```

## Validation Rules

### Execution Mode
- Must be either "simulation" or "live"

### Data Sources
- At least one data source must be configured
- Each source must have a valid source type (alpaca, yahoo_finance)
- Each source must have a non-empty api_key
- Priority must be non-negative

### Risk Parameters
- `stop_loss_pct`: Must be between 0 and 1.0 (0-100%)
- `take_profit_pct`: Must be non-negative
- `max_position_size_pct`: Must be between 0 and 1.0 (0-100%)
- `max_drawdown_pct`: Must be between 0 and 1.0 (0-100%)
- `max_portfolio_value`: Must be positive

### Trading Schedule
- `market_open` and `market_close`: Must be in "HH:MM" format
- `data_fetch_interval_seconds`: Must be positive
- `trading_days`: Must contain at least one valid day (MON, TUE, WED, THU, FRI, SAT, SUN)

### Broker Config
- All fields (broker_name, api_key, api_secret, base_url) must be non-empty

### Logging Config
- `log_directory`: Must be non-empty
- `log_level`: Must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL
- `rotation_policy`: Must be non-empty

### Models
- Each model must have a non-empty model_id and model_type
- Parameters can be any valid dictionary

## Error Handling

The Configuration Manager uses the Result type for error handling. All errors are wrapped in a `ConfigError` exception with descriptive messages indicating:

- Missing required fields
- Invalid field values
- File not found errors
- JSON/YAML parsing errors
- Validation failures with specific details

Example error messages:
- "Configuration file not found: config/missing.json"
- "Invalid execution_mode: 'invalid'. Must be 'simulation' or 'live'"
- "stop_loss_pct must be non-negative"
- "Invalid trading day: 'INVALID_DAY'. Must be one of ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']"

## Requirements Satisfied

This implementation satisfies the following requirements:

- **Requirement 9.1**: Load configuration from a configuration file at startup
- **Requirement 9.7**: Fail to start and provide descriptive error messages when configuration is invalid or incomplete

## Testing

The Configuration Manager includes comprehensive unit tests covering:

- Valid configuration loading (JSON format)
- File not found errors
- Invalid JSON format handling
- Missing required fields
- Invalid field values (negative percentages, invalid modes, etc.)
- Invalid trading days
- Invalid log levels
- Unsupported file formats
- All getter methods

Run tests with:
```bash
python -m pytest tests/test_config_manager.py -v
```
