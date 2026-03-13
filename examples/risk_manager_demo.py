"""Demo script for Risk Manager functionality"""
from decimal import Decimal
from datetime import datetime

from src.risk_manager import RiskManager
from src.config_models import RiskParameters
from src.models import (
    Position, PortfolioSnapshot, Signal, Recommendation
)


def main():
    print("=== Risk Manager Demo ===\n")
    
    # Initialize risk parameters
    risk_params = RiskParameters(
        stop_loss_pct=Decimal("0.05"),  # 5% loss threshold
        take_profit_pct=Decimal("0.10"),  # 10% profit threshold
        max_position_size_pct=Decimal("0.20"),  # 20% of portfolio max
        max_drawdown_pct=Decimal("0.15"),  # 15% drawdown limit
        max_portfolio_value=Decimal("100000.00")
    )
    
    # Create Risk Manager
    risk_manager = RiskManager(risk_params)
    print("Risk Manager initialized with parameters:")
    print(f"  Stop Loss: {risk_params.stop_loss_pct * 100}%")
    print(f"  Take Profit: {risk_params.take_profit_pct * 100}%")
    print(f"  Max Position Size: {risk_params.max_position_size_pct * 100}%")
    print(f"  Max Drawdown: {risk_params.max_drawdown_pct * 100}%")
    print(f"  Max Portfolio Value: ${risk_params.max_portfolio_value}\n")
    
    # Create sample positions
    position_with_loss = Position(
        symbol="AAPL",
        quantity=100,
        entry_price=Decimal("150.00"),
        current_price=Decimal("135.00"),  # 10% loss
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("-1500.00")
    )
    
    position_with_profit = Position(
        symbol="TSLA",
        quantity=50,
        entry_price=Decimal("200.00"),
        current_price=Decimal("240.00"),  # 20% profit
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("2000.00")
    )
    
    position_within_limits = Position(
        symbol="GOOGL",
        quantity=30,
        entry_price=Decimal("100.00"),
        current_price=Decimal("105.00"),  # 5% profit
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("150.00")
    )
    
    # Create portfolio snapshot
    portfolio = PortfolioSnapshot(
        timestamp=datetime.now(),
        positions=[position_with_loss, position_with_profit, position_within_limits],
        total_value=Decimal("50000.00"),
        cash_balance=Decimal("20000.00"),
        unrealized_pnl=Decimal("650.00"),
        realized_pnl=Decimal("0.00"),
        drawdown=Decimal("0.05")  # 5% drawdown
    )
    
    # Check individual positions
    print("=== Position Risk Checks ===\n")
    
    print(f"AAPL Position (Entry: $150, Current: $135):")
    print(f"  Stop-loss breached: {risk_manager.check_stop_loss(position_with_loss)}")
    print(f"  Take-profit reached: {risk_manager.check_take_profit(position_with_loss)}\n")
    
    print(f"TSLA Position (Entry: $200, Current: $240):")
    print(f"  Stop-loss breached: {risk_manager.check_stop_loss(position_with_profit)}")
    print(f"  Take-profit reached: {risk_manager.check_take_profit(position_with_profit)}\n")
    
    print(f"GOOGL Position (Entry: $100, Current: $105):")
    print(f"  Stop-loss breached: {risk_manager.check_stop_loss(position_within_limits)}")
    print(f"  Take-profit reached: {risk_manager.check_take_profit(position_within_limits)}\n")
    
    # Generate protective signals
    print("=== Protective Signals ===\n")
    protective_signals = risk_manager.generate_protective_signals(portfolio)
    
    if protective_signals:
        print(f"Generated {len(protective_signals)} protective signal(s):")
        for signal in protective_signals:
            print(f"  {signal.symbol}: {signal.recommendation.value.upper()} "
                  f"(Reason: {signal.metadata['reason']})")
    else:
        print("No protective signals generated - all positions within limits")
    
    print()
    
    # Check trading status
    print("=== Trading Status ===\n")
    print(f"Current drawdown: {portfolio.drawdown * 100}%")
    print(f"Trading halted: {risk_manager.is_trading_halted(portfolio)}\n")
    
    # Evaluate signals
    print("=== Signal Evaluation ===\n")
    
    buy_signal = Signal(
        symbol="MSFT",
        timestamp=datetime.now(),
        recommendation=Recommendation.BUY,
        confidence=0.85,
        model_id="test_model",
        metadata={}
    )
    
    sell_signal = Signal(
        symbol="AAPL",
        timestamp=datetime.now(),
        recommendation=Recommendation.SELL,
        confidence=0.90,
        model_id="test_model",
        metadata={}
    )
    
    buy_result = risk_manager.evaluate_signal(buy_signal, portfolio)
    print(f"BUY signal for MSFT: {'APPROVED' if buy_result.is_ok() else f'REJECTED ({buy_result.unwrap_err().value})'}")
    
    sell_result = risk_manager.evaluate_signal(sell_signal, portfolio)
    print(f"SELL signal for AAPL: {'APPROVED' if sell_result.is_ok() else f'REJECTED ({sell_result.unwrap_err().value})'}")
    
    print()
    
    # Test with high drawdown
    print("=== High Drawdown Scenario ===\n")
    high_drawdown_portfolio = PortfolioSnapshot(
        timestamp=datetime.now(),
        positions=[],
        total_value=Decimal("40000.00"),
        cash_balance=Decimal("40000.00"),
        unrealized_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        drawdown=Decimal("0.20")  # 20% drawdown (exceeds 15% limit)
    )
    
    print(f"Portfolio drawdown: {high_drawdown_portfolio.drawdown * 100}%")
    print(f"Trading halted: {risk_manager.is_trading_halted(high_drawdown_portfolio)}")
    
    buy_result_high_dd = risk_manager.evaluate_signal(buy_signal, high_drawdown_portfolio)
    print(f"BUY signal evaluation: {'APPROVED' if buy_result_high_dd.is_ok() else f'REJECTED ({buy_result_high_dd.unwrap_err().value})'}")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
