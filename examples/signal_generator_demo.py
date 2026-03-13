"""Demo of Signal Generator with multiple trading models"""
from datetime import datetime
from decimal import Decimal

from src.signal_generator import SignalGenerator, AggregationStrategy
from src.trading_models import MovingAverageCrossover, MLClassifierModel
from src.models import PriceData, PortfolioSnapshot, DataSource


def create_sample_price_data(symbol: str, close: Decimal) -> PriceData:
    """Create sample price data for demonstration"""
    return PriceData(
        symbol=symbol,
        timestamp=datetime.now(),
        open=close * Decimal("0.99"),
        high=close * Decimal("1.01"),
        low=close * Decimal("0.98"),
        close=close,
        volume=1000000,
        source=DataSource.YAHOO_FINANCE
    )


def create_sample_portfolio() -> PortfolioSnapshot:
    """Create sample portfolio snapshot"""
    return PortfolioSnapshot(
        timestamp=datetime.now(),
        positions=[],
        total_value=Decimal("10000.00"),
        cash_balance=Decimal("10000.00"),
        unrealized_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        drawdown=Decimal("0.00")
    )


def demo_single_model():
    """Demonstrate signal generation with a single model"""
    print("=" * 60)
    print("Demo 1: Single Model Signal Generation")
    print("=" * 60)
    
    # Create signal generator
    generator = SignalGenerator()
    
    # Add a moving average crossover model
    ma_model = MovingAverageCrossover(short_window=5, long_window=20, model_id="ma_5_20")
    generator.add_model(ma_model)
    generator.set_active_models(["ma_5_20"])
    
    # Simulate price data
    portfolio = create_sample_portfolio()
    
    print("\nFeeding price data and generating signals...")
    prices = [Decimal("100"), Decimal("101"), Decimal("102"), Decimal("103"), Decimal("104")]
    
    for i, price in enumerate(prices):
        market_data = create_sample_price_data("AAPL", price)
        signal = generator.generate_signal(market_data, portfolio)
        
        print(f"\nPrice {i+1}: ${price}")
        print(f"  Recommendation: {signal.recommendation.value}")
        print(f"  Confidence: {signal.confidence:.2f}")
        print(f"  Model: {signal.model_id}")
        if "short_ma" in signal.metadata:
            print(f"  Short MA: {signal.metadata['short_ma']:.2f}")
            print(f"  Long MA: {signal.metadata['long_ma']:.2f}")


def demo_multiple_models_voting():
    """Demonstrate signal aggregation with voting strategy"""
    print("\n" + "=" * 60)
    print("Demo 2: Multiple Models with Voting Aggregation")
    print("=" * 60)
    
    # Create signal generator with voting strategy
    generator = SignalGenerator(aggregation_strategy=AggregationStrategy.VOTING)
    
    # Add multiple models
    ma_model = MovingAverageCrossover(short_window=5, long_window=20, model_id="ma_5_20")
    ml_model = MLClassifierModel(model_id="ml_classifier")
    
    generator.add_model(ma_model)
    generator.add_model(ml_model)
    generator.set_active_models(["ma_5_20", "ml_classifier"])
    
    # Simulate price data
    portfolio = create_sample_portfolio()
    
    print("\nFeeding price data with multiple models...")
    prices = [Decimal(str(100 + i)) for i in range(25)]
    
    for i, price in enumerate(prices[-5:], start=len(prices)-5):
        market_data = create_sample_price_data("AAPL", price)
        signal = generator.generate_signal(market_data, portfolio)
        
        print(f"\nPrice {i+1}: ${price}")
        print(f"  Aggregated Recommendation: {signal.recommendation.value}")
        print(f"  Confidence: {signal.confidence:.2f}")
        print(f"  Strategy: {signal.metadata.get('strategy', 'N/A')}")
        if "votes" in signal.metadata:
            print(f"  Votes: {signal.metadata['votes']}")


def demo_multiple_models_weighted():
    """Demonstrate signal aggregation with weighted average strategy"""
    print("\n" + "=" * 60)
    print("Demo 3: Multiple Models with Weighted Average Aggregation")
    print("=" * 60)
    
    # Create signal generator with weighted average strategy
    generator = SignalGenerator(aggregation_strategy=AggregationStrategy.WEIGHTED_AVERAGE)
    
    # Add multiple models
    ma_model = MovingAverageCrossover(short_window=5, long_window=20, model_id="ma_5_20")
    ml_model = MLClassifierModel(model_id="ml_classifier")
    
    generator.add_model(ma_model)
    generator.add_model(ml_model)
    generator.set_active_models(["ma_5_20", "ml_classifier"])
    
    # Simulate price data
    portfolio = create_sample_portfolio()
    
    print("\nFeeding price data with weighted aggregation...")
    prices = [Decimal(str(100 + i)) for i in range(25)]
    
    for i, price in enumerate(prices[-5:], start=len(prices)-5):
        market_data = create_sample_price_data("AAPL", price)
        signal = generator.generate_signal(market_data, portfolio)
        
        print(f"\nPrice {i+1}: ${price}")
        print(f"  Aggregated Recommendation: {signal.recommendation.value}")
        print(f"  Confidence: {signal.confidence:.2f}")
        print(f"  Strategy: {signal.metadata.get('strategy', 'N/A')}")
        if "scores" in signal.metadata:
            print(f"  Scores: {signal.metadata['scores']}")


def demo_runtime_model_management():
    """Demonstrate runtime model addition and removal"""
    print("\n" + "=" * 60)
    print("Demo 4: Runtime Model Management")
    print("=" * 60)
    
    # Create signal generator
    generator = SignalGenerator()
    
    # Start with one model
    ma_model1 = MovingAverageCrossover(short_window=5, long_window=20, model_id="ma_5_20")
    generator.add_model(ma_model1)
    generator.set_active_models(["ma_5_20"])
    
    print("\nActive models: ['ma_5_20']")
    
    # Add another model at runtime
    ma_model2 = MovingAverageCrossover(short_window=10, long_window=50, model_id="ma_10_50")
    generator.add_model(ma_model2)
    generator.set_active_models(["ma_5_20", "ma_10_50"])
    
    print("Added model: 'ma_10_50'")
    print("Active models: ['ma_5_20', 'ma_10_50']")
    
    # Remove a model at runtime
    generator.remove_model("ma_5_20")
    generator.set_active_models(["ma_10_50"])
    
    print("Removed model: 'ma_5_20'")
    print("Active models: ['ma_10_50']")
    
    # Generate signal with remaining model
    portfolio = create_sample_portfolio()
    market_data = create_sample_price_data("AAPL", Decimal("105"))
    signal = generator.generate_signal(market_data, portfolio)
    
    print(f"\nGenerated signal with model: {signal.model_id}")
    print(f"  Recommendation: {signal.recommendation.value}")
    print(f"  Confidence: {signal.confidence:.2f}")


if __name__ == "__main__":
    demo_single_model()
    demo_multiple_models_voting()
    demo_multiple_models_weighted()
    demo_runtime_model_management()
    
    print("\n" + "=" * 60)
    print("All demos completed successfully!")
    print("=" * 60)
