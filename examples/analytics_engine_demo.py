"""Demo script for Analytics Engine"""
from datetime import datetime, timedelta
from decimal import Decimal

from src.analytics_engine import AnalyticsEngine
from src.logger import Logger
from src.models import (
    PortfolioSnapshot, Position, TradeRecord, Signal,
    OrderAction, Recommendation
)


def main():
    """Demonstrate Analytics Engine functionality"""
    
    # Initialize Logger and Analytics Engine
    logger = Logger(log_directory="logs")
    analytics = AnalyticsEngine(logger)
    
    print("=" * 60)
    print("Analytics Engine Demo")
    print("=" * 60)
    
    # Create sample portfolio history
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    portfolio_history = []
    
    print("\n1. Creating sample portfolio history...")
    for i in range(10):
        # Simulate portfolio growth with some volatility
        value = 100000 + i * 2000 + (i % 3) * 1000
        snapshot = PortfolioSnapshot(
            timestamp=base_time + timedelta(days=i),
            positions=[],
            total_value=Decimal(str(value)),
            cash_balance=Decimal(str(value)),
            unrealized_pnl=Decimal("0.00"),
            realized_pnl=Decimal(str(value - 100000)),
            drawdown=Decimal("0.00")
        )
        portfolio_history.append(snapshot)
        logger.log_portfolio_change(snapshot)
    
    print(f"   Created {len(portfolio_history)} portfolio snapshots")
    
    # Calculate performance metrics
    print("\n2. Calculating performance metrics...")
    
    cumulative_return = analytics.calculate_cumulative_returns(portfolio_history)
    print(f"   Cumulative Return: {cumulative_return:.2%}")
    
    sharpe_ratio = analytics.calculate_sharpe_ratio(portfolio_history)
    print(f"   Sharpe Ratio: {sharpe_ratio:.4f}")
    
    max_drawdown = analytics.calculate_max_drawdown(portfolio_history)
    print(f"   Max Drawdown: {max_drawdown:.2%}")
    
    # Log some signals and trades for model performance
    print("\n3. Logging signals and trades...")
    
    signals = [
        Signal(
            symbol="AAPL",
            timestamp=base_time,
            recommendation=Recommendation.BUY,
            confidence=0.85,
            model_id="momentum_model",
            metadata={"indicator": "RSI"}
        ),
        Signal(
            symbol="GOOGL",
            timestamp=base_time + timedelta(hours=1),
            recommendation=Recommendation.BUY,
            confidence=0.78,
            model_id="ml_model",
            metadata={"prediction": "bullish"}
        ),
        Signal(
            symbol="AAPL",
            timestamp=base_time + timedelta(hours=2),
            recommendation=Recommendation.SELL,
            confidence=0.82,
            model_id="momentum_model",
            metadata={"indicator": "MACD"}
        )
    ]
    
    for signal in signals:
        logger.log_signal(signal)
    
    print(f"   Logged {len(signals)} signals")
    
    # Get model performance
    print("\n4. Calculating model performance...")
    
    model_metrics = analytics.get_model_performance(
        start_date=base_time - timedelta(hours=1),
        end_date=base_time + timedelta(days=1)
    )
    
    for model_id, metrics in model_metrics.items():
        print(f"\n   Model: {model_id}")
        print(f"      Total Signals: {metrics.total_signals}")
        print(f"      Profitable Signals: {metrics.profitable_signals}")
        print(f"      Win Rate: {metrics.win_rate:.2%}")
        print(f"      Average Return: {metrics.average_return:.4f}")
        print(f"      Sharpe Ratio: {metrics.sharpe_ratio:.4f}")
    
    # Generate visualizations
    print("\n5. Generating visualizations...")
    
    pnl_chart_path = "logs/pnl_chart.png"
    analytics.generate_pnl_chart(portfolio_history, pnl_chart_path)
    print(f"   P&L chart saved to: {pnl_chart_path}")
    
    # Create a snapshot with positions for allocation chart
    current_snapshot = PortfolioSnapshot(
        timestamp=datetime.now(),
        positions=[
            Position(
                symbol="AAPL",
                quantity=100,
                entry_price=Decimal("150.00"),
                current_price=Decimal("155.00"),
                entry_timestamp=base_time,
                unrealized_pnl=Decimal("500.00")
            ),
            Position(
                symbol="GOOGL",
                quantity=50,
                entry_price=Decimal("2800.00"),
                current_price=Decimal("2850.00"),
                entry_timestamp=base_time,
                unrealized_pnl=Decimal("2500.00")
            )
        ],
        total_value=Decimal("200000.00"),
        cash_balance=Decimal("30000.00"),
        unrealized_pnl=Decimal("3000.00"),
        realized_pnl=Decimal("20000.00"),
        drawdown=Decimal("0.00")
    )
    
    allocation_chart_path = "logs/allocation_chart.png"
    analytics.generate_allocation_chart(current_snapshot, allocation_chart_path)
    print(f"   Allocation chart saved to: {allocation_chart_path}")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
