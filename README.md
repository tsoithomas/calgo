# Calgo - AI-Driven Trading Bot

Calgo is an AI-driven autonomous trading bot designed for simulated stock and ETF trading with a modular architecture that supports future live trading with minimal modifications.

## Project Structure

```
calgo/
├── src/                    # Source code
│   ├── __init__.py
│   ├── models.py          # Core data models and enums
│   └── result.py          # Result/Option types for error handling
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_models.py     # Tests for data models
│   └── test_result.py     # Tests for Result/Option types
├── config/                 # Configuration files
├── logs/                   # Log files
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Core Data Models

### Enums
- `ExecutionMode`: SIMULATION, LIVE
- `Recommendation`: BUY, SELL, HOLD
- `OrderAction`: BUY, SELL
- `OrderType`: MARKET, LIMIT
- `OrderStatus`: PENDING, FILLED, PARTIALLY_FILLED, CANCELLED, REJECTED
- `DataSource`: YAHOO_FINANCE, ALPACA
- `RiskViolation`: STOP_LOSS_BREACHED, TAKE_PROFIT_REACHED, POSITION_SIZE_EXCEEDED, PORTFOLIO_LIMIT_EXCEEDED, DRAWDOWN_LIMIT_EXCEEDED

### Data Classes
- `PriceData`: Market price data with OHLCV
- `Signal`: Trading signal from AI model
- `Position`: Open position in portfolio
- `Order`: Order to be submitted
- `OrderConfirmation`: Order execution confirmation
- `ClosedPosition`: Closed position with realized P&L
- `PortfolioSnapshot`: Complete portfolio state
- `TradeRecord`: Record of executed trade

## Installation

```bash
pip install -r requirements.txt
```

## Running Tests

```bash
pytest tests/ -v
```

## Development Status

✅ Task 1: Project structure and core data models - COMPLETE
