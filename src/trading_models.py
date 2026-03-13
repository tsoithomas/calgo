"""Example trading model implementations for Calgo"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
import random

from src.models import Signal, PriceData, PortfolioSnapshot, Recommendation
from src.signal_generator import TradingModel


class MovingAverageCrossover(TradingModel):
    """
    Moving Average Crossover trading model.
    
    Generates BUY signal when short MA crosses above long MA.
    Generates SELL signal when short MA crosses below long MA.
    Generates HOLD signal otherwise.
    """
    
    def __init__(self, short_window: int = 10, long_window: int = 50, model_id: str = "ma_crossover"):
        """
        Initialize Moving Average Crossover model.
        
        Args:
            short_window: Number of periods for short moving average
            long_window: Number of periods for long moving average
            model_id: Unique identifier for this model instance
        """
        if short_window >= long_window:
            raise ValueError("Short window must be less than long window")
        
        self.short_window = short_window
        self.long_window = long_window
        self._model_id = model_id
        self._price_history: Dict[str, List[Decimal]] = {}
    
    def get_model_id(self) -> str:
        """Get model identifier"""
        return self._model_id
    
    def predict(self, market_data: PriceData, portfolio_state: PortfolioSnapshot) -> Signal:
        """
        Generate signal based on moving average crossover.
        
        Args:
            market_data: Current market price data
            portfolio_state: Current portfolio state
            
        Returns:
            Signal with BUY/SELL/HOLD recommendation
        """
        symbol = market_data.symbol
        
        # Initialize price history for this symbol if needed
        if symbol not in self._price_history:
            self._price_history[symbol] = []
        
        # Add current price to history
        self._price_history[symbol].append(market_data.close)
        
        # Keep only the required number of prices
        max_history = self.long_window
        if len(self._price_history[symbol]) > max_history:
            self._price_history[symbol] = self._price_history[symbol][-max_history:]
        
        # Need enough data for long MA
        if len(self._price_history[symbol]) < self.long_window:
            # Not enough data, return HOLD with low confidence
            return Signal(
                symbol=symbol,
                timestamp=market_data.timestamp,
                recommendation=Recommendation.HOLD,
                confidence=0.3,
                model_id=self._model_id,
                metadata={
                    "reason": "insufficient_data",
                    "data_points": len(self._price_history[symbol]),
                    "required": self.long_window
                }
            )
        
        # Calculate moving averages
        prices = self._price_history[symbol]
        short_ma = sum(prices[-self.short_window:]) / self.short_window
        long_ma = sum(prices[-self.long_window:]) / self.long_window
        
        # Calculate previous MAs for crossover detection
        if len(prices) >= self.long_window + 1:
            prev_prices = prices[:-1]
            prev_short_ma = sum(prev_prices[-self.short_window:]) / self.short_window
            prev_long_ma = sum(prev_prices[-self.long_window:]) / self.long_window
        else:
            # First time we have enough data, no previous crossover
            prev_short_ma = short_ma
            prev_long_ma = long_ma
        
        # Detect crossover
        current_diff = short_ma - long_ma
        prev_diff = prev_short_ma - prev_long_ma
        
        # Calculate confidence based on magnitude of difference
        diff_pct = abs(float(current_diff / long_ma)) if long_ma != 0 else 0
        confidence = min(0.5 + diff_pct * 10, 1.0)  # Scale to 0.5-1.0 range
        
        # Determine recommendation
        if prev_diff <= 0 and current_diff > 0:
            # Bullish crossover: short MA crossed above long MA
            recommendation = Recommendation.BUY
            reason = "bullish_crossover"
        elif prev_diff >= 0 and current_diff < 0:
            # Bearish crossover: short MA crossed below long MA
            recommendation = Recommendation.SELL
            reason = "bearish_crossover"
        elif current_diff > 0:
            # Short MA above long MA but no recent crossover
            recommendation = Recommendation.HOLD
            reason = "short_above_long"
            confidence *= 0.7  # Lower confidence for non-crossover
        elif current_diff < 0:
            # Short MA below long MA but no recent crossover
            recommendation = Recommendation.HOLD
            reason = "short_below_long"
            confidence *= 0.7  # Lower confidence for non-crossover
        else:
            # MAs are equal
            recommendation = Recommendation.HOLD
            reason = "mas_equal"
            confidence = 0.5
        
        return Signal(
            symbol=symbol,
            timestamp=market_data.timestamp,
            recommendation=recommendation,
            confidence=confidence,
            model_id=self._model_id,
            metadata={
                "short_ma": float(short_ma),
                "long_ma": float(long_ma),
                "short_window": self.short_window,
                "long_window": self.long_window,
                "reason": reason,
                "diff_pct": diff_pct
            }
        )


class MLClassifierModel(TradingModel):
    """
    Machine Learning Classifier trading model.
    
    Placeholder implementation using simple heuristics.
    In production, this would use a trained Random Forest or Logistic Regression model.
    """
    
    def __init__(self, model_id: str = "ml_classifier", use_random: bool = False):
        """
        Initialize ML Classifier model.
        
        Args:
            model_id: Unique identifier for this model instance
            use_random: If True, generates random predictions (for testing)
        """
        self._model_id = model_id
        self._use_random = use_random
        self._price_history: Dict[str, List[Decimal]] = {}
    
    def get_model_id(self) -> str:
        """Get model identifier"""
        return self._model_id
    
    def predict(self, market_data: PriceData, portfolio_state: PortfolioSnapshot) -> Signal:
        """
        Generate signal using ML classifier.
        
        This is a placeholder implementation using simple heuristics.
        In production, this would use features like:
        - Price momentum
        - Volume trends
        - Volatility
        - Technical indicators
        
        Args:
            market_data: Current market price data
            portfolio_state: Current portfolio state
            
        Returns:
            Signal with BUY/SELL/HOLD recommendation
        """
        symbol = market_data.symbol
        
        # Initialize price history for this symbol if needed
        if symbol not in self._price_history:
            self._price_history[symbol] = []
        
        # Add current price to history
        self._price_history[symbol].append(market_data.close)
        
        # Keep last 20 prices for feature calculation
        if len(self._price_history[symbol]) > 20:
            self._price_history[symbol] = self._price_history[symbol][-20:]
        
        # If using random mode (for testing)
        if self._use_random:
            return self._generate_random_signal(market_data)
        
        # Need at least 5 data points for features
        if len(self._price_history[symbol]) < 5:
            return Signal(
                symbol=symbol,
                timestamp=market_data.timestamp,
                recommendation=Recommendation.HOLD,
                confidence=0.4,
                model_id=self._model_id,
                metadata={
                    "reason": "insufficient_data",
                    "data_points": len(self._price_history[symbol])
                }
            )
        
        # Calculate simple features
        prices = self._price_history[symbol]
        
        # Feature 1: Price momentum (% change over last 5 periods)
        momentum = float((prices[-1] - prices[-5]) / prices[-5]) if prices[-5] != 0 else 0
        
        # Feature 2: Volatility (std dev of last 10 prices)
        if len(prices) >= 10:
            recent_prices = [float(p) for p in prices[-10:]]
            mean_price = sum(recent_prices) / len(recent_prices)
            variance = sum((p - mean_price) ** 2 for p in recent_prices) / len(recent_prices)
            volatility = variance ** 0.5
        else:
            volatility = 0.0
        
        # Feature 3: Volume trend (current vs average)
        volume_ratio = 1.0  # Placeholder - would use actual volume data
        
        # Simple heuristic-based classification (placeholder for trained model)
        # In production, this would be: prediction = self.model.predict(features)
        
        # Normalize volatility as percentage of price
        volatility_pct = volatility / float(prices[-1]) if prices[-1] != 0 else 0
        
        if momentum > 0.02 and volatility_pct < 0.05:
            # Strong upward momentum with low volatility -> BUY
            recommendation = Recommendation.BUY
            confidence = min(0.6 + abs(momentum) * 5, 0.95)
            reason = "positive_momentum_low_volatility"
        elif momentum < -0.02 and volatility_pct < 0.05:
            # Strong downward momentum with low volatility -> SELL
            recommendation = Recommendation.SELL
            confidence = min(0.6 + abs(momentum) * 5, 0.95)
            reason = "negative_momentum_low_volatility"
        elif volatility_pct > 0.1:
            # High volatility -> HOLD (too risky)
            recommendation = Recommendation.HOLD
            confidence = 0.7
            reason = "high_volatility"
        else:
            # Neutral conditions -> HOLD
            recommendation = Recommendation.HOLD
            confidence = 0.5
            reason = "neutral_conditions"
        
        return Signal(
            symbol=symbol,
            timestamp=market_data.timestamp,
            recommendation=recommendation,
            confidence=confidence,
            model_id=self._model_id,
            metadata={
                "momentum": momentum,
                "volatility": volatility,
                "volatility_pct": volatility_pct,
                "volume_ratio": volume_ratio,
                "reason": reason,
                "note": "placeholder_heuristics"
            }
        )
    
    def _generate_random_signal(self, market_data: PriceData) -> Signal:
        """
        Generate a random signal for testing purposes.
        
        Args:
            market_data: Current market price data
            
        Returns:
            Random signal
        """
        recommendations = [Recommendation.BUY, Recommendation.SELL, Recommendation.HOLD]
        recommendation = random.choice(recommendations)
        confidence = random.uniform(0.5, 0.95)
        
        return Signal(
            symbol=market_data.symbol,
            timestamp=market_data.timestamp,
            recommendation=recommendation,
            confidence=confidence,
            model_id=self._model_id,
            metadata={
                "mode": "random",
                "note": "random_prediction_for_testing"
            }
        )
