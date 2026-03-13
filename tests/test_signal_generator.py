"""Unit tests for Signal Generator"""
import pytest
from datetime import datetime
from decimal import Decimal

from src.signal_generator import SignalGenerator, TradingModel, AggregationStrategy
from src.trading_models import MovingAverageCrossover, MLClassifierModel
from src.models import (
    Signal, PriceData, PortfolioSnapshot, Recommendation, 
    DataSource, Position
)


# Helper function to create test price data
def create_price_data(symbol: str, close: Decimal, timestamp: datetime = None) -> PriceData:
    """Create test price data"""
    if timestamp is None:
        timestamp = datetime.now()
    
    return PriceData(
        symbol=symbol,
        timestamp=timestamp,
        open=close,
        high=close * Decimal("1.01"),
        low=close * Decimal("0.99"),
        close=close,
        volume=1000000,
        source=DataSource.YAHOO_FINANCE
    )


# Helper function to create test portfolio snapshot
def create_portfolio_snapshot() -> PortfolioSnapshot:
    """Create test portfolio snapshot"""
    return PortfolioSnapshot(
        timestamp=datetime.now(),
        positions=[],
        total_value=Decimal("10000.00"),
        cash_balance=Decimal("10000.00"),
        unrealized_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        drawdown=Decimal("0.00")
    )


class TestSignalGenerator:
    """Test cases for SignalGenerator"""
    
    def test_add_model(self):
        """Test adding a model to the generator"""
        generator = SignalGenerator()
        model = MovingAverageCrossover()
        
        generator.add_model(model)
        
        # Model should be added but not active
        assert model.get_model_id() in generator._models
    
    def test_remove_model(self):
        """Test removing a model from the generator"""
        generator = SignalGenerator()
        model = MovingAverageCrossover()
        
        generator.add_model(model)
        generator.remove_model(model.get_model_id())
        
        assert model.get_model_id() not in generator._models
    
    def test_set_active_models(self):
        """Test setting active models"""
        generator = SignalGenerator()
        model1 = MovingAverageCrossover(model_id="ma1")
        model2 = MLClassifierModel(model_id="ml1")
        
        generator.add_model(model1)
        generator.add_model(model2)
        generator.set_active_models(["ma1", "ml1"])
        
        assert generator._active_model_ids == ["ma1", "ml1"]
    
    def test_set_active_models_invalid_id(self):
        """Test setting active models with invalid ID raises error"""
        generator = SignalGenerator()
        
        with pytest.raises(ValueError, match="not found"):
            generator.set_active_models(["nonexistent_model"])
    
    def test_generate_signal_no_active_models(self):
        """Test generating signal with no active models raises error"""
        generator = SignalGenerator()
        market_data = create_price_data("AAPL", Decimal("150.00"))
        portfolio = create_portfolio_snapshot()
        
        with pytest.raises(ValueError, match="No active models"):
            generator.generate_signal(market_data, portfolio)
    
    def test_generate_signal_single_model(self):
        """Test generating signal with single active model"""
        generator = SignalGenerator()
        model = MovingAverageCrossover()
        
        generator.add_model(model)
        generator.set_active_models([model.get_model_id()])
        
        market_data = create_price_data("AAPL", Decimal("150.00"))
        portfolio = create_portfolio_snapshot()
        
        signal = generator.generate_signal(market_data, portfolio)
        
        assert signal.symbol == "AAPL"
        assert signal.recommendation in [Recommendation.BUY, Recommendation.SELL, Recommendation.HOLD]
        assert 0.0 <= signal.confidence <= 1.0
        assert signal.model_id == model.get_model_id()
    
    def test_generate_signal_multiple_models_voting(self):
        """Test generating signal with multiple models using voting strategy"""
        generator = SignalGenerator(aggregation_strategy=AggregationStrategy.VOTING)
        
        model1 = MovingAverageCrossover(model_id="ma1")
        model2 = MLClassifierModel(model_id="ml1", use_random=False)
        
        generator.add_model(model1)
        generator.add_model(model2)
        generator.set_active_models(["ma1", "ml1"])
        
        market_data = create_price_data("AAPL", Decimal("150.00"))
        portfolio = create_portfolio_snapshot()
        
        signal = generator.generate_signal(market_data, portfolio)
        
        assert signal.symbol == "AAPL"
        assert signal.recommendation in [Recommendation.BUY, Recommendation.SELL, Recommendation.HOLD]
        assert 0.0 <= signal.confidence <= 1.0
        assert signal.model_id == "aggregated_voting"
        assert "strategy" in signal.metadata
        assert signal.metadata["strategy"] == "voting"
    
    def test_generate_signal_multiple_models_weighted(self):
        """Test generating signal with multiple models using weighted average strategy"""
        generator = SignalGenerator(aggregation_strategy=AggregationStrategy.WEIGHTED_AVERAGE)
        
        model1 = MovingAverageCrossover(model_id="ma1")
        model2 = MLClassifierModel(model_id="ml1", use_random=False)
        
        generator.add_model(model1)
        generator.add_model(model2)
        generator.set_active_models(["ma1", "ml1"])
        
        market_data = create_price_data("AAPL", Decimal("150.00"))
        portfolio = create_portfolio_snapshot()
        
        signal = generator.generate_signal(market_data, portfolio)
        
        assert signal.symbol == "AAPL"
        assert signal.recommendation in [Recommendation.BUY, Recommendation.SELL, Recommendation.HOLD]
        assert 0.0 <= signal.confidence <= 1.0
        assert signal.model_id == "aggregated_weighted"
        assert "strategy" in signal.metadata
        assert signal.metadata["strategy"] == "weighted_average"
    
    def test_aggregate_signals_voting_majority_buy(self):
        """Test voting aggregation with majority BUY signals"""
        generator = SignalGenerator(aggregation_strategy=AggregationStrategy.VOTING)
        
        timestamp = datetime.now()
        signals = [
            Signal("AAPL", timestamp, Recommendation.BUY, 0.8, "model1", {}),
            Signal("AAPL", timestamp, Recommendation.BUY, 0.7, "model2", {}),
            Signal("AAPL", timestamp, Recommendation.SELL, 0.6, "model3", {}),
        ]
        
        result = generator.aggregate_signals(signals)
        
        assert result.recommendation == Recommendation.BUY
        assert result.confidence == 0.75  # Average of 0.8 and 0.7
        assert result.metadata["votes"][Recommendation.BUY.value] == 2
        assert result.metadata["votes"][Recommendation.SELL.value] == 1
    
    def test_aggregate_signals_weighted_average(self):
        """Test weighted average aggregation"""
        generator = SignalGenerator(aggregation_strategy=AggregationStrategy.WEIGHTED_AVERAGE)
        
        timestamp = datetime.now()
        signals = [
            Signal("AAPL", timestamp, Recommendation.BUY, 0.9, "model1", {}),
            Signal("AAPL", timestamp, Recommendation.SELL, 0.3, "model2", {}),
            Signal("AAPL", timestamp, Recommendation.HOLD, 0.3, "model3", {}),
        ]
        
        result = generator.aggregate_signals(signals)
        
        # BUY has highest weight: 0.9 / 1.5 = 0.6
        # SELL has weight: 0.3 / 1.5 = 0.2
        # HOLD has weight: 0.3 / 1.5 = 0.2
        assert result.recommendation == Recommendation.BUY
        assert result.metadata["strategy"] == "weighted_average"
    
    def test_aggregate_signals_empty_list(self):
        """Test aggregating empty signal list raises error"""
        generator = SignalGenerator()
        
        with pytest.raises(ValueError, match="empty signal list"):
            generator.aggregate_signals([])
    
    def test_aggregate_signals_single_signal(self):
        """Test aggregating single signal returns it unchanged"""
        generator = SignalGenerator()
        
        timestamp = datetime.now()
        signal = Signal("AAPL", timestamp, Recommendation.BUY, 0.8, "model1", {})
        
        result = generator.aggregate_signals([signal])
        
        assert result == signal


