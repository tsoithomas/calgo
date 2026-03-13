"""Risk Manager for Calgo trading bot"""
from decimal import Decimal
from typing import List, Optional

from src.config_models import RiskParameters
from src.models import (
    Position, PortfolioSnapshot, Signal, Recommendation, RiskViolation
)
from src.result import Result


class RiskError(Exception):
    """Base exception for risk management errors"""
    pass


class RiskManager:
    """
    Enforces risk management rules and generates protective signals.
    
    Responsibilities:
    - Validate signals against risk parameters
    - Check stop-loss and take-profit thresholds
    - Enforce position sizing limits
    - Monitor portfolio drawdown
    - Generate protective sell signals when thresholds breached
    - Halt trading when max drawdown exceeded
    """
    
    def __init__(self, risk_params: RiskParameters):
        """
        Initialize Risk Manager with risk parameters.
        
        Args:
            risk_params: Risk management thresholds and limits
        """
        self._risk_params = risk_params
    
    # Task 9.2: Risk check methods
    
    def check_stop_loss(self, position: Position) -> bool:
        """
        Check if position has breached stop-loss threshold.
        
        Args:
            position: Position to check
            
        Returns:
            True if stop-loss breached (loss exceeds threshold), False otherwise
        """
        # Calculate loss percentage: (current_price - entry_price) / entry_price
        loss_pct = (position.current_price - position.entry_price) / position.entry_price
        
        # Stop-loss breached if loss exceeds threshold (negative value)
        return loss_pct <= -self._risk_params.stop_loss_pct
    
    def check_take_profit(self, position: Position) -> bool:
        """
        Check if position has reached take-profit threshold.
        
        Args:
            position: Position to check
            
        Returns:
            True if take-profit reached (profit exceeds threshold), False otherwise
        """
        # Calculate profit percentage: (current_price - entry_price) / entry_price
        profit_pct = (position.current_price - position.entry_price) / position.entry_price
        
        # Take-profit reached if profit exceeds threshold (positive value)
        return profit_pct >= self._risk_params.take_profit_pct
    
    def check_position_size(self, portfolio: PortfolioSnapshot, position_value: Decimal) -> bool:
        """
        Check if position size is within allowed percentage of portfolio.
        
        Args:
            portfolio: Current portfolio snapshot
            position_value: Value of position to check
            
        Returns:
            True if position size is within limits, False otherwise
        """
        if portfolio.total_value == 0:
            return False
        
        # Calculate position percentage of total portfolio
        position_pct = position_value / portfolio.total_value
        
        # Check if within max position size limit
        return position_pct <= self._risk_params.max_position_size_pct
    
    def check_drawdown(self, portfolio: PortfolioSnapshot) -> bool:
        """
        Check if current drawdown exceeds maximum threshold.
        
        Args:
            portfolio: Current portfolio snapshot
            
        Returns:
            True if drawdown is within limits, False if exceeded
        """
        # Check if drawdown exceeds max threshold
        return portfolio.drawdown <= self._risk_params.max_drawdown_pct
    
    # Task 9.3: Signal evaluation and protective signals
    
    def evaluate_signal(self, signal: Signal, portfolio: PortfolioSnapshot) -> Result[Signal, RiskViolation]:
        """
        Evaluate a signal against risk parameters and approve or reject.
        
        Args:
            signal: Trading signal to evaluate
            portfolio: Current portfolio snapshot
            
        Returns:
            Result containing approved Signal or RiskViolation reason for rejection
        """
        # Only evaluate BUY signals (SELL and HOLD don't add risk)
        if signal.recommendation != Recommendation.BUY:
            return Result.ok(signal)
        
        # Check if trading is halted due to drawdown
        if not self.check_drawdown(portfolio):
            return Result.err(RiskViolation.DRAWDOWN_LIMIT_EXCEEDED)
        
        # Check portfolio value limit
        if portfolio.total_value >= self._risk_params.max_portfolio_value:
            return Result.err(RiskViolation.PORTFOLIO_LIMIT_EXCEEDED)
        
        # For BUY signals, we need to estimate the position size
        # This is a simplified check - actual position size would depend on order quantity
        # We'll check if adding a max-sized position would exceed limits
        max_position_value = portfolio.total_value * self._risk_params.max_position_size_pct
        
        if not self.check_position_size(portfolio, max_position_value):
            return Result.err(RiskViolation.POSITION_SIZE_EXCEEDED)
        
        # Signal approved
        return Result.ok(signal)
    
    def generate_protective_signals(self, portfolio: PortfolioSnapshot) -> List[Signal]:
        """
        Generate protective sell signals for positions breaching stop-loss or take-profit.
        
        Args:
            portfolio: Current portfolio snapshot
            
        Returns:
            List of protective sell signals for positions that need to be closed
        """
        protective_signals = []
        
        for position in portfolio.positions:
            # Check stop-loss breach
            if self.check_stop_loss(position):
                signal = Signal(
                    symbol=position.symbol,
                    timestamp=portfolio.timestamp,
                    recommendation=Recommendation.SELL,
                    confidence=1.0,  # Protective signals have max confidence
                    model_id="risk_manager_stop_loss",
                    metadata={
                        "reason": "stop_loss_breached",
                        "entry_price": str(position.entry_price),
                        "current_price": str(position.current_price),
                        "unrealized_pnl": str(position.unrealized_pnl),
                        "loss_pct": str((position.current_price - position.entry_price) / position.entry_price)
                    }
                )
                protective_signals.append(signal)
            
            # Check take-profit reach
            elif self.check_take_profit(position):
                signal = Signal(
                    symbol=position.symbol,
                    timestamp=portfolio.timestamp,
                    recommendation=Recommendation.SELL,
                    confidence=1.0,  # Protective signals have max confidence
                    model_id="risk_manager_take_profit",
                    metadata={
                        "reason": "take_profit_reached",
                        "entry_price": str(position.entry_price),
                        "current_price": str(position.current_price),
                        "unrealized_pnl": str(position.unrealized_pnl),
                        "profit_pct": str((position.current_price - position.entry_price) / position.entry_price)
                    }
                )
                protective_signals.append(signal)
        
        return protective_signals
    
    def is_trading_halted(self, portfolio: PortfolioSnapshot) -> bool:
        """
        Check if trading should be halted due to drawdown limit.
        
        Args:
            portfolio: Current portfolio snapshot
            
        Returns:
            True if trading should be halted (drawdown exceeded), False otherwise
        """
        return not self.check_drawdown(portfolio)
