"""Unit tests for Risk Manager"""
import pytest
from decimal import Decimal
from datetime import datetime

from src.risk_manager import RiskManager, RiskError
from src.config_models import RiskParameters
from src.models import (
    Position, PortfolioSnapshot, Signal, Recommendation, RiskViolation
)


@pytest.fixture
def risk_params():
    """Create standard risk parameters for testing"""
    return RiskParameters(
        stop_loss_pct=Decimal("0.05"),  # 5% loss
        take_profit_pct=Decimal("0.10"),  # 10% profit
        max_position_size_pct=Decimal("0.20"),  # 20% of portfolio
        max_drawdown_pct=Decimal("0.15"),  # 15% drawdown
        max_portfolio_value=Decimal("100000.00")
    )


@pytest.fixture
def risk_manager(risk_params):
    """Create risk manager instance"""
    return RiskManager(risk_params)


@pytest.fixture
def sample_position():
    """Create a sample position"""
    return Position(
        symbol="AAPL",
        quantity=100,
        entry_price=Decimal("150.00"),
        current_price=Decimal("150.00"),
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("0.00")
    )


@pytest.fixture
def sample_portfolio():
    """Create a sample portfolio snapshot"""
    return PortfolioSnapshot(
        timestamp=datetime.now(),
        positions=[],
        total_value=Decimal("50000.00"),
        cash_balance=Decimal("50000.00"),
        unrealized_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        drawdown=Decimal("0.00")
    )


# Task 9.1: Risk Manager initialization tests

def test_risk_manager_initialization(risk_params):
    """Test Risk Manager initializes with risk parameters"""
    manager = RiskManager(risk_params)
    assert manager is not None
    assert manager._risk_params == risk_params


# Task 9.2: Risk check methods tests

def test_check_stop_loss_not_breached(risk_manager, sample_position):
    """Test stop-loss check when position is within limits"""
    # Position at entry price - no loss
    assert not risk_manager.check_stop_loss(sample_position)
    
    # Position with small loss (3% - below 5% threshold)
    sample_position.current_price = Decimal("145.50")  # 3% loss
    assert not risk_manager.check_stop_loss(sample_position)


def test_check_stop_loss_breached(risk_manager, sample_position):
    """Test stop-loss check when threshold breached"""
    # Position with 5% loss (exactly at threshold)
    sample_position.current_price = Decimal("142.50")  # 5% loss
    assert risk_manager.check_stop_loss(sample_position)
    
    # Position with 10% loss (well beyond threshold)
    sample_position.current_price = Decimal("135.00")  # 10% loss
    assert risk_manager.check_stop_loss(sample_position)


def test_check_stop_loss_with_profit(risk_manager, sample_position):
    """Test stop-loss check when position has profit"""
    # Position with profit should not trigger stop-loss
    sample_position.current_price = Decimal("165.00")  # 10% profit
    assert not risk_manager.check_stop_loss(sample_position)


def test_check_take_profit_not_reached(risk_manager, sample_position):
    """Test take-profit check when position is below threshold"""
    # Position at entry price - no profit
    assert not risk_manager.check_take_profit(sample_position)
    
    # Position with small profit (5% - below 10% threshold)
    sample_position.current_price = Decimal("157.50")  # 5% profit
    assert not risk_manager.check_take_profit(sample_position)


def test_check_take_profit_reached(risk_manager, sample_position):
    """Test take-profit check when threshold reached"""
    # Position with 10% profit (exactly at threshold)
    sample_position.current_price = Decimal("165.00")  # 10% profit
    assert risk_manager.check_take_profit(sample_position)
    
    # Position with 20% profit (well beyond threshold)
    sample_position.current_price = Decimal("180.00")  # 20% profit
    assert risk_manager.check_take_profit(sample_position)


def test_check_take_profit_with_loss(risk_manager, sample_position):
    """Test take-profit check when position has loss"""
    # Position with loss should not trigger take-profit
    sample_position.current_price = Decimal("135.00")  # 10% loss
    assert not risk_manager.check_take_profit(sample_position)


