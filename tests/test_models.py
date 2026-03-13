"""Basic tests for core data models"""
from datetime import datetime
from decimal import Decimal

from src.models import (
    ExecutionMode, Recommendation, OrderAction, OrderType, OrderStatus,
    DataSource, RiskViolation, PriceData, Signal, Position, Order,
    OrderConfirmation, ClosedPosition, PortfolioSnapshot, TradeRecord
)


def test_enums_exist():
    """Test that all enums are defined"""
    assert ExecutionMode.SIMULATION.value == "simulation"
    assert ExecutionMode.LIVE.value == "live"
    
    assert Recommendation.BUY.value == "buy"
    assert Recommendation.SELL.value == "sell"
    assert Recommendation.HOLD.value == "hold"
    
    assert OrderAction.BUY.value == "buy"
    assert OrderAction.SELL.value == "sell"
    
    assert OrderType.MARKET.value == "market"
    assert OrderType.LIMIT.value == "limit"
    
    assert OrderStatus.PENDING.value == "pending"
    assert OrderStatus.FILLED.value == "filled"
    
    assert DataSource.YAHOO_FINANCE.value == "yahoo_finance"
    assert DataSource.ALPACA.value == "alpaca"
    
    assert RiskViolation.STOP_LOSS_BREACHED.value == "stop_loss_breached"


def test_price_data_creation():
    """Test PriceData dataclass creation"""
    price = PriceData(
        symbol="AAPL",
        timestamp=datetime.now(),
        open=Decimal("150.00"),
        high=Decimal("152.00"),
        low=Decimal("149.00"),
        close=Decimal("151.00"),
        volume=1000000,
        source=DataSource.YAHOO_FINANCE
    )
    assert price.symbol == "AAPL"
    assert price.close == Decimal("151.00")



def test_signal_creation():
    """Test Signal dataclass creation"""
    signal = Signal(
        symbol="AAPL",
        timestamp=datetime.now(),
        recommendation=Recommendation.BUY,
        confidence=0.85,
        model_id="test_model",
        metadata={"reason": "test"}
    )
    assert signal.symbol == "AAPL"
    assert signal.recommendation == Recommendation.BUY
    assert signal.confidence == 0.85


def test_position_creation():
    """Test Position dataclass creation"""
    position = Position(
        symbol="AAPL",
        quantity=10,
        entry_price=Decimal("150.00"),
        current_price=Decimal("151.00"),
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("10.00")
    )
    assert position.symbol == "AAPL"
    assert position.quantity == 10
    assert position.unrealized_pnl == Decimal("10.00")


def test_order_creation():
    """Test Order dataclass creation"""
    order = Order(
        symbol="AAPL",
        quantity=10,
        action=OrderAction.BUY,
        order_type=OrderType.MARKET
    )
    assert order.symbol == "AAPL"
    assert order.action == OrderAction.BUY
    assert order.limit_price is None


def test_portfolio_snapshot_creation():
    """Test PortfolioSnapshot dataclass creation"""
    snapshot = PortfolioSnapshot(
        timestamp=datetime.now(),
        positions=[],
        total_value=Decimal("10000.00"),
        cash_balance=Decimal("10000.00"),
        unrealized_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        drawdown=Decimal("0.00")
    )
    assert snapshot.total_value == Decimal("10000.00")
    assert len(snapshot.positions) == 0
