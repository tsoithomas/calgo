# Calgo - AI-Driven Trading Bot

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██████╗ █████╗ ██╗      ██████╗  ██████╗               ║
║  ██╔════╝██╔══██╗██║     ██╔════╝ ██╔═══██╗              ║
║  ██║     ███████║██║     ██║  ███╗██║   ██║              ║
║  ██║     ██╔══██║██║     ██║   ██║██║   ██║              ║
║  ╚██████╗██║  ██║███████╗╚██████╔╝╚██████╔╝              ║
║   ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝               ║
║                                                           ║
║         AI-Driven Autonomous Trading Bot                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

Calgo is an AI-driven autonomous trading bot designed for simulated stock and ETF trading with a modular architecture that supports future live trading with minimal modifications. The system operates continuously during market hours, fetching market data, generating AI-powered trading signals, managing portfolio positions, executing trades through abstracted broker APIs, and enforcing comprehensive risk management controls.

## Features

- **AI-Driven Signal Generation**: Multiple AI models (Moving Average Crossover, ML Classifiers) with configurable aggregation strategies
- **Comprehensive Risk Management**: Stop-loss, take-profit, position sizing, and drawdown limits
- **Modular Architecture**: Easy to extend with new models, data sources, and brokers
- **Dual Execution Modes**: Seamless switching between paper trading (simulation) and live trading
- **Automatic Failover**: Multi-source market data with automatic failover and retry logic
- **Complete Observability**: Detailed logging, analytics, and performance metrics
- **State Machine**: Robust system lifecycle management (INITIALIZING → READY → RUNNING → HALTED → SHUTDOWN)

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd calgo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your trading bot:
```bash
cp config/config.example.json config/config.json
# Edit config/config.json with your API keys and preferences
```

### Running the Bot

**Simulation Mode (Paper Trading):**
```bash
python main.py --config config/config.json --symbols AAPL MSFT GOOGL
```

**Live Trading Mode (USE WITH CAUTION):**
```bash
python main.py --config config/config.live.json --symbols SPY --mode live
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_calgo_system.py -v
```


## Project Structure

```
calgo/
├── src/                           # Source code
│   ├── __init__.py
│   ├── calgo_system.py           # Main system orchestrator and state machine
│   ├── models.py                 # Core data models and enums
│   ├── result.py                 # Result/Option types for error handling
│   ├── config_manager.py         # Configuration loading and validation
│   ├── config_models.py          # Configuration data models
│   ├── market_data_ingester.py   # Market data fetching with failover
│   ├── data_sources.py           # Data source adapters (Yahoo, Alpaca)
│   ├── signal_generator.py       # AI signal generation and aggregation
│   ├── trading_models.py         # Trading model implementations
│   ├── portfolio_manager.py      # Position tracking and portfolio metrics
│   ├── trade_executor.py         # Order execution abstraction
│   ├── broker_adapter.py         # Broker API interface
│   ├── paper_broker_adapter.py   # Paper trading implementation
│   ├── live_broker_adapter.py    # Live trading implementation (stub)
│   ├── risk_manager.py           # Risk management and protective signals
│   ├── logger.py                 # Comprehensive logging system
│   └── analytics_engine.py       # Performance metrics and visualizations
├── tests/                         # Comprehensive test suite (288 tests)
│   ├── test_calgo_system.py      # State machine tests
│   ├── test_config_manager.py    # Configuration tests
│   ├── test_market_data_ingester.py
│   ├── test_signal_generator.py
│   ├── test_portfolio_manager.py
│   ├── test_trade_executor.py
│   ├── test_risk_manager.py
│   ├── test_logger.py
│   ├── test_analytics_engine.py
│   └── ...
├── config/                        # Configuration files
│   ├── config.example.json       # Example simulation config
│   ├── config.example.yaml       # Example YAML config
│   └── test_config.json          # Test configuration
├── logs/                          # Log files (auto-generated)
│   ├── trades/                   # Trade execution logs
│   ├── portfolio/                # Portfolio state snapshots
│   ├── signals/                  # Generated signals
│   └── errors/                   # Error logs
├── docs/                          # Documentation
│   ├── configuration.md          # Configuration guide
│   ├── data_sources.md           # Data source setup
│   ├── risk_management.md        # Risk management guide
│   └── trade_execution.md        # Trade execution guide
├── examples/                      # Example scripts and demos
├── main.py                        # Main entry point and CLI
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Calgo System Core                       │
│                   (State Machine & Orchestration)           │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│   Market     │      │   Signal     │     │  Portfolio   │
│    Data      │─────▶│  Generator   │────▶│   Manager    │
│  Ingester    │      │              │     │              │
└──────────────┘      └──────────────┘     └──────────────┘
        │                     │                     │
        │                     ▼                     │
        │             ┌──────────────┐             │
        │             │     Risk     │             │
        │             │   Manager    │             │
        │             └──────────────┘             │
        │                     │                     │
        │                     ▼                     │
        │             ┌──────────────┐             │
        │             │    Trade     │             │
        └────────────▶│   Executor   │◀────────────┘
                      └──────────────┘
                              │
                      ┌───────┴───────┐
                      ▼               ▼
              ┌──────────────┐ ┌──────────────┐
              │    Logger    │ │  Analytics   │
              │              │ │   Engine     │
              └──────────────┘ └──────────────┘
```

