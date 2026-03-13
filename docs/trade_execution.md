# Trade Execution System

## Overview

The Trade Execution system provides an abstracted interface for executing trades through different broker APIs. It enables seamless switching between paper trading (simulation) and live trading with minimal code changes.

## Architecture

### Components

1. **BrokerAdapter (Interface)** - Abstract base class defining the broker API contract
2. **PaperBrokerAdapter** - Paper trading implementation with simulated order execution
3. **LiveBrokerAdapter** - Live trading stub for production broker integration
4. **TradeExecutor** - Core execution logic that routes orders to appropriate broker

### Design Pattern

The system uses the **Strategy Pattern** where:
- `BrokerAdapter` is the strategy interface
- `PaperBrokerAdapter` and `LiveBrokerAdapter` are concrete strategies
- `TradeExecutor` is the context that uses the strategy

This enables runtime switching between execution modes without changing client code.

## Components

### BrokerAdapter (Abstract Base Class)

**Location:** `src/broker_adapter.py`

**Purpose:** Defines the interface that all broker implementations must follow.

**Methods:**
- `place_order(symbol, quantity, action, order_type)` - Place an order with the broker
- `cancel_order(order_id)` - Cancel a pending order
- `get_order_status(order_id)` - Get current status of an order

**Returns:** All methods return `Result[T, OrderError]` for explicit error handling.

### PaperBrokerAdapter

**Location:** `src/paper_broker_adapter.py`

**Purpose:** Simulates order execution for paper trading without real money.

**Features:**
- Immediate order fills with mock prices
- Cash balance tracking
- Order history tracking
- Deterministic mock pricing based on symbol hash
- Validation of order parameters
- Insufficient funds checking

**Mock Pricing:**
Mock prices are generated deterministically based on symbol hash:
```python
hash_val = sum(ord(c) for c in symbol)
base_price = 50 + (hash_val % 200)  # Price between $50-$250
cents = (hash_val % 100) / 100
price = base_price + cents
```

This ensures consistent prices for the same symbol across multiple orders.

**Limitations:**
- Orders fill immediately (no pending state)
- Cannot cancel orders (already filled)
- Does not fetch real market prices
- Does not validate against actual market conditions

### LiveBrokerAdapter (Stub)

**Location:** `src/live_broker_adapter.py`

**Purpose:** Provides structure for live broker API integration (not yet implemented).

**Current State:** Stub implementation that returns "not implemented" errors.

**To Implement:**
1. Add authentication with broker API credentials
2. Implement actual API calls for order placement
3. Add real-time order status tracking
4. Implement proper error handling for API failures
5. Add rate limiting and retry logic
6. Map broker-specific status codes to internal OrderStatus enum

**Example Integration (Alpaca):**
```python
# TODO: Implement
response = self._client.submit_order(
    symbol=symbol,
    qty=quantity,
    side=action.value,
    type=order_type.lower(),
    time_in_force='day'
)

confirmation = OrderConfirmation(
    order_id=response.id,
    symbol=response.symbol,
    quantity=response.filled_qty,
    execution_price=Decimal(str(response.filled_avg_price)),
    timestamp=response.filled_at,
    status=self._map_broker_status(response.status)
)
```

### TradeExecutor

**Location:** `src/trade_executor.py`

**Purpose:** Routes orders to appropriate broker adapter based on execution mode.

**Features:**
- Order validation before submission
- Unified interface for all execution modes
- Comprehensive error handling
- Order status tracking
- Execution mode management

**Validation:**
- Symbol cannot be empty
- Quantity must be positive
- LIMIT orders must have valid limit_price
- All parameters must be valid before submission

**Error Handling:**
- Validates orders before broker submission
- Catches and wraps unexpected exceptions
- Logs order failures (placeholder for Logger integration)
- Returns descriptive error messages

## Usage

### Paper Trading Example

```python
from decimal import Decimal
from src.trade_executor import TradeExecutor
from src.paper_broker_adapter import PaperBrokerAdapter
from src.models import Order, OrderAction, OrderType, ExecutionMode

# Initialize paper broker with starting cash
paper_adapter = PaperBrokerAdapter(initial_cash=Decimal("100000.00"))

# Create executor in simulation mode
executor = TradeExecutor(ExecutionMode.SIMULATION, paper_adapter)

# Create and submit order
order = Order(
    symbol="AAPL",
    quantity=10,
    action=OrderAction.BUY,
    order_type=OrderType.MARKET
)

result = executor.submit_order(order)

if result.is_ok():
    confirmation = result.unwrap()
    print(f"Order filled: {confirmation.order_id}")
    print(f"Execution price: ${confirmation.execution_price}")
else:
    error = result.unwrap_err()
    print(f"Order failed: {error.message}")
```

### Live Trading Example (Stub)

