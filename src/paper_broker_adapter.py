"""Paper trading broker adapter for simulated order execution"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict

from src.broker_adapter import BrokerAdapter, OrderError, CancelConfirmation
from src.models import OrderConfirmation, OrderStatus, OrderAction
from src.result import Result


class PaperBrokerAdapter(BrokerAdapter):
    """
    Paper trading broker adapter that simulates order execution.
    
    Simulates immediate fills at current market price with mock execution.
    Tracks order history for testing and validation.
    """
    
    def __init__(self, initial_cash: Decimal = Decimal("100000.00")):
        """
        Initialize paper trading adapter.
        
        Args:
            initial_cash: Starting cash balance for simulation
        """
        self._orders: Dict[str, OrderConfirmation] = {}
        self._cash_balance = initial_cash
        self._order_counter = 0
    
    def place_order(
        self,
        symbol: str,
        quantity: int,
        action: OrderAction,
        order_type: str
    ) -> Result[OrderConfirmation, OrderError]:
        """
        Simulate order placement with immediate fill.
        
        Args:
            symbol: Stock/ETF ticker symbol
            quantity: Number of shares to trade
            action: BUY or SELL
            order_type: MARKET or LIMIT (both treated as immediate fill)
            
        Returns:
            Result containing OrderConfirmation with simulated execution
        """
        # Validate inputs
        if quantity <= 0:
            return Result.err(OrderError(
                "Invalid quantity: must be positive",
                {"symbol": symbol, "quantity": quantity}
            ))
        
        if not symbol or not symbol.strip():
            return Result.err(OrderError(
                "Invalid symbol: cannot be empty",
                {"symbol": symbol}
            ))
        
        # Generate unique order ID
        self._order_counter += 1
        order_id = f"PAPER-{uuid.uuid4().hex[:8].upper()}-{self._order_counter}"
        
        # Simulate execution price (in real implementation, would fetch current market price)
        # For now, use a mock price based on symbol hash for consistency
        mock_price = self._get_mock_price(symbol)
        
        # Calculate order value
        order_value = mock_price * Decimal(quantity)
        
        # Check if we have sufficient funds for BUY orders
        if action == OrderAction.BUY:
            if order_value > self._cash_balance:
                return Result.err(OrderError(
                    f"Insufficient funds: need {order_value}, have {self._cash_balance}",
                    {
                        "symbol": symbol,
                        "quantity": quantity,
                        "required": float(order_value),
                        "available": float(self._cash_balance)
                    }
                ))
            self._cash_balance -= order_value
        else:  # SELL
            self._cash_balance += order_value
        
        # Create order confirmation
        confirmation = OrderConfirmation(
            order_id=order_id,
            symbol=symbol,
            quantity=quantity,
            execution_price=mock_price,
            timestamp=datetime.now(),
            status=OrderStatus.FILLED
        )
        
        # Store order in history
        self._orders[order_id] = confirmation
        
        return Result.ok(confirmation)
    
    def cancel_order(self, order_id: str) -> Result[CancelConfirmation, OrderError]:
        """
        Cancel a pending order (always fails in paper trading since orders fill immediately).
        
        Args:
            order_id: Unique identifier of the order to cancel
            
        Returns:
            Result containing error (orders are immediately filled in paper trading)
        """
        if order_id not in self._orders:
            return Result.err(OrderError(
                f"Order not found: {order_id}",
                {"order_id": order_id}
            ))
        
        order = self._orders[order_id]
        if order.status == OrderStatus.FILLED:
            return Result.err(OrderError(
                f"Cannot cancel filled order: {order_id}",
                {"order_id": order_id, "status": order.status.value}
            ))
        
        # In paper trading, orders are immediately filled, so cancellation always fails
        return Result.err(OrderError(
            "Cannot cancel order in paper trading (orders fill immediately)",
            {"order_id": order_id}
        ))
    
    def get_order_status(self, order_id: str) -> OrderStatus:
        """
        Get the current status of an order.
        
        Args:
            order_id: Unique identifier of the order
            
        Returns:
            Current OrderStatus (always FILLED for existing orders in paper trading)
        """
        if order_id in self._orders:
            return self._orders[order_id].status
        return OrderStatus.REJECTED
    
    def get_cash_balance(self) -> Decimal:
        """
        Get current simulated cash balance.
        
        Returns:
            Current cash balance
        """
        return self._cash_balance
    
    def get_order_history(self) -> Dict[str, OrderConfirmation]:
        """
        Get all executed orders.
        
        Returns:
            Dictionary of order_id to OrderConfirmation
        """
        return self._orders.copy()
    
    def _get_mock_price(self, symbol: str) -> Decimal:
        """
        Generate a consistent mock price for a symbol.
        
        Uses symbol hash to generate a deterministic price for testing.
        In real implementation, would fetch actual market price.
        
        Args:
            symbol: Stock/ETF ticker symbol
            
        Returns:
            Mock price as Decimal
        """
        # Generate price based on symbol hash (deterministic for testing)
        hash_val = sum(ord(c) for c in symbol)
        base_price = 50 + (hash_val % 200)  # Price between 50 and 250
        cents = (hash_val % 100) / 100  # Add cents
        return Decimal(str(base_price + cents))