### State Machine

```
INITIALIZING ──▶ READY ──▶ RUNNING ──▶ HALTED ──▶ SHUTDOWN
                   ▲          │
                   └──────────┘
```


## Configuration

### Example Configuration (config.json)

```json
{
  "execution_mode": "simulation",
  "data_sources": [
    {
      "source": "yahoo_finance",
      "api_key": "YOUR_API_KEY",
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
      "model_type": "moving_average_crossover",
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
    "data_fetch_interval_seconds": 60,
    "trading_days": ["MON", "TUE", "WED", "THU", "FRI"]
  },
  "broker_config": {
    "broker_name": "alpaca",
    "api_key": "YOUR_BROKER_API_KEY",
    "api_secret": "YOUR_BROKER_API_SECRET",
    "base_url": "https://paper-api.alpaca.markets"
  },
  "logging_config": {
    "log_directory": "logs",
    "log_level": "INFO",
    "rotation_policy": "daily"
  }
}
```

See `docs/configuration.md` for detailed configuration options.

## Core Components

### 1. Market Data Ingester
- Fetches historical and real-time price data
- Supports multiple data sources (Yahoo Finance, Alpaca)
- Automatic failover with exponential backoff retry
- Data validation and normalization

### 2. Signal Generator
- Supports multiple AI trading models
- Configurable signal aggregation (voting, weighted average, ensemble)
- Runtime model management (add/remove/activate models)
- Built-in models: Moving Average Crossover, ML Classifier

### 3. Portfolio Manager
- Tracks open and closed positions
- Calculates realized and unrealized P&L
- Enforces position and portfolio size limits
- Provides portfolio snapshots and allocation metrics

### 4. Risk Manager
- Stop-loss and take-profit enforcement
- Position sizing validation
- Drawdown monitoring and trading halt
- Generates protective sell signals
- Operates identically in simulation and live modes

### 5. Trade Executor
- Abstracts broker API interactions
- Supports simulation (paper trading) and live modes
- Order validation and error handling
- Returns detailed order confirmations

### 6. Logger
- Records all trades, signals, and portfolio changes
- JSON-based structured logging
- Date-based log organization
- Supports log retrieval by date range

### 7. Analytics Engine
- Performance metrics (cumulative returns, Sharpe ratio, max drawdown)
- Per-model performance tracking
- P&L and allocation visualizations
- Historical data analysis


## Usage Examples

### Basic Usage

