"""
Demo script for Trade Executor and Broker Adapters.

This script demonstrates:
1. Creating broker adapters (paper and live)
2. Initializing trade executor with different execution modes
3. Submitting orders through the executor
4. Handling order confirmations and errors
5. Checking order status
"""
from decimal import Decimal

from src.trade_executor import TradeExecutor
from src.paper_broker_adapter import PaperBrokerAdapter
from src.live_broker_adapter import LiveBrokerAdapter
from src.models import Order, OrderAction, OrderType, ExecutionMode


def demo_paper_trading():
    """Demonstrate paper trading execution"""
    print("=" * 60)
    print("PAPER TRADING DEMO")
    print("=" * 60)
    
    # Initialize paper broker adapter with starting cash
    paper_adapter = PaperBrokerAdapter(initial_cash=Decimal("100000.00"))
    
    # Create trade executor in simulation mode
    executor = TradeExecutor(ExecutionMode.SIMULATION, paper_adapter)
    
    print(f"\nExecution Mode: {executor.get_execution_mode().value}")
    print(f"Starting Cash: ${paper_adapter.get_cash_balance()}")
    
    # Example 1: Successful BUY order
    print("\n--- Example 1: BUY Order ---")
    buy_order = Order(
        symbol="AAPL",
        quantity=10,
        action=OrderAction.BUY,
        order_type=OrderType.MARKET
    )
    
    result = executor.submit_order(buy_order)
    
    if result.is_ok():
        confirmation = result.unwrap()
        print(f"✓ Order Filled!")
        print(f"  Order ID: {confirmation.order_id}")
        print(f"  Symbol: {confirmation.symbol}")
        print(f"  Quantity: {confirmation.quantity}")
        print(f"  Execution Price: ${confirmation.execution_price}")
        print(f"  Total Cost: ${confirmation.execution_price * confirmation.quantity}")
        print(f"  Status: {confirmation.status.value}")
        print(f"  Timestamp: {confirmation.timestamp}")
        
        # Check order status
        status = executor.get_order_status(confirmation.order_id)
        print(f"  Current Status: {status.value}")
    else:
        error = result.unwrap_err()
        print(f"✗ Order Failed: {error.message}")
    
    print(f"\nCash Balance After Buy: ${paper_adapter.get_cash_balance()}")
    
    # Example 2: Successful SELL order
    print("\n--- Example 2: SELL Order ---")
    sell_order = Order(
        symbol="TSLA",
        quantity=5,
        action=OrderAction.SELL,
        order_type=OrderType.MARKET
    )
    
    result = executor.submit_order(sell_order)
    
    if result.is_ok():
        confirmation = result.unwrap()
        print(f"✓ Order Filled!")
        print(f"  Order ID: {confirmation.order_id}")
        print(f"  Symbol: {confirmation.symbol}")
        print(f"  Quantity: {confirmation.quantity}")
        print(f"  Execution Price: ${confirmation.execution_price}")
        print(f"  Total Proceeds: ${confirmation.execution_price * confirmation.quantity}")
        print(f"  Status: {confirmation.status.value}")
    else:
        error = result.unwrap_err()
        print(f"✗ Order Failed: {error.message}")
    
    print(f"\nCash Balance After Sell: ${paper_adapter.get_cash_balance()}")
    
    # Example 3: Order with insufficient funds
    print("\n--- Example 3: Insufficient Funds ---")
    large_order = Order(
        symbol="GOOGL",
        quantity=10000,
        action=OrderAction.BUY,
        order_type=OrderType.MARKET
    )
    
    result = executor.submit_order(large_order)
    
    if result.is_ok():
        confirmation = result.unwrap()
        print(f"✓ Order Filled: {confirmation.order_id}")
    else:
        error = result.unwrap_err()
        print(f"✗ Order Failed: {error.message}")
        if error.order_details:
            print(f"  Details: {error.order_details}")
    
    # Example 4: Invalid order (zero quantity)
    print("\n--- Example 4: Invalid Order ---")
    invalid_order = Order(
        symbol="MSFT",
        quantity=0,
        action=OrderAction.BUY,
        order_type=OrderType.MARKET
    )
    
    result = executor.submit_order(invalid_order)
    
    if result.is_ok():
        confirmation = result.unwrap()
        print(f"✓ Order Filled: {confirmation.order_id}")
    else:
        error = result.unwrap_err()
        print(f"✗ Order Failed: {error.message}")
    
    # Example 5: LIMIT order with limit price
    print("\n--- Example 5: LIMIT Order ---")
    limit_order = Order(
        symbol="AMZN",
        quantity=3,
        action=OrderAction.BUY,
        order_type=OrderType.LIMIT,
        limit_price=Decimal("150.00")
    )
    
    result = executor.submit_order(limit_order)
    
    if result.is_ok():
        confirmation = result.unwrap()
        print(f"✓ Order Filled!")
        print(f"  Order ID: {confirmation.order_id}")
        print(f"  Limit Price: ${limit_order.limit_price}")
        print(f"  Execution Price: ${confirmation.execution_price}")
    else:
        error = result.unwrap_err()
        print(f"✗ Order Failed: {error.message}")
    
    # Show order history
    print("\n--- Order History ---")
    history = paper_adapter.get_order_history()
    print(f"Total Orders Executed: {len(history)}")
    for order_id, confirmation in history.items():
        print(f"  {order_id}: {confirmation.quantity} {confirmation.symbol} @ ${confirmation.execution_price}")
    
    print(f"\nFinal Cash Balance: ${paper_adapter.get_cash_balance()}")


