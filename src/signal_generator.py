"""Signal Generator for Calgo trading bot"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from src.models import Signal, PriceData, PortfolioSnapshot, Recommendation


class AggregationStrategy(Enum):
    """Signal aggregation strategies for multiple models"""
    VOTING = "voting"
    WEIGHTED_AVERAGE = "weighted_average"
    ENSEMBLE = "ensemble"


class TradingModel(ABC):
    """Abstract base class for trading models"""
    
    @abstractmethod
    def predict(self, market_data: PriceData, portfolio_state: PortfolioSnapshot) -> Signal:
        """
        Generate a trading signal based on market data and portfolio state.
        
        Args:
            market_data: Current market price data
            portfolio_state: Current portfolio state
            
        Returns:
            Signal with recommendation, confidence, and metadata
        """
        pass
    
    @abstractmethod
    def get_model_id(self) -> str:
        """
        Get unique identifier for this model.
        
        Returns:
            Model identifier string
        """
        pass


class SignalGenerator:
    """
    Generates trading signals using AI models.
    Supports multiple models, runtime model selection, and signal aggregation.
    """
    
    def __init__(self, aggregation_strategy: AggregationStrategy = AggregationStrategy.VOTING):
        """
        Initialize Signal Generator.
        
        Args:
            aggregation_strategy: Strategy for aggregating signals from multiple models
        """
        self._models: Dict[str, TradingModel] = {}
        self._active_model_ids: List[str] = []
        self._aggregation_strategy = aggregation_strategy
    
    def add_model(self, model: TradingModel) -> None:
        """
        Add a trading model to the generator.
        
        Args:
            model: Trading model instance
        """
        model_id = model.get_model_id()
        self._models[model_id] = model
    
    def remove_model(self, model_id: str) -> None:
        """
        Remove a trading model from the generator.
        
        Args:
            model_id: Identifier of model to remove
        """
        if model_id in self._models:
            del self._models[model_id]
        if model_id in self._active_model_ids:
            self._active_model_ids.remove(model_id)
    
    def set_active_models(self, model_ids: List[str]) -> None:
        """
        Set which models are active for signal generation.
        
        Args:
            model_ids: List of model identifiers to activate
        """
        # Validate all model IDs exist
        for model_id in model_ids:
            if model_id not in self._models:
                raise ValueError(f"Model '{model_id}' not found in available models")
        
        self._active_model_ids = model_ids
    
    def generate_signal(self, market_data: PriceData, portfolio_state: PortfolioSnapshot) -> Signal:
        """
        Generate a trading signal using active models.
        
        If multiple models are active, aggregates their signals using the configured strategy.
        
        Args:
            market_data: Current market price data
            portfolio_state: Current portfolio state
            
        Returns:
            Aggregated signal from active models
            
        Raises:
            ValueError: If no active models are configured
        """
        if not self._active_model_ids:
            raise ValueError("No active models configured")
        
        # Generate signals from all active models
        signals = []
        for model_id in self._active_model_ids:
            model = self._models[model_id]
            signal = model.predict(market_data, portfolio_state)
            signals.append(signal)
        
        # If only one model, return its signal directly
        if len(signals) == 1:
            return signals[0]
        
        # Aggregate multiple signals
        return self.aggregate_signals(signals)
    
    def aggregate_signals(self, signals: List[Signal]) -> Signal:
        """
        Aggregate multiple signals using the configured strategy.
        
        Args:
            signals: List of signals to aggregate
            
        Returns:
            Aggregated signal
        """
        if not signals:
            raise ValueError("Cannot aggregate empty signal list")
        
        if len(signals) == 1:
            return signals[0]
        
        if self._aggregation_strategy == AggregationStrategy.VOTING:
            return self._aggregate_voting(signals)
        elif self._aggregation_strategy == AggregationStrategy.WEIGHTED_AVERAGE:
            return self._aggregate_weighted_average(signals)
        elif self._aggregation_strategy == AggregationStrategy.ENSEMBLE:
            return self._aggregate_ensemble(signals)
        else:
            raise ValueError(f"Unknown aggregation strategy: {self._aggregation_strategy}")
    
    def _aggregate_voting(self, signals: List[Signal]) -> Signal:
        """
        Aggregate signals using majority voting.
        
        Args:
            signals: List of signals to aggregate
            
        Returns:
            Signal with majority recommendation
        """
        # Count votes for each recommendation
        votes = {Recommendation.BUY: 0, Recommendation.SELL: 0, Recommendation.HOLD: 0}
        for signal in signals:
            votes[signal.recommendation] += 1
        
        # Find majority recommendation
        majority_rec = max(votes, key=votes.get)
        
        # Calculate average confidence of signals with majority recommendation
        matching_signals = [s for s in signals if s.recommendation == majority_rec]
        avg_confidence = sum(s.confidence for s in matching_signals) / len(matching_signals)
        
        # Use first signal as template
        first_signal = signals[0]
        
        return Signal(
            symbol=first_signal.symbol,
            timestamp=first_signal.timestamp,
            recommendation=majority_rec,
            confidence=avg_confidence,
            model_id="aggregated_voting",
            metadata={
                "strategy": "voting",
                "num_models": len(signals),
                "votes": {rec.value: count for rec, count in votes.items()},
                "source_models": [s.model_id for s in signals]
            }
        )
    
    def _aggregate_weighted_average(self, signals: List[Signal]) -> Signal:
        """
        Aggregate signals using confidence-weighted average.
        
        Args:
            signals: List of signals to aggregate
            
        Returns:
            Signal with confidence-weighted recommendation
        """
        # Calculate weighted scores for each recommendation
        scores = {Recommendation.BUY: 0.0, Recommendation.SELL: 0.0, Recommendation.HOLD: 0.0}
        total_confidence = sum(s.confidence for s in signals)
        
        for signal in signals:
            weight = signal.confidence / total_confidence if total_confidence > 0 else 1.0 / len(signals)
            scores[signal.recommendation] += weight
        
        # Find recommendation with highest weighted score
        best_rec = max(scores, key=scores.get)
        
        # Use the highest weighted score as confidence
        confidence = scores[best_rec]
        
        # Use first signal as template
        first_signal = signals[0]
        
        return Signal(
            symbol=first_signal.symbol,
            timestamp=first_signal.timestamp,
            recommendation=best_rec,
            confidence=confidence,
            model_id="aggregated_weighted",
            metadata={
                "strategy": "weighted_average",
                "num_models": len(signals),
                "scores": {rec.value: score for rec, score in scores.items()},
                "source_models": [s.model_id for s in signals]
            }
        )
    
    def _aggregate_ensemble(self, signals: List[Signal]) -> Signal:
        """
        Aggregate signals using custom ensemble logic.
        
        Currently uses weighted average as default ensemble strategy.
        Can be extended with more sophisticated ensemble methods.
        
        Args:
            signals: List of signals to aggregate
            
        Returns:
            Ensemble aggregated signal
        """
        # For now, use weighted average as ensemble strategy
        # This can be extended with more sophisticated ensemble methods
        return self._aggregate_weighted_average(signals)