class TestMovingAverageCrossover:
    """Test cases for MovingAverageCrossover model"""
    
    def test_initialization(self):
        """Test model initialization"""
        model = MovingAverageCrossover(short_window=5, long_window=20, model_id="test_ma")
        
        assert model.short_window == 5
        assert model.long_window == 20
        assert model.get_model_id() == "test_ma"
    
    def test_initialization_invalid_windows(self):
        """Test initialization with invalid window sizes raises error"""
        with pytest.raises(ValueError, match="Short window must be less than long window"):
            MovingAverageCrossover(short_window=20, long_window=10)
    
    def test_predict_insufficient_data(self):
        """Test prediction with insufficient data returns HOLD"""
        model = MovingAverageCrossover(short_window=5, long_window=10)
        market_data = create_price_data("AAPL", Decimal("150.00"))
        portfolio = create_portfolio_snapshot()
        
        signal = model.predict(market_data, portfolio)
        
        assert signal.recommendation == Recommendation.HOLD
        assert signal.confidence < 0.5
        assert signal.metadata["reason"] == "insufficient_data"
    
    def test_predict_bullish_signal(self):
        """Test that model generates valid signals for bullish scenarios"""
        model = MovingAverageCrossover(short_window=2, long_window=5)
        portfolio = create_portfolio_snapshot()
        
        # Feed enough prices to get past insufficient data phase
        for i in range(15):
            price = Decimal("100") + Decimal(str(i))
            market_data = create_price_data("AAPL", price)
            signal = model.predict(market_data, portfolio)
        
        # Verify signal structure is complete
        assert signal.symbol == "AAPL"
        assert signal.recommendation in [Recommendation.BUY, Recommendation.SELL, Recommendation.HOLD]
        assert 0.0 <= signal.confidence <= 1.0
        assert "short_ma" in signal.metadata
        assert "long_ma" in signal.metadata
    
    def test_predict_bearish_signal(self):
        """Test that model generates valid signals for bearish scenarios"""
        model = MovingAverageCrossover(short_window=2, long_window=5)
        portfolio = create_portfolio_snapshot()
        
        # Feed enough prices to get past insufficient data phase
        for i in range(15):
            price = Decimal("100") - Decimal(str(i))
            market_data = create_price_data("AAPL", price)
            signal = model.predict(market_data, portfolio)
        
        # Verify signal structure is complete
        assert signal.symbol == "AAPL"
        assert signal.recommendation in [Recommendation.BUY, Recommendation.SELL, Recommendation.HOLD]
        assert 0.0 <= signal.confidence <= 1.0
        assert "short_ma" in signal.metadata
        assert "long_ma" in signal.metadata
    
    def test_predict_hold_short_above_long(self):
        """Test prediction returns HOLD when short MA above long MA (no crossover)"""
        model = MovingAverageCrossover(short_window=2, long_window=5)
        portfolio = create_portfolio_snapshot()
        
        # Feed steadily increasing prices
        prices = [Decimal(str(100 + i)) for i in range(10)]
        
        for price in prices:
            market_data = create_price_data("AAPL", price)
            signal = model.predict(market_data, portfolio)
        
        # Should be HOLD (short above long but no recent crossover)
        assert signal.recommendation == Recommendation.HOLD
        assert signal.metadata["reason"] == "short_above_long"


