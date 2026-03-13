"""Unit tests for Analytics Engine"""
import os
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

from src.analytics_engine import AnalyticsEngine, ModelMetrics
from src.logger import Logger
from src.models import (
    PortfolioSnapshot, Position, TradeRecord, Signal,
    OrderAction, Recommendation
)


@pytest.fixture
def temp_log_dir():
    """Create temporary log directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def logger(temp_log_dir):
    """Create Logger instance with temp directory"""
    return Logger(log_directory=temp_log_dir)


@pytest.fixture
def analytics_engine(logger):
    """Create AnalyticsEngine instance"""
    return AnalyticsEngine(logger)


@pytest.fixture
def sample_portfolio_history():
    """Create sample portfolio history for testing"""
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    
    return [
        PortfolioSnapshot(
            timestamp=base_time,
            positions=[],
            total_value=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
            unrealized_pnl=Decimal("0.00"),
            realized_pnl=Decimal("0.00"),
            drawdown=Decimal("0.00")
        ),
        PortfolioSnapshot(
            timestamp=base_time + timedelta(days=1),
            positions=[],
            total_value=Decimal("105000.00"),
            cash_balance=Decimal("105000.00"),
            unrealized_pnl=Decimal("0.00"),
            realized_pnl=Decimal("5000.00"),
            drawdown=Decimal("0.00")
        ),
        PortfolioSnapshot(
            timestamp=base_time + timedelta(days=2),
            positions=[],
            total_value=Decimal("103000.00"),
            cash_balance=Decimal("103000.00"),
            unrealized_pnl=Decimal("0.00"),
            realized_pnl=Decimal("3000.00"),
            drawdown=Decimal("0.019")
        ),
        PortfolioSnapshot(
            timestamp=base_time + timedelta(days=3),
            positions=[],
            total_value=Decimal("110000.00"),
            cash_balance=Decimal("110000.00"),
            unrealized_pnl=Decimal("0.00"),
            realized_pnl=Decimal("10000.00"),
            drawdown=Decimal("0.00")
        )
    ]


class TestCalculateCumulativeReturns:
    """Tests for calculate_cumulative_returns"""
    
    def test_positive_returns(self, analytics_engine, sample_portfolio_history):
        """Test calculation with positive returns"""
        cumulative_return = analytics_engine.calculate_cumulative_returns(
            sample_portfolio_history
        )
        
        # (110000 - 100000) / 100000 = 0.10
        assert cumulative_return == pytest.approx(0.10, rel=1e-6)
    
    def test_negative_returns(self, analytics_engine):
        """Test calculation with negative returns"""
        portfolio_history = [
            PortfolioSnapshot(
                timestamp=datetime(2024, 1, 1),
                positions=[],
                total_value=Decimal("100000.00"),
                cash_balance=Decimal("100000.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("0.00"),
                drawdown=Decimal("0.00")
            ),
            PortfolioSnapshot(
                timestamp=datetime(2024, 1, 2),
                positions=[],
                total_value=Decimal("90000.00"),
                cash_balance=Decimal("90000.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("-10000.00"),
                drawdown=Decimal("0.10")
            )
        ]
        
        cumulative_return = analytics_engine.calculate_cumulative_returns(
            portfolio_history
        )
        
        # (90000 - 100000) / 100000 = -0.10
        assert cumulative_return == pytest.approx(-0.10, rel=1e-6)
    
    def test_empty_history(self, analytics_engine):
        """Test with empty portfolio history"""
        cumulative_return = analytics_engine.calculate_cumulative_returns([])
        assert cumulative_return == 0.0
    
    def test_single_snapshot(self, analytics_engine):
        """Test with single snapshot"""
        portfolio_history = [
            PortfolioSnapshot(
                timestamp=datetime(2024, 1, 1),
                positions=[],
                total_value=Decimal("100000.00"),
                cash_balance=Decimal("100000.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("0.00"),
                drawdown=Decimal("0.00")
            )
        ]
        
        cumulative_return = analytics_engine.calculate_cumulative_returns(
            portfolio_history
        )
        assert cumulative_return == 0.0
    
    def test_zero_initial_value(self, analytics_engine):
        """Test with zero initial value"""
        portfolio_history = [
            PortfolioSnapshot(
                timestamp=datetime(2024, 1, 1),
                positions=[],
                total_value=Decimal("0.00"),
                cash_balance=Decimal("0.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("0.00"),
                drawdown=Decimal("0.00")
            ),
            PortfolioSnapshot(
                timestamp=datetime(2024, 1, 2),
                positions=[],
                total_value=Decimal("10000.00"),
                cash_balance=Decimal("10000.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("0.00"),
                drawdown=Decimal("0.00")
            )
        ]
        
        cumulative_return = analytics_engine.calculate_cumulative_returns(
            portfolio_history
        )
        assert cumulative_return == 0.0


class TestCalculateSharpeRatio:
    """Tests for calculate_sharpe_ratio"""
    
    def test_positive_sharpe(self, analytics_engine, sample_portfolio_history):
        """Test Sharpe ratio calculation with positive returns"""
        sharpe = analytics_engine.calculate_sharpe_ratio(sample_portfolio_history)
        
        # Should be positive for generally increasing portfolio
        assert sharpe > 0
    
    def test_consistent_returns(self, analytics_engine):
        """Test with consistent positive returns"""
        base_time = datetime(2024, 1, 1)
        portfolio_history = [
            PortfolioSnapshot(
                timestamp=base_time + timedelta(days=i),
                positions=[],
                total_value=Decimal(str(100000 + i * 1000)),
                cash_balance=Decimal(str(100000 + i * 1000)),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal(str(i * 1000)),
                drawdown=Decimal("0.00")
            )
            for i in range(10)
        ]
        
        sharpe = analytics_engine.calculate_sharpe_ratio(portfolio_history)
        
        # Consistent returns should have high Sharpe ratio
        assert sharpe > 0
    
    def test_volatile_returns(self, analytics_engine):
        """Test with volatile returns"""
        base_time = datetime(2024, 1, 1)
        values = [100000, 110000, 95000, 115000, 90000, 120000]
        
        portfolio_history = [
            PortfolioSnapshot(
                timestamp=base_time + timedelta(days=i),
                positions=[],
                total_value=Decimal(str(values[i])),
                cash_balance=Decimal(str(values[i])),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("0.00"),
                drawdown=Decimal("0.00")
            )
            for i in range(len(values))
        ]
        
        sharpe = analytics_engine.calculate_sharpe_ratio(portfolio_history)
        
        # Volatile returns should have lower Sharpe ratio
        # Just verify it's calculated (could be positive or negative)
        assert isinstance(sharpe, float)
    
    def test_empty_history(self, analytics_engine):
        """Test with empty portfolio history"""
        sharpe = analytics_engine.calculate_sharpe_ratio([])
        assert sharpe == 0.0
    
    def test_single_snapshot(self, analytics_engine):
        """Test with single snapshot"""
        portfolio_history = [
            PortfolioSnapshot(
                timestamp=datetime(2024, 1, 1),
                positions=[],
                total_value=Decimal("100000.00"),
                cash_balance=Decimal("100000.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("0.00"),
                drawdown=Decimal("0.00")
            )
        ]
        
        sharpe = analytics_engine.calculate_sharpe_ratio(portfolio_history)
        assert sharpe == 0.0
    
    def test_zero_volatility(self, analytics_engine):
        """Test with zero volatility (constant value)"""
        base_time = datetime(2024, 1, 1)
        portfolio_history = [
            PortfolioSnapshot(
                timestamp=base_time + timedelta(days=i),
                positions=[],
                total_value=Decimal("100000.00"),
                cash_balance=Decimal("100000.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("0.00"),
                drawdown=Decimal("0.00")
            )
            for i in range(5)
        ]
        
        sharpe = analytics_engine.calculate_sharpe_ratio(portfolio_history)
        assert sharpe == 0.0


class TestCalculateMaxDrawdown:
    """Tests for calculate_max_drawdown"""
    
    def test_drawdown_calculation(self, analytics_engine, sample_portfolio_history):
        """Test max drawdown calculation"""
        max_dd = analytics_engine.calculate_max_drawdown(sample_portfolio_history)
        
        # Peak at 105000, trough at 103000
        # Drawdown = (105000 - 103000) / 105000 = 0.01904761904761905
        assert max_dd == pytest.approx(0.019, rel=1e-2)
    
    def test_no_drawdown(self, analytics_engine):
        """Test with continuously increasing portfolio"""
        base_time = datetime(2024, 1, 1)
        portfolio_history = [
            PortfolioSnapshot(
                timestamp=base_time + timedelta(days=i),
                positions=[],
                total_value=Decimal(str(100000 + i * 1000)),
                cash_balance=Decimal(str(100000 + i * 1000)),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal(str(i * 1000)),
                drawdown=Decimal("0.00")
            )
            for i in range(5)
        ]
        
        max_dd = analytics_engine.calculate_max_drawdown(portfolio_history)
        assert max_dd == 0.0
    
    def test_large_drawdown(self, analytics_engine):
        """Test with large drawdown"""
        portfolio_history = [
            PortfolioSnapshot(
                timestamp=datetime(2024, 1, 1),
                positions=[],
                total_value=Decimal("100000.00"),
                cash_balance=Decimal("100000.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("0.00"),
                drawdown=Decimal("0.00")
            ),
            PortfolioSnapshot(
                timestamp=datetime(2024, 1, 2),
                positions=[],
                total_value=Decimal("50000.00"),
                cash_balance=Decimal("50000.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("-50000.00"),
                drawdown=Decimal("0.50")
            )
        ]
        
        max_dd = analytics_engine.calculate_max_drawdown(portfolio_history)
        assert max_dd == pytest.approx(0.50, rel=1e-6)
    
    def test_empty_history(self, analytics_engine):
        """Test with empty portfolio history"""
        max_dd = analytics_engine.calculate_max_drawdown([])
        assert max_dd == 0.0
    
    def test_recovery_after_drawdown(self, analytics_engine):
        """Test that max drawdown is preserved after recovery"""
        portfolio_history = [
            PortfolioSnapshot(
                timestamp=datetime(2024, 1, 1),
                positions=[],
                total_value=Decimal("100000.00"),
                cash_balance=Decimal("100000.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("0.00"),
                drawdown=Decimal("0.00")
            ),
            PortfolioSnapshot(
                timestamp=datetime(2024, 1, 2),
                positions=[],
                total_value=Decimal("80000.00"),
                cash_balance=Decimal("80000.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("-20000.00"),
                drawdown=Decimal("0.20")
            ),
            PortfolioSnapshot(
                timestamp=datetime(2024, 1, 3),
                positions=[],
                total_value=Decimal("110000.00"),
                cash_balance=Decimal("110000.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("10000.00"),
                drawdown=Decimal("0.00")
            )
        ]
        
        max_dd = analytics_engine.calculate_max_drawdown(portfolio_history)
        # Max drawdown should be 0.20 from the dip
        assert max_dd == pytest.approx(0.20, rel=1e-6)


class TestGetModelPerformance:
    """Tests for get_model_performance"""
    
    def test_single_model_performance(self, analytics_engine, logger):
        """Test performance calculation for single model"""
        base_time = datetime(2024, 1, 1, 9, 0, 0)
        
        # Log signals
        signals = [
            Signal(
                symbol="AAPL",
                timestamp=base_time,
                recommendation=Recommendation.BUY,
                confidence=0.8,
                model_id="model_1",
                metadata={}
            ),
            Signal(
                symbol="AAPL",
                timestamp=base_time + timedelta(minutes=30),
                recommendation=Recommendation.SELL,
                confidence=0.7,
                model_id="model_1",
                metadata={}
            )
        ]
        
        for signal in signals:
            logger.log_signal(signal)
        
        # Log trades
        trades = [
            TradeRecord(
                timestamp=base_time + timedelta(minutes=1),
                order_id="order_1",
                symbol="AAPL",
                action=OrderAction.BUY,
                quantity=100,
                execution_price=Decimal("150.00")
            ),
            TradeRecord(
                timestamp=base_time + timedelta(minutes=31),
                order_id="order_2",
                symbol="AAPL",
                action=OrderAction.SELL,
                quantity=100,
                execution_price=Decimal("155.00")
            )
        ]
        
        for trade in trades:
            logger.log_trade(trade)
        
        # Get model performance
        metrics = analytics_engine.get_model_performance(
            start_date=base_time - timedelta(hours=1),
            end_date=base_time + timedelta(hours=1)
        )
        
        assert "model_1" in metrics
        assert metrics["model_1"].total_signals == 2
        assert metrics["model_1"].model_id == "model_1"
    
    def test_multiple_models(self, analytics_engine, logger):
        """Test performance calculation for multiple models"""
        base_time = datetime(2024, 1, 1, 9, 0, 0)
        
        # Log signals from different models
        signals = [
            Signal(
                symbol="AAPL",
                timestamp=base_time,
                recommendation=Recommendation.BUY,
                confidence=0.8,
                model_id="model_1",
                metadata={}
            ),
            Signal(
                symbol="GOOGL",
                timestamp=base_time,
                recommendation=Recommendation.BUY,
                confidence=0.9,
                model_id="model_2",
                metadata={}
            )
        ]
        
        for signal in signals:
            logger.log_signal(signal)
        
        # Get model performance
        metrics = analytics_engine.get_model_performance(
            start_date=base_time - timedelta(hours=1),
            end_date=base_time + timedelta(hours=1)
        )
        
        assert len(metrics) == 2
        assert "model_1" in metrics
        assert "model_2" in metrics
        assert metrics["model_1"].total_signals == 1
        assert metrics["model_2"].total_signals == 1
    
    def test_filter_by_model_id(self, analytics_engine, logger):
        """Test filtering by specific model ID"""
        base_time = datetime(2024, 1, 1, 9, 0, 0)
        
        # Log signals from different models
        signals = [
            Signal(
                symbol="AAPL",
                timestamp=base_time,
                recommendation=Recommendation.BUY,
                confidence=0.8,
                model_id="model_1",
                metadata={}
            ),
            Signal(
                symbol="GOOGL",
                timestamp=base_time,
                recommendation=Recommendation.BUY,
                confidence=0.9,
                model_id="model_2",
                metadata={}
            )
        ]
        
        for signal in signals:
            logger.log_signal(signal)
        
        # Get performance for specific model
        metrics = analytics_engine.get_model_performance(
            start_date=base_time - timedelta(hours=1),
            end_date=base_time + timedelta(hours=1),
            model_id="model_1"
        )
        
        assert len(metrics) == 1
        assert "model_1" in metrics
        assert "model_2" not in metrics
    
    def test_no_signals(self, analytics_engine, logger):
        """Test with no signals in date range"""
        base_time = datetime(2024, 1, 1, 9, 0, 0)
        
        metrics = analytics_engine.get_model_performance(
            start_date=base_time,
            end_date=base_time + timedelta(hours=1)
        )
        
        assert len(metrics) == 0


class TestGeneratePnlChart:
    """Tests for generate_pnl_chart"""
    
    def test_generate_chart_with_data(self, analytics_engine, sample_portfolio_history):
        """Test chart generation with portfolio data"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            analytics_engine.generate_pnl_chart(
                sample_portfolio_history,
                output_path
            )
            
            # Verify file was created
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_generate_chart_empty_data(self, analytics_engine):
        """Test chart generation with empty data"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            analytics_engine.generate_pnl_chart([], output_path)
            
            # Verify file was created even with no data
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestGenerateAllocationChart:
    """Tests for generate_allocation_chart"""
    
    def test_generate_chart_with_positions(self, analytics_engine):
        """Test allocation chart with positions"""
        snapshot = PortfolioSnapshot(
            timestamp=datetime(2024, 1, 1),
            positions=[
                Position(
                    symbol="AAPL",
                    quantity=100,
                    entry_price=Decimal("150.00"),
                    current_price=Decimal("155.00"),
                    entry_timestamp=datetime(2024, 1, 1),
                    unrealized_pnl=Decimal("500.00")
                ),
                Position(
                    symbol="GOOGL",
                    quantity=50,
                    entry_price=Decimal("2800.00"),
                    current_price=Decimal("2850.00"),
                    entry_timestamp=datetime(2024, 1, 1),
                    unrealized_pnl=Decimal("2500.00")
                )
            ],
            total_value=Decimal("200000.00"),
            cash_balance=Decimal("30000.00"),
            unrealized_pnl=Decimal("3000.00"),
            realized_pnl=Decimal("0.00"),
            drawdown=Decimal("0.00")
        )
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            analytics_engine.generate_allocation_chart(snapshot, output_path)
            
            # Verify file was created
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_generate_chart_no_positions(self, analytics_engine):
        """Test allocation chart with no positions (cash only)"""
        snapshot = PortfolioSnapshot(
            timestamp=datetime(2024, 1, 1),
            positions=[],
            total_value=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
            unrealized_pnl=Decimal("0.00"),
            realized_pnl=Decimal("0.00"),
            drawdown=Decimal("0.00")
        )
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            analytics_engine.generate_allocation_chart(snapshot, output_path)
            
            # Verify file was created
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
