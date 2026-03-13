"""Broker adapter interface and implementations for trade execution"""
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional

from src.models import Order, OrderConfirmation, OrderStatus, OrderAction
from src.result import Result


class OrderError(Exception):
    """Error during order execution"""
    def __init__(self, message: str, order_details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.order_details = order_details or {}


class CancelConfirmation:
    """Confirmation of order cancellation"""
    def __init__(self, order_id: str, timestamp: datetime, status: str):
        self.order_id = order_id
        self.timestamp = timestamp
        self.status = status


class BrokerAdapter(ABC):
    """
    Abstract base class for broker API adapters.
    
    Defines the interface that all broker implementations must follow.
    Enables switching between paper trading and live trading brokers.
    """
    
    @abstractmethod
    def place_order(
        self,
        symbol: str,
        quantity: int,
        action: OrderAction,
        order_type: str
    ) -> Result[OrderConfirmation, OrderError]:
        """
        Place an order with the broker.
        
        Args:
            symbol: Stock/ETF ticker symbol
            quantity: Number of shares to trade
            action: BUY or SELL
            order_type: MARKET or LIMIT
            
        Returns:
            Result containing OrderConfirmation on success or OrderError on failure
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> Result[CancelConfirmation, OrderError]:
        """
        Cancel a pending order.
        
        Args:
            order_id: Unique identifier of the order to cancel
            
        Returns:
            Result containing CancelConfirmation on success or OrderError on failure
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> OrderStatus:
        """
        Get the current status of an order.
        
        Args:
            order_id: Unique identifier of the order
            
        Returns:
            Current OrderStatus
        """
        pass