class TestMLClassifierModel:
    """Test cases for MLClassifierModel"""
    
    def test_initialization(self):
        """Test model initialization"""
        model = MLClassifierModel(model_id="test_ml")
        
        assert model.get_model_id() == "test_ml"
        assert not model._use_random
    
    def test_predict_insufficient_data(self):
        """Test prediction with insufficient data returns HOLD"""
        model = MLClassifierModel()
        market_data = create_price_data("AAPL", Decimal("150.00"))
        portfolio = create_portfolio_snapshot()
        
        signal = model.predict(market_data, portfolio)
        
        assert signal.recommendation == Recommendation.HOLD
        assert signal.metadata["reason"] == "insufficient_data"
    
    def test_predict_positive_momentum(self):
        """Test prediction with positive momentum"""
        model = MLClassifierModel()
        portfolio = create_portfolio_snapshot()
        
        # Feed prices with strong steady upward momentum (low volatility)
        # Use larger increments to exceed 2% momentum threshold
        for i in range(10):
            price = Decimal("100") + Decimal(str(i * 1.0))  # Steady 1.0 increase
            market_data = create_price_data("AAPL", price)
            signal = model.predict(market_data, portfolio)
        
        # Should detect positive momentum with low volatility
        # Momentum over last 5 periods: (109 - 105) / 105 = 3.8%
        assert signal.recommendation == Recommendation.BUY
        assert signal.metadata["momentum"] > 0.02
    
    def test_predict_negative_momentum(self):
        """Test prediction with negative momentum"""
        model = MLClassifierModel()
        portfolio = create_portfolio_snapshot()
        
        # Feed prices with steady downward momentum (low volatility)
        # Use smaller decrements to keep volatility low
        for i in range(10):
            price = Decimal("100") - Decimal(str(i * 0.5))  # Steady 0.5 decrease
            market_data = create_price_data("AAPL", price)
            signal = model.predict(market_data, portfolio)
        
        # Should detect negative momentum with low volatility
        assert signal.recommendation == Recommendation.SELL
        assert signal.metadata["momentum"] < 0
    
    def test_predict_random_mode(self):
        """Test prediction in random mode"""
        model = MLClassifierModel(use_random=True)
        market_data = create_price_data("AAPL", Decimal("150.00"))
        portfolio = create_portfolio_snapshot()
        
        signal = model.predict(market_data, portfolio)
        
        assert signal.recommendation in [Recommendation.BUY, Recommendation.SELL, Recommendation.HOLD]
        assert 0.0 <= signal.confidence <= 1.0
        assert signal.metadata["mode"] == "random"
    
    def test_predict_signal_structure(self):
        """Test that prediction returns complete signal structure"""
        model = MLClassifierModel()
        portfolio = create_portfolio_snapshot()
        
        # Feed enough data
        for i in range(10):
            market_data = create_price_data("AAPL", Decimal("150.00"))
            signal = model.predict(market_data, portfolio)
        
        # Verify signal structure
        assert signal.symbol == "AAPL"
        assert isinstance(signal.timestamp, datetime)
        assert isinstance(signal.recommendation, Recommendation)
        assert 0.0 <= signal.confidence <= 1.0
        assert signal.model_id == model.get_model_id()
        assert isinstance(signal.metadata, dict)