def test_check_position_size_within_limits(risk_manager, sample_portfolio):
    """Test position size check when within limits"""
    # 10% of portfolio (below 20% limit)
    position_value = Decimal("5000.00")
    assert risk_manager.check_position_size(sample_portfolio, position_value)
    
    # Exactly at 20% limit
    position_value = Decimal("10000.00")
    assert risk_manager.check_position_size(sample_portfolio, position_value)


def test_check_position_size_exceeds_limits(risk_manager, sample_portfolio):
    """Test position size check when exceeding limits"""
    # 25% of portfolio (exceeds 20% limit)
    position_value = Decimal("12500.00")
    assert not risk_manager.check_position_size(sample_portfolio, position_value)
    
    # 50% of portfolio (well beyond limit)
    position_value = Decimal("25000.00")
    assert not risk_manager.check_position_size(sample_portfolio, position_value)


def test_check_position_size_zero_portfolio(risk_manager):
    """Test position size check with zero portfolio value"""
    portfolio = PortfolioSnapshot(
        timestamp=datetime.now(),
        positions=[],
        total_value=Decimal("0.00"),
        cash_balance=Decimal("0.00"),
        unrealized_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        drawdown=Decimal("0.00")
    )
    
    position_value = Decimal("1000.00")
    assert not risk_manager.check_position_size(portfolio, position_value)


def test_check_drawdown_within_limits(risk_manager, sample_portfolio):
    """Test drawdown check when within limits"""
    # No drawdown
    sample_portfolio.drawdown = Decimal("0.00")
    assert risk_manager.check_drawdown(sample_portfolio)
    
    # 10% drawdown (below 15% limit)
    sample_portfolio.drawdown = Decimal("0.10")
    assert risk_manager.check_drawdown(sample_portfolio)
    
    # Exactly at 15% limit
    sample_portfolio.drawdown = Decimal("0.15")
    assert risk_manager.check_drawdown(sample_portfolio)


def test_check_drawdown_exceeds_limits(risk_manager, sample_portfolio):
    """Test drawdown check when exceeding limits"""
    # 20% drawdown (exceeds 15% limit)
    sample_portfolio.drawdown = Decimal("0.20")
    assert not risk_manager.check_drawdown(sample_portfolio)
    
    # 30% drawdown (well beyond limit)
    sample_portfolio.drawdown = Decimal("0.30")
    assert not risk_manager.check_drawdown(sample_portfolio)



# Task 9.3: Signal evaluation and protective signals tests

def test_evaluate_signal_sell_always_approved(risk_manager, sample_portfolio):
    """Test that SELL signals are always approved"""
    signal = Signal(
        symbol="AAPL",
        timestamp=datetime.now(),
        recommendation=Recommendation.SELL,
        confidence=0.8,
        model_id="test_model",
        metadata={}
    )
    
    result = risk_manager.evaluate_signal(signal, sample_portfolio)
    assert result.is_ok()
    assert result.unwrap() == signal


def test_evaluate_signal_hold_always_approved(risk_manager, sample_portfolio):
    """Test that HOLD signals are always approved"""
    signal = Signal(
        symbol="AAPL",
        timestamp=datetime.now(),
        recommendation=Recommendation.HOLD,
        confidence=0.8,
        model_id="test_model",
        metadata={}
    )
    
    result = risk_manager.evaluate_signal(signal, sample_portfolio)
    assert result.is_ok()
    assert result.unwrap() == signal


def test_evaluate_signal_buy_approved(risk_manager, sample_portfolio):
    """Test BUY signal approval when all checks pass"""
    signal = Signal(
        symbol="AAPL",
        timestamp=datetime.now(),
        recommendation=Recommendation.BUY,
        confidence=0.8,
        model_id="test_model",
        metadata={}
    )
    
    result = risk_manager.evaluate_signal(signal, sample_portfolio)
    assert result.is_ok()
    assert result.unwrap() == signal