```python
from src.live_broker_adapter import LiveBrokerAdapter

# Initialize live broker (stub)
live_adapter = LiveBrokerAdapter(
    api_key="your_api_key",
    api_secret="your_api_secret",
    base_url="https://paper-api.alpaca.markets",
    broker_name="alpaca_live"
)

# Create executor in live mode
executor = TradeExecutor(ExecutionMode.LIVE, live_adapter)

# Submit order (will return "not implemented" error)
result = executor.submit_order(order)
```

### Switching Execution Modes

```python
# Easy switching between modes
if config.execution_mode == ExecutionMode.SIMULATION:
    adapter = PaperBrokerAdapter(initial_cash=config.initial_cash)
else:
    adapter = LiveBrokerAdapter(
        api_key=config.broker_config.api_key,
        api_secret=config.broker_config.api_secret,
        base_url=config.broker_config.base_url
    )

executor = TradeExecutor(config.execution_mode, adapter)
```

## Error Handling

### OrderError

All broker operations return `Result[T, OrderError]` for explicit error handling.

**OrderError Structure:**
```python
class OrderError(Exception):
    message: str  # Human-readable error message
    order_details: dict  # Additional context about the error
```

**Common Errors:**
- Invalid symbol (empty or whitespace)
- Invalid quantity (zero or negative)
- Insufficient funds (paper trading)
- Missing limit_price (LIMIT orders)
- Invalid limit_price (zero or negative)
- Order not found (cancellation)
- Not implemented (live trading stub)

### Error Handling Pattern

```python
result = executor.submit_order(order)

if result.is_ok():
    confirmation = result.unwrap()
    # Handle success
else:
    error = result.unwrap_err()
    # Handle error
    print(f"Error: {error.message}")
    if error.order_details:
        print(f"Details: {error.order_details}")
```

## Testing

### Unit Tests

**Location:** `tests/test_broker_adapter.py`, `tests/test_trade_executor.py`

**Coverage:**
- Order placement (BUY/SELL)
- Order validation
- Cash balance tracking
- Order status checking
- Order cancellation
- Error conditions
- Execution mode switching

**Test Statistics:**
- 37 total tests
- 19 broker adapter tests
- 18 trade executor tests
- 100% pass rate

### Running Tests

```bash
# Run all trade execution tests
python -m pytest tests/test_broker_adapter.py tests/test_trade_executor.py -v

# Run specific test class
python -m pytest tests/test_broker_adapter.py::TestPaperBrokerAdapter -v

# Run with coverage
python -m pytest tests/test_broker_adapter.py tests/test_trade_executor.py --cov=src --cov-report=html
```

## Demo

**Location:** `examples/trade_executor_demo.py`

**Demonstrates:**
1. Paper trading with successful orders
2. Error handling (insufficient funds, invalid orders)
3. LIMIT orders with limit prices
4. Order history tracking
5. Live trading stub behavior
6. Execution mode comparison

**Run Demo:**
```bash
python examples/trade_executor_demo.py
```

## Requirements Validation

### Requirement 4.1: Execution Mode Support
✓ TradeExecutor supports SIMULATION and LIVE execution modes

### Requirement 4.2: Paper Trading Adapter
✓ PaperBrokerAdapter simulates order execution with mock fills

### Requirement 4.3: Live Trading Adapter (Stub)
✓ LiveBrokerAdapter provides structure for live broker integration

### Requirement 4.4: Broker Adapter Interface
✓ BrokerAdapter abstract class defines place_order(), cancel_order(), get_order_status()

### Requirement 4.5: Broker Abstraction
✓ BrokerAdapter interface isolates broker-specific implementation details

### Requirement 4.6: Order Confirmation
✓ submit_order() returns OrderConfirmation with order_id, execution_price, timestamp

### Requirement 4.7: Order Failure Handling
✓ Failed orders return descriptive OrderError with message and details

## Future Enhancements

### Live Broker Integration
1. Implement Alpaca Live API integration
2. Add Interactive Brokers support
3. Implement order status polling
4. Add webhook support for order updates
5. Implement rate limiting and retry logic

### Advanced Order Types
1. Stop-loss orders
2. Take-profit orders
3. Trailing stop orders
4. Bracket orders
5. One-cancels-other (OCO) orders

### Risk Management Integration
1. Pre-trade risk checks
2. Position size validation
3. Portfolio limit enforcement
4. Real-time margin checking

### Performance Optimization
1. Batch order submission
2. Async order execution
3. Connection pooling
4. Order queue management

### Monitoring and Observability
1. Order execution metrics
2. Latency tracking
3. Error rate monitoring
4. Broker API health checks

## Related Documentation

- [Configuration Guide](configuration.md) - System configuration
- [Data Sources](data_sources.md) - Market data integration
- [Design Document](../.kiro/specs/calgo/design.md) - Complete system design
- [Requirements](../.kiro/specs/calgo/requirements.md) - System requirements