```python
from src.calgo_system import CalgoSystem

# Initialize system
system = CalgoSystem()
result = system.initialize("config/config.json")

if result.is_ok():
    # Start trading
    system.start_trading(["AAPL", "MSFT", "GOOGL"])
    
    # Shutdown when done
    system.shutdown()
```

### CLI Usage

```bash
# Run with default configuration
python main.py --config config/config.json --symbols AAPL MSFT

# Override execution mode
python main.py --config config/config.json --symbols SPY --mode simulation

# Run without banner
python main.py --config config/config.json --symbols TSLA --no-banner
```

### Adding Custom Trading Models

```python
from src.signal_generator import TradingModel
from src.models import Signal, Recommendation

class MyCustomModel(TradingModel):
    def predict(self, market_data, portfolio_state):
        # Your trading logic here
        return Signal(
            symbol=market_data.symbol,
            timestamp=market_data.timestamp,
            recommendation=Recommendation.BUY,
            confidence=0.85,
            model_id=self.get_model_id(),
            metadata={}
        )
    
    def get_model_id(self):
        return "my_custom_model_v1"

# Add to signal generator
signal_generator.add_model(MyCustomModel())
signal_generator.set_active_models(["my_custom_model_v1"])
```

## Risk Management

Calgo includes comprehensive risk management controls:

- **Stop-Loss**: Automatically sells positions when losses exceed threshold (default: 5%)
- **Take-Profit**: Automatically sells positions when profits exceed threshold (default: 10%)
- **Position Sizing**: Limits individual position size as percentage of portfolio (default: 20%)
- **Drawdown Protection**: Halts new buy orders when drawdown exceeds limit (default: 15%)
- **Portfolio Limits**: Enforces maximum portfolio value

All risk parameters are configurable in `config.json`.

## Testing

The project includes 288 comprehensive unit tests covering all components:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific component tests
pytest tests/test_risk_manager.py -v
pytest tests/test_portfolio_manager.py -v
pytest tests/test_signal_generator.py -v

# Run tests matching pattern
pytest tests/ -k "test_state_machine" -v
```

Test coverage includes:
- State machine transitions
- Configuration validation
- Market data failover and retry logic
- Signal generation and aggregation
- Portfolio calculations and limits
- Risk management enforcement
- Trade execution flows
- Logging and serialization
- Analytics calculations


## Data Models

### Core Enums
- `ExecutionMode`: SIMULATION, LIVE
- `Recommendation`: BUY, SELL, HOLD
- `OrderAction`: BUY, SELL
- `OrderType`: MARKET, LIMIT
- `OrderStatus`: PENDING, FILLED, PARTIALLY_FILLED, CANCELLED, REJECTED
- `DataSource`: YAHOO_FINANCE, ALPACA
- `RiskViolation`: STOP_LOSS_BREACHED, TAKE_PROFIT_REACHED, POSITION_SIZE_EXCEEDED, PORTFOLIO_LIMIT_EXCEEDED, DRAWDOWN_LIMIT_EXCEEDED
- `SystemState`: INITIALIZING, READY, RUNNING, HALTED, SHUTDOWN

### Data Classes
- `PriceData`: Market price data with OHLCV
- `Signal`: Trading signal from AI model with confidence
- `Position`: Open position with unrealized P&L
- `Order`: Order to be submitted to broker
- `OrderConfirmation`: Order execution confirmation
- `ClosedPosition`: Closed position with realized P&L
- `PortfolioSnapshot`: Complete portfolio state at a point in time
- `TradeRecord`: Record of executed trade

## Logging

Calgo maintains comprehensive logs organized by type and date:

```
logs/
├── trades/
│   └── 2024-01-15.json       # All trades executed on this date
├── portfolio/
│   └── 2024-01-15.json       # Portfolio snapshots
├── signals/
│   └── 2024-01-15.json       # Generated signals
└── errors/
    └── 2024-01-15.json       # System errors and warnings