def test_evaluate_signal_buy_rejected_drawdown(risk_manager, sample_portfolio):
    """Test BUY signal rejection when drawdown exceeded"""
    # Set drawdown above limit
    sample_portfolio.drawdown = Decimal("0.20")  # 20% exceeds 15% limit
    
    signal = Signal(
        symbol="AAPL",
        timestamp=datetime.now(),
        recommendation=Recommendation.BUY,
        confidence=0.8,
        model_id="test_model",
        metadata={}
    )
    
    result = risk_manager.evaluate_signal(signal, sample_portfolio)
    assert result.is_err()
    assert result.unwrap_err() == RiskViolation.DRAWDOWN_LIMIT_EXCEEDED


def test_evaluate_signal_buy_rejected_portfolio_limit(risk_manager, sample_portfolio):
    """Test BUY signal rejection when portfolio value at limit"""
    # Set portfolio value at max limit
    sample_portfolio.total_value = Decimal("100000.00")
    
    signal = Signal(
        symbol="AAPL",
        timestamp=datetime.now(),
        recommendation=Recommendation.BUY,
        confidence=0.8,
        model_id="test_model",
        metadata={}
    )
    
    result = risk_manager.evaluate_signal(signal, sample_portfolio)
    assert result.is_err()
    assert result.unwrap_err() == RiskViolation.PORTFOLIO_LIMIT_EXCEEDED


def test_generate_protective_signals_empty_portfolio(risk_manager, sample_portfolio):
    """Test protective signal generation with no positions"""
    signals = risk_manager.generate_protective_signals(sample_portfolio)
    assert len(signals) == 0


def test_generate_protective_signals_stop_loss(risk_manager, sample_portfolio):
    """Test protective signal generation for stop-loss breach"""
    # Add position with stop-loss breach
    position = Position(
        symbol="AAPL",
        quantity=100,
        entry_price=Decimal("150.00"),
        current_price=Decimal("135.00"),  # 10% loss (exceeds 5% threshold)
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("-1500.00")
    )
    sample_portfolio.positions = [position]
    
    signals = risk_manager.generate_protective_signals(sample_portfolio)
    
    assert len(signals) == 1
    assert signals[0].symbol == "AAPL"
    assert signals[0].recommendation == Recommendation.SELL
    assert signals[0].confidence == 1.0
    assert signals[0].model_id == "risk_manager_stop_loss"
    assert signals[0].metadata["reason"] == "stop_loss_breached"


def test_generate_protective_signals_take_profit(risk_manager, sample_portfolio):
    """Test protective signal generation for take-profit reach"""
    # Add position with take-profit reach
    position = Position(
        symbol="TSLA",
        quantity=50,
        entry_price=Decimal("200.00"),
        current_price=Decimal("240.00"),  # 20% profit (exceeds 10% threshold)
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("2000.00")
    )
    sample_portfolio.positions = [position]
    
    signals = risk_manager.generate_protective_signals(sample_portfolio)
    
    assert len(signals) == 1
    assert signals[0].symbol == "TSLA"
    assert signals[0].recommendation == Recommendation.SELL
    assert signals[0].confidence == 1.0
    assert signals[0].model_id == "risk_manager_take_profit"
    assert signals[0].metadata["reason"] == "take_profit_reached"


