"""Portfolio Manager for tracking positions and calculating P&L"""
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime

from src.models import Position, ClosedPosition, PortfolioSnapshot
from src.result import Result, Option


class PortfolioError(Exception):
    """Base exception for portfolio-related errors"""
    pass


class PortfolioManager:
    """
    Manages portfolio positions, tracks P&L, and enforces position limits.
    
    Responsibilities:
    - Track all open positions with entry price, current price, quantity, and unrealized P&L
    - Calculate realized P&L when positions are closed
    - Enforce portfolio and position size limits
    - Maintain current allocation and risk metrics
    - Provide portfolio snapshots on demand
    """
    
    def __init__(self, initial_cash: Decimal, max_portfolio_value: Decimal, max_position_size_pct: Decimal):
        """
        Initialize Portfolio Manager.
        
        Args:
            initial_cash: Starting cash balance
            max_portfolio_value: Maximum total portfolio value allowed
            max_position_size_pct: Maximum position size as percentage of portfolio (e.g., 0.20 for 20%)
        """
        # Internal storage for open positions (symbol -> Position)
        self._open_positions: Dict[str, Position] = {}
        
        # Internal storage for closed positions (list of all closed positions)
        self._closed_positions: List[ClosedPosition] = []
        
        # Cash balance tracking
        self._cash_balance: Decimal = initial_cash
        self._initial_cash: Decimal = initial_cash
        
        # Portfolio limits
        self._max_portfolio_value: Decimal = max_portfolio_value
        self._max_position_size_pct: Decimal = max_position_size_pct
        
        # Peak value for drawdown calculation
        self._peak_value: Decimal = initial_cash
    
    # Task 6.2: Position management methods
    
    def add_position(self, symbol: str, quantity: int, entry_price: Decimal) -> Result[Position, PortfolioError]:
        """
        Open a new position.
        
        Args:
            symbol: Stock/ETF symbol
            quantity: Number of shares
            entry_price: Entry price per share
            
        Returns:
            Result containing the new Position or PortfolioError
        """
        if symbol in self._open_positions:
            return Result.err(PortfolioError(f"Position for {symbol} already exists"))
        
        if quantity <= 0:
            return Result.err(PortfolioError(f"Quantity must be positive, got {quantity}"))
        
        if entry_price <= 0:
            return Result.err(PortfolioError(f"Entry price must be positive, got {entry_price}"))
        
        # Calculate position cost
        position_cost = entry_price * quantity
        
        # Check if we have enough cash
        if position_cost > self._cash_balance:
            return Result.err(PortfolioError(
                f"Insufficient cash: need {position_cost}, have {self._cash_balance}"
            ))
        
        # Create position
        position = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            entry_timestamp=datetime.now(),
            unrealized_pnl=Decimal("0.00")
        )
        
        # Update cash balance
        self._cash_balance -= position_cost
        
        # Store position
        self._open_positions[symbol] = position
        
        return Result.ok(position)
    
    def close_position(self, symbol: str, exit_price: Decimal) -> Result[ClosedPosition, PortfolioError]:
        """
        Close an existing position and calculate realized P&L.
        
        Args:
            symbol: Stock/ETF symbol
            exit_price: Exit price per share
            
        Returns:
            Result containing the ClosedPosition or PortfolioError
        """
        if symbol not in self._open_positions:
            return Result.err(PortfolioError(f"No open position for {symbol}"))
        
        if exit_price <= 0:
            return Result.err(PortfolioError(f"Exit price must be positive, got {exit_price}"))
        
        # Get the open position
        position = self._open_positions[symbol]
        
        # Calculate realized P&L: (exit_price - entry_price) * quantity
        realized_pnl = (exit_price - position.entry_price) * position.quantity
        
        # Create closed position
        closed_position = ClosedPosition(
            symbol=symbol,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=exit_price,
            entry_timestamp=position.entry_timestamp,
            exit_timestamp=datetime.now(),
            realized_pnl=realized_pnl
        )
        
        # Update cash balance (add proceeds from sale)
        self._cash_balance += exit_price * position.quantity
        
        # Remove from open positions and add to closed positions
        del self._open_positions[symbol]
        self._closed_positions.append(closed_position)
        
        return Result.ok(closed_position)
    
    def update_position(self, symbol: str, current_price: Decimal) -> None:
        """
        Update current price and unrealized P&L for a position.
        
        Args:
            symbol: Stock/ETF symbol
            current_price: Current market price per share
        """
        if symbol not in self._open_positions:
            raise PortfolioError(f"No open position for {symbol}")
        
        if current_price <= 0:
            raise PortfolioError(f"Current price must be positive, got {current_price}")
        
        position = self._open_positions[symbol]
        
        # Update current price
        position.current_price = current_price
        
        # Calculate unrealized P&L: (current_price - entry_price) * quantity
        position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
    
    def get_position(self, symbol: str) -> Option[Position]:
        """
        Get a specific open position.
        
        Args:
            symbol: Stock/ETF symbol
            
        Returns:
            Option containing the Position if it exists, or None
        """
        if symbol in self._open_positions:
            return Option.some(self._open_positions[symbol])
        return Option.none()
    
    def get_all_positions(self) -> List[Position]:
        """
        Get all open positions.
        
        Returns:
            List of all open positions
        """
        return list(self._open_positions.values())
    
    # Task 6.3: Portfolio metrics calculation
    
    def calculate_unrealized_pnl(self) -> Decimal:
        """
        Calculate total unrealized P&L across all open positions.
        
        Returns:
            Sum of all unrealized P&L
        """
        total = Decimal("0.00")
        for position in self._open_positions.values():
            total += position.unrealized_pnl
        return total
    
    def calculate_realized_pnl(self) -> Decimal:
        """
        Calculate total realized P&L from all closed positions.
        
        Returns:
            Sum of all realized P&L
        """
        total = Decimal("0.00")
        for closed_position in self._closed_positions:
            total += closed_position.realized_pnl
        return total
    
    def get_allocation(self, symbol: str) -> Decimal:
        """
        Calculate position allocation as percentage of total portfolio value.
        
        Args:
            symbol: Stock/ETF symbol
            
        Returns:
            Allocation percentage (e.g., 0.20 for 20%)
        """
        if symbol not in self._open_positions:
            return Decimal("0.00")
        
        total_value = self.get_total_value()
        
        # Avoid division by zero
        if total_value == 0:
            return Decimal("0.00")
        
        position = self._open_positions[symbol]
        position_value = position.current_price * position.quantity
        
        return position_value / total_value
    
    def get_total_value(self) -> Decimal:
        """
        Calculate total portfolio value (cash + all position values).
        
        Returns:
            Total portfolio value
        """
        total = self._cash_balance
        
        for position in self._open_positions.values():
            position_value = position.current_price * position.quantity
            total += position_value
        
        return total
    
    def get_snapshot(self) -> PortfolioSnapshot:
        """
        Create a complete portfolio snapshot.
        
        Returns:
            PortfolioSnapshot with all current state
        """
        # Update peak value if current value is higher
        current_value = self.get_total_value()
        if current_value > self._peak_value:
            self._peak_value = current_value
        
        # Calculate drawdown: (peak_value - current_value) / peak_value
        if self._peak_value > 0:
            drawdown = (self._peak_value - current_value) / self._peak_value
        else:
            drawdown = Decimal("0.00")
        
        return PortfolioSnapshot(
            timestamp=datetime.now(),
            positions=self.get_all_positions(),
            total_value=current_value,
            cash_balance=self._cash_balance,
            unrealized_pnl=self.calculate_unrealized_pnl(),
            realized_pnl=self.calculate_realized_pnl(),
            drawdown=drawdown
        )
    
    # Task 6.4: Portfolio limits enforcement
    
    def check_position_limit(self, symbol: str, quantity: int, price: Decimal) -> bool:
        """
        Validate position size against max_position_size_pct.
        
        Args:
            symbol: Stock/ETF symbol
            quantity: Number of shares
            price: Price per share
            
        Returns:
            True if position is within limits, False otherwise
        """
        position_value = price * quantity
        total_value = self.get_total_value()
        
        # Avoid division by zero
        if total_value == 0:
            return False
        
        position_pct = position_value / total_value
        
        return position_pct <= self._max_position_size_pct
    
    def check_portfolio_limit(self, value: Decimal) -> bool:
        """
        Validate total value against max_portfolio_value.
        
        Args:
            value: Total portfolio value to check
            
        Returns:
            True if within limits, False otherwise
        """
        return value <= self._max_portfolio_value