```

Each log entry includes:
- Timestamp (ISO 8601 format)
- All relevant fields for the event type
- Metadata for debugging and analysis

## Performance Analytics

The Analytics Engine provides:

- **Cumulative Returns**: Total return over time period
- **Sharpe Ratio**: Risk-adjusted return metric
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Per-Model Performance**: Independent metrics for each trading model
- **Visualizations**: P&L charts and allocation pie charts

```python
from src.analytics_engine import AnalyticsEngine
from datetime import datetime, timedelta

analytics = AnalyticsEngine(logger)

# Calculate metrics
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

returns = analytics.calculate_cumulative_returns(start_date, end_date)
sharpe = analytics.calculate_sharpe_ratio(start_date, end_date)
drawdown = analytics.calculate_max_drawdown(start_date, end_date)

# Generate visualizations
analytics.generate_pnl_chart(start_date, end_date)
analytics.generate_allocation_chart(datetime.now())
```

## Development

### Project Status

✅ All core components implemented and tested (288 tests passing)
✅ State machine and system orchestration
✅ Configuration management
✅ Market data ingestion with failover
✅ Signal generation and aggregation
✅ Portfolio management
✅ Trade execution abstraction
✅ Risk management
✅ Logging and analytics
✅ CLI and main entry point

### Adding New Features

1. **New Trading Model**: Extend `TradingModel` class in `src/trading_models.py`
2. **New Data Source**: Implement `DataSourceAdapter` interface in `src/data_sources.py`
3. **New Broker**: Implement `BrokerAdapter` interface in a new adapter file
4. **New Risk Rule**: Add methods to `RiskManager` in `src/risk_manager.py`

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Write docstrings for all public methods
- Maintain test coverage above 80%


## Dependencies

Core dependencies (see `requirements.txt` for full list):
- `pytest`: Testing framework
- `hypothesis`: Property-based testing
- `requests`: HTTP client for API calls
- `matplotlib`: Visualization and charting
- `pyyaml`: YAML configuration support (optional)

## Documentation

Detailed documentation is available in the `docs/` directory:

- `configuration.md`: Complete configuration guide
- `data_sources.md`: Setting up data sources and API keys
- `risk_management.md`: Risk management strategies and parameters
- `trade_execution.md`: Trade execution and broker integration

## Safety and Disclaimers

⚠️ **IMPORTANT DISCLAIMERS**:

1. **Paper Trading First**: Always test thoroughly in simulation mode before considering live trading
2. **No Guarantees**: This software is provided as-is with no guarantees of profitability
3. **Financial Risk**: Trading involves substantial risk of loss. Never trade with money you cannot afford to lose
4. **Not Financial Advice**: This software is for educational and research purposes only
5. **Your Responsibility**: You are solely responsible for your trading decisions and outcomes
6. **API Keys**: Keep your API keys and secrets secure. Never commit them to version control
7. **Live Trading**: The live trading adapter is a stub and requires proper implementation before use

## Troubleshooting

### Common Issues

**Configuration errors:**
```bash
# Validate your configuration
python -c "from src.config_manager import ConfigurationManager; cm = ConfigurationManager(None); result = cm.load_config('config/config.json'); print('Valid!' if result.is_ok() else result.unwrap_err())"
```

**Import errors:**
```bash
# Ensure you're in the project root and dependencies are installed
pip install -r requirements.txt
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Test failures:**
```bash
# Run tests with verbose output
pytest tests/ -v --tb=short

# Run specific failing test
pytest tests/test_calgo_system.py::TestCalgoSystemStateMachine::test_initial_state_is_initializing -v
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest tests/ -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is provided for educational and research purposes. See LICENSE file for details.

## Acknowledgments

- Built with Python 3.13+
- Designed following clean architecture principles
- Implements formal correctness properties for reliability
- Inspired by quantitative trading best practices

## Contact

For questions, issues, or contributions, please open an issue on the repository.

---

**Remember**: Past performance does not guarantee future results. Always practice responsible trading and risk management.