def demo_live_trading():
    """Demonstrate live trading execution (stub)"""
    print("\n" + "=" * 60)
    print("LIVE TRADING DEMO (STUB)")
    print("=" * 60)
    
    # Initialize live broker adapter (stub)
    live_adapter = LiveBrokerAdapter(
        api_key="demo_api_key",
        api_secret="demo_api_secret",
        base_url="https://paper-api.alpaca.markets",
        broker_name="alpaca_live"
    )
    
    # Create trade executor in live mode
    executor = TradeExecutor(ExecutionMode.LIVE, live_adapter)
    
    print(f"\nExecution Mode: {executor.get_execution_mode().value}")
    print("Note: This is a stub implementation - no real trades will be executed")
    
    # Attempt to place order (will fail with not implemented error)
    print("\n--- Attempting Live Order ---")
    order = Order(
        symbol="AAPL",
        quantity=10,
        action=OrderAction.BUY,
        order_type=OrderType.MARKET
    )
    
    result = executor.submit_order(order)
    
    if result.is_ok():
        confirmation = result.unwrap()
        print(f"✓ Order Filled: {confirmation.order_id}")
    else:
        error = result.unwrap_err()
        print(f"✗ Order Failed: {error.message}")
        if error.order_details:
            print(f"  Details:")
            for key, value in error.order_details.items():
                print(f"    {key}: {value}")


def demo_execution_mode_comparison():
    """Compare simulation vs live execution modes"""
    print("\n" + "=" * 60)
    print("EXECUTION MODE COMPARISON")
    print("=" * 60)
    
    # Same order for both modes
    order = Order(
        symbol="AAPL",
        quantity=10,
        action=OrderAction.BUY,
        order_type=OrderType.MARKET
    )
    
    # Simulation mode
    print("\n--- Simulation Mode ---")
    paper_adapter = PaperBrokerAdapter(initial_cash=Decimal("10000.00"))
    sim_executor = TradeExecutor(ExecutionMode.SIMULATION, paper_adapter)
    
    sim_result = sim_executor.submit_order(order)
    if sim_result.is_ok():
        print(f"✓ Simulation: Order filled successfully")
        print(f"  Order ID: {sim_result.unwrap().order_id}")
    else:
        print(f"✗ Simulation: {sim_result.unwrap_err().message}")
    
    # Live mode (stub)
    print("\n--- Live Mode (Stub) ---")
    live_adapter = LiveBrokerAdapter(
        api_key="test",
        api_secret="test",
        base_url="https://api.example.com"
    )
    live_executor = TradeExecutor(ExecutionMode.LIVE, live_adapter)
    
    live_result = live_executor.submit_order(order)
    if live_result.is_ok():
        print(f"✓ Live: Order filled successfully")
    else:
        print(f"✗ Live: {live_result.unwrap_err().message}")
    
    print("\nKey Differences:")
    print("  • Simulation: Orders execute immediately with mock prices")
    print("  • Live: Requires real broker API integration (not yet implemented)")
    print("  • Both: Use same TradeExecutor interface for seamless switching")


if __name__ == "__main__":
    # Run all demos
    demo_paper_trading()
    demo_live_trading()
    demo_execution_mode_comparison()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("  1. BrokerAdapter interface enables switching between paper and live trading")
    print("  2. TradeExecutor validates orders before submission")
    print("  3. Paper trading simulates immediate fills with mock prices")
    print("  4. Live trading stub provides structure for future implementation")
    print("  5. Error handling provides descriptive messages for debugging")
