"""Demo script for Portfolio Manager functionality"""
from decimal import Decimal
from src.portfolio_manager import PortfolioManager


def main():
    print("=== Portfolio Manager Demo ===\n")
    
    # Initialize Portfolio Manager
    pm = PortfolioManager(
        initial_cash=Decimal("10000.00"),
        max_portfolio_value=Decimal("50000.00"),
        max_position_size_pct=Decimal("0.20")  # 20% max per position
    )
    
    print(f"Initial cash: ${pm._cash_balance}")
    print(f"Max portfolio value: ${pm._max_portfolio_value}")
    print(f"Max position size: {pm._max_position_size_pct * 100}%\n")
    
    # Add positions
    print("--- Adding Positions ---")
    result = pm.add_position("AAPL", 10, Decimal("150.00"))
    if result.is_ok():
        print(f"✓ Added AAPL position: 10 shares @ $150.00")
    
    result = pm.add_position("GOOGL", 5, Decimal("100.00"))
    if result.is_ok():
        print(f"✓ Added GOOGL position: 5 shares @ $100.00")
    
    result = pm.add_position("MSFT", 20, Decimal("50.00"))
    if result.is_ok():
        print(f"✓ Added MSFT position: 20 shares @ $50.00")
    
    print(f"\nCash balance after purchases: ${pm._cash_balance}\n")
    
    # Update prices
    print("--- Updating Prices ---")
    pm.update_position("AAPL", Decimal("155.00"))
    print(f"AAPL price updated to $155.00")
    
    pm.update_position("GOOGL", Decimal("95.00"))
    print(f"GOOGL price updated to $95.00")
    
    pm.update_position("MSFT", Decimal("52.00"))
    print(f"MSFT price updated to $52.00\n")
    
    # Show portfolio metrics
    print("--- Portfolio Metrics ---")
    print(f"Total portfolio value: ${pm.get_total_value()}")
    print(f"Unrealized P&L: ${pm.calculate_unrealized_pnl()}")
    print(f"Realized P&L: ${pm.calculate_realized_pnl()}")
    
    print("\nPosition allocations:")
    for position in pm.get_all_positions():
        allocation = pm.get_allocation(position.symbol)
        print(f"  {position.symbol}: {allocation * 100:.2f}% (${position.current_price * position.quantity})")
    
    # Close a position
    print("\n--- Closing Position ---")
    result = pm.close_position("GOOGL", Decimal("95.00"))
    if result.is_ok():
        closed = result.unwrap()
        print(f"✓ Closed GOOGL position")
        print(f"  Realized P&L: ${closed.realized_pnl}")
    
    print(f"\nCash balance after sale: ${pm._cash_balance}")
    
    # Get portfolio snapshot
    print("\n--- Portfolio Snapshot ---")
    snapshot = pm.get_snapshot()
    print(f"Timestamp: {snapshot.timestamp}")
    print(f"Total value: ${snapshot.total_value}")
    print(f"Cash balance: ${snapshot.cash_balance}")
    print(f"Unrealized P&L: ${snapshot.unrealized_pnl}")
    print(f"Realized P&L: ${snapshot.realized_pnl}")
    print(f"Drawdown: {snapshot.drawdown * 100:.2f}%")
    print(f"Open positions: {len(snapshot.positions)}")
    
    # Test limits
    print("\n--- Testing Limits ---")
    
    # Position size limit
    within_limit = pm.check_position_limit("TSLA", 50, Decimal("200.00"))
    print(f"Position of 50 TSLA @ $200 within limit: {within_limit}")
    
    # Portfolio value limit
    within_limit = pm.check_portfolio_limit(Decimal("45000.00"))
    print(f"Portfolio value of $45,000 within limit: {within_limit}")
    
    within_limit = pm.check_portfolio_limit(Decimal("55000.00"))
    print(f"Portfolio value of $55,000 within limit: {within_limit}")


if __name__ == "__main__":
    main()
