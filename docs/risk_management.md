# Risk Management

The Risk Manager enforces risk management rules and generates protective signals to protect the portfolio from excessive losses.

## Overview

The Risk Manager is responsible for:
- Validating trading signals against risk parameters
- Monitoring positions for stop-loss and take-profit thresholds
- Enforcing position sizing limits
- Tracking portfolio drawdown
- Generating protective sell signals when thresholds are breached
- Halting trading when maximum drawdown is exceeded

## Risk Parameters

Risk parameters are configured in the main configuration file:

```python
from src.config_models import RiskParameters
from decimal import Decimal

risk_params = RiskParameters(
    stop_loss_pct=Decimal("0.05"),          # 5% loss threshold
    take_profit_pct=Decimal("0.10"),        # 10% profit threshold
    max_position_size_pct=Decimal("0.20"),  # 20% of portfolio max
    max_drawdown_pct=Decimal("0.15"),       # 15% drawdown limit
    max_portfolio_value=Decimal("100000.00") # Maximum portfolio value
)
```

### Parameter Descriptions

- **stop_loss_pct**: Maximum loss percentage before triggering a protective sell signal (e.g., 0.05 = 5%)
- **take_profit_pct**: Profit percentage at which to trigger a protective sell signal (e.g., 0.10 = 10%)
- **max_position_size_pct**: Maximum position size as percentage of total portfolio value (e.g., 0.20 = 20%)
- **max_drawdown_pct**: Maximum portfolio drawdown before halting all new buy orders (e.g., 0.15 = 15%)
- **max_portfolio_value**: Maximum total portfolio value allowed

## Usage

### Initialize Risk Manager

```python
from src.risk_manager import RiskManager
from src.config_models import RiskParameters

# Create risk parameters
risk_params = RiskParameters(
    stop_loss_pct=Decimal("0.05"),
    take_profit_pct=Decimal("0.10"),
    max_position_size_pct=Decimal("0.20"),
    max_drawdown_pct=Decimal("0.15"),
    max_portfolio_value=Decimal("100000.00")
)

# Initialize Risk Manager
risk_manager = RiskManager(risk_params)
```

### Check Individual Positions

```python
# Check if position has breached stop-loss
if risk_manager.check_stop_loss(position):
    print(f"Stop-loss breached for {position.symbol}")

# Check if position has reached take-profit
if risk_manager.check_take_profit(position):
    print(f"Take-profit reached for {position.symbol}")
```

### Evaluate Trading Signals

```python
# Evaluate a signal before executing
result = risk_manager.evaluate_signal(signal, portfolio)

if result.is_ok():
    # Signal approved - proceed with execution
    approved_signal = result.unwrap()
else:
    # Signal rejected - get violation reason
    violation = result.unwrap_err()
    print(f"Signal rejected: {violation.value}")
```

### Generate Protective Signals

```python
# Generate protective sell signals for positions breaching thresholds
protective_signals = risk_manager.generate_protective_signals(portfolio)

for signal in protective_signals:
    print(f"Protective signal: {signal.symbol} - {signal.recommendation.value}")
    print(f"Reason: {signal.metadata['reason']}")
```

### Check Trading Status

```python
# Check if trading should be halted due to drawdown
if risk_manager.is_trading_halted(portfolio):
    print("Trading halted - maximum drawdown exceeded")
    # Do not execute any new buy orders
```

## Risk Check Methods

### check_stop_loss(position)

Checks if a position has breached the stop-loss threshold.

**Parameters:**
- `position`: Position to check

**Returns:**
- `True` if loss exceeds threshold (should sell)
- `False` if within limits

**Calculation:**
```
loss_pct = (current_price - entry_price) / entry_price
breached = loss_pct <= -stop_loss_pct
```

### check_take_profit(position)

Checks if a position has reached the take-profit threshold.

**Parameters:**
- `position`: Position to check