def test_generate_protective_signals_multiple_positions(risk_manager, sample_portfolio):
    """Test protective signal generation for multiple positions"""
    # Add position with stop-loss breach
    position1 = Position(
        symbol="AAPL",
        quantity=100,
        entry_price=Decimal("150.00"),
        current_price=Decimal("135.00"),  # 10% loss
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("-1500.00")
    )
    
    # Add position with take-profit reach
    position2 = Position(
        symbol="TSLA",
        quantity=50,
        entry_price=Decimal("200.00"),
        current_price=Decimal("240.00"),  # 20% profit
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("2000.00")
    )
    
    # Add position within limits (no signal)
    position3 = Position(
        symbol="GOOGL",
        quantity=30,
        entry_price=Decimal("100.00"),
        current_price=Decimal("105.00"),  # 5% profit (below threshold)
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("150.00")
    )
    
    sample_portfolio.positions = [position1, position2, position3]
    
    signals = risk_manager.generate_protective_signals(sample_portfolio)
    
    assert len(signals) == 2
    
    # Check stop-loss signal
    stop_loss_signal = next(s for s in signals if s.symbol == "AAPL")
    assert stop_loss_signal.recommendation == Recommendation.SELL
    assert stop_loss_signal.model_id == "risk_manager_stop_loss"
    
    # Check take-profit signal
    take_profit_signal = next(s for s in signals if s.symbol == "TSLA")
    assert take_profit_signal.recommendation == Recommendation.SELL
    assert take_profit_signal.model_id == "risk_manager_take_profit"


def test_generate_protective_signals_no_breach(risk_manager, sample_portfolio):
    """Test protective signal generation when no thresholds breached"""
    # Add positions within limits
    position1 = Position(
        symbol="AAPL",
        quantity=100,
        entry_price=Decimal("150.00"),
        current_price=Decimal("153.00"),  # 2% profit
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("300.00")
    )
    
    position2 = Position(
        symbol="TSLA",
        quantity=50,
        entry_price=Decimal("200.00"),
        current_price=Decimal("197.00"),  # 1.5% loss
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("-150.00")
    )
    
    sample_portfolio.positions = [position1, position2]
    
    signals = risk_manager.generate_protective_signals(sample_portfolio)
    assert len(signals) == 0


def test_is_trading_halted_false(risk_manager, sample_portfolio):
    """Test trading halted check when drawdown within limits"""
    # No drawdown
    sample_portfolio.drawdown = Decimal("0.00")
    assert not risk_manager.is_trading_halted(sample_portfolio)
    
    # 10% drawdown (below 15% limit)
    sample_portfolio.drawdown = Decimal("0.10")
    assert not risk_manager.is_trading_halted(sample_portfolio)


def test_is_trading_halted_true(risk_manager, sample_portfolio):
    """Test trading halted check when drawdown exceeded"""
    # 20% drawdown (exceeds 15% limit)
    sample_portfolio.drawdown = Decimal("0.20")
    assert risk_manager.is_trading_halted(sample_portfolio)
    
    # 30% drawdown (well beyond limit)
    sample_portfolio.drawdown = Decimal("0.30")
    assert risk_manager.is_trading_halted(sample_portfolio)


# Edge case tests

def test_check_stop_loss_edge_case_exact_threshold(risk_manager, sample_position):
    """Test stop-loss at exact threshold boundary"""
    # Exactly 5% loss
    sample_position.current_price = Decimal("142.50")
    assert risk_manager.check_stop_loss(sample_position)


def test_check_take_profit_edge_case_exact_threshold(risk_manager, sample_position):
    """Test take-profit at exact threshold boundary"""
    # Exactly 10% profit
    sample_position.current_price = Decimal("165.00")
    assert risk_manager.check_take_profit(sample_position)


def test_protective_signals_priority_stop_loss_over_take_profit(risk_manager, sample_portfolio):
    """Test that stop-loss takes priority over take-profit (shouldn't happen but test logic)"""
    # This is a theoretical edge case - a position can't have both stop-loss and take-profit
    # But we test that the logic handles stop-loss first
    position = Position(
        symbol="AAPL",
        quantity=100,
        entry_price=Decimal("150.00"),
        current_price=Decimal("135.00"),  # Loss
        entry_timestamp=datetime.now(),
        unrealized_pnl=Decimal("-1500.00")
    )
    sample_portfolio.positions = [position]
    
    signals = risk_manager.generate_protective_signals(sample_portfolio)
    
    # Should generate stop-loss signal
    assert len(signals) == 1
    assert signals[0].model_id == "risk_manager_stop_loss"