**Returns:**
- `True` if profit exceeds threshold (should sell)
- `False` if below threshold

**Calculation:**
```
profit_pct = (current_price - entry_price) / entry_price
reached = profit_pct >= take_profit_pct
```

### check_position_size(portfolio, position_value)

Validates position size against maximum percentage of portfolio.

**Parameters:**
- `portfolio`: Current portfolio snapshot
- `position_value`: Value of position to check

**Returns:**
- `True` if within limits
- `False` if exceeds max_position_size_pct

### check_drawdown(portfolio)

Checks if current drawdown exceeds maximum threshold.

**Parameters:**
- `portfolio`: Current portfolio snapshot

**Returns:**
- `True` if drawdown is within limits
- `False` if exceeds max_drawdown_pct

## Signal Evaluation

The `evaluate_signal()` method validates signals against risk parameters:

1. **SELL and HOLD signals**: Always approved (don't add risk)
2. **BUY signals**: Checked against:
   - Drawdown limit (reject if exceeded)
   - Portfolio value limit (reject if at max)
   - Position size limit (simplified check)

**Return Value:**
- `Result.ok(signal)`: Signal approved
- `Result.err(RiskViolation)`: Signal rejected with reason

**Risk Violations:**
- `DRAWDOWN_LIMIT_EXCEEDED`: Portfolio drawdown exceeds max_drawdown_pct
- `PORTFOLIO_LIMIT_EXCEEDED`: Portfolio value at or above max_portfolio_value
- `POSITION_SIZE_EXCEEDED`: Position size would exceed max_position_size_pct

## Protective Signals

Protective signals are automatically generated for positions that breach thresholds:

### Stop-Loss Signals

Generated when a position's loss exceeds `stop_loss_pct`:
- **Recommendation**: SELL
- **Confidence**: 1.0 (maximum)
- **Model ID**: "risk_manager_stop_loss"
- **Metadata**: Includes entry price, current price, unrealized P&L, loss percentage

### Take-Profit Signals

Generated when a position's profit exceeds `take_profit_pct`:
- **Recommendation**: SELL
- **Confidence**: 1.0 (maximum)
- **Model ID**: "risk_manager_take_profit"
- **Metadata**: Includes entry price, current price, unrealized P&L, profit percentage

## Trading Halt

When portfolio drawdown exceeds `max_drawdown_pct`:
- `is_trading_halted()` returns `True`
- All new BUY signals are rejected with `DRAWDOWN_LIMIT_EXCEEDED`
- Existing positions can still be closed (SELL signals approved)
- Trading resumes when drawdown falls below threshold

## Integration with Trading System

The Risk Manager integrates with other components:

1. **Signal Generator**: Generates trading signals
2. **Risk Manager**: Evaluates and filters signals
3. **Trade Executor**: Executes approved signals
4. **Portfolio Manager**: Tracks positions and calculates metrics

**Typical Workflow:**
```python
# 1. Generate signal
signal = signal_generator.generate_signal(market_data, portfolio)

# 2. Evaluate signal with Risk Manager
result = risk_manager.evaluate_signal(signal, portfolio)

if result.is_ok():
    # 3. Execute approved signal
    trade_executor.submit_order(order)
else:
    # Log rejection reason
    print(f"Signal rejected: {result.unwrap_err().value}")

# 4. Generate protective signals
protective_signals = risk_manager.generate_protective_signals(portfolio)

# 5. Execute protective signals immediately
for signal in protective_signals:
    # Convert to order and execute
    pass
```

## Example

See `examples/risk_manager_demo.py` for a complete working example demonstrating all Risk Manager functionality.

## Testing

Comprehensive unit tests are available in `tests/test_risk_manager.py` covering:
- Risk parameter initialization
- Stop-loss and take-profit checks
- Position size validation
- Drawdown monitoring
- Signal evaluation
- Protective signal generation
- Trading halt logic
- Edge cases and boundary conditions
