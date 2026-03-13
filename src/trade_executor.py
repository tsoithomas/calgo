"""Trade executor for routing orders to broker adapters"""
from datetime import datetime
from typing import Optional

from src.broker_adapter import BrokerAdapter, OrderError, CancelConfirmation
from src.models import Order, OrderConfirmation, OrderStatus, ExecutionMode
from src.result import Result


class TradeExecutor:
    """
    Trade executor that routes orders to appropriate broker adapter.
    
    Abstracts broker API interactions and provides unified interface for
    order submission regardless of execution mode (simulation or live).
    """
    
    def __init__(self, execution_mode: ExecutionMode, broker_adapter: BrokerAdapter):
        """
        Initialize trade executor.
        
        Args:
            execution_mode: SIMULATION or LIVE execution mode
            broker_adapter: Broker adapter instance for order execution
        """
        self._execution_mode = execution_mode
        self._broker_adapter = broker_adapter
    
    def submit_order(self, order: Order) -> Result[OrderConfirmation, OrderError]:
        """
        Submit an order for execution through the configured broker adapter.
        
        Validates order parameters and routes to the appropriate broker
        based on execution mode.
        
        Args:
            order: Order to be executed
            
        Returns:
            Result containing OrderConfirmation on success or OrderError on failure
        """
        # Validate order
        validation_result = self._validate_order(order)
        if validation_result.is_err():
            return validation_result
        
        # Route order to broker adapter
        try:
            result = self._broker_adapter.place_order(
                symbol=order.symbol,
                quantity=order.quantity,
                action=order.action,
                order_type=order.order_type.value
            )
            
            if result.is_err():
                # Log error details
                error = result.unwrap_err()
                self._log_order_failure(order, error)
            
            return result
            
        except Exception as e:
            # Handle unexpected exceptions
            error = OrderError(
                f"Unexpected error during order submission: {str(e)}",
                {
                    "symbol": order.symbol,
                    "quantity": order.quantity,
                    "action": order.action.value,
                    "exception_type": type(e).__name__
                }
            )
            self._log_order_failure(order, error)
            return Result.err(error)
    
    def cancel_order(self, order_id: str) -> Result[CancelConfirmation, OrderError]:
        """
        Cancel a pending order.
        
        Args:
            order_id: Unique identifier of the order to cancel
            
        Returns:
            Result containing CancelConfirmation on success or OrderError on failure
        """
        if not order_id or not order_id.strip():
            return Result.err(OrderError(
                "Invalid order_id: cannot be empty",
                {"order_id": order_id}
            ))
        
        try:
            result = self._broker_adapter.cancel_order(order_id)
            
            if result.is_err():
                error = result.unwrap_err()
                self._log_cancellation_failure(order_id, error)
            
            return result
            
        except Exception as e:
            error = OrderError(
                f"Unexpected error during order cancellation: {str(e)}",
                {
                    "order_id": order_id,
                    "exception_type": type(e).__name__
                }
            )
            self._log_cancellation_failure(order_id, error)
            return Result.err(error)
    
    def get_order_status(self, order_id: str) -> OrderStatus:
        """
        Get the current status of an order.
        
        Args:
            order_id: Unique identifier of the order
            
        Returns:
            Current OrderStatus
        """
        if not order_id or not order_id.strip():
            return OrderStatus.REJECTED
        
        try:
            return self._broker_adapter.get_order_status(order_id)
        except Exception:
            # If status check fails, return REJECTED
            return OrderStatus.REJECTED
    
    def get_execution_mode(self) -> ExecutionMode:
        """
        Get the current execution mode.
        
        Returns:
            Current ExecutionMode (SIMULATION or LIVE)
        """
        return self._execution_mode
    
    def _validate_order(self, order: Order) -> Result[None, OrderError]:
        """
        Validate order parameters before submission.
        
        Args:
            order: Order to validate
            
        Returns:
            Result.ok(None) if valid, Result.err(OrderError) if invalid
        """
        # Validate symbol
        if not order.symbol or not order.symbol.strip():
            return Result.err(OrderError(
                "Invalid order: symbol cannot be empty",
                {"symbol": order.symbol}
            ))
        
        # Validate quantity
        if order.quantity <= 0:
            return Result.err(OrderError(
                f"Invalid order: quantity must be positive, got {order.quantity}",
                {"symbol": order.symbol, "quantity": order.quantity}
            ))
        
        # Validate limit price for LIMIT orders
        if order.order_type.value.upper() == "LIMIT":
            if order.limit_price is None:
                return Result.err(OrderError(
                    "Invalid order: limit_price required for LIMIT orders",
                    {"symbol": order.symbol, "order_type": order.order_type.value}
                ))
            if order.limit_price <= 0:
                return Result.err(OrderError(
                    f"Invalid order: limit_price must be positive, got {order.limit_price}",
                    {
                        "symbol": order.symbol,
                        "limit_price": float(order.limit_price)
                    }
                ))
        
        return Result.ok(None)
    
    def _log_order_failure(self, order: Order, error: OrderError) -> None:
        """
        Log order failure details.
        
        In production, this would write to the Logger component.
        For now, it's a placeholder for error tracking.
        
        Args:
            order: Failed order
            error: Error that occurred
        """
        # TODO: Integrate with Logger component
        # Example:
        # self._logger.log_error({
        #     "timestamp": datetime.now(),
        #     "component": "TradeExecutor",
        #     "error_type": "OrderFailure",
        #     "message": error.message,
        #     "order": {
        #         "symbol": order.symbol,
        #         "quantity": order.quantity,
        #         "action": order.action.value,
        #         "order_type": order.order_type.value
        #     },
        #     "details": error.order_details
        # })
        pass
    
    def _log_cancellation_failure(self, order_id: str, error: OrderError) -> None:
        """
        Log order cancellation failure details.
        
        In production, this would write to the Logger component.
        For now, it's a placeholder for error tracking.
        
        Args:
            order_id: ID of order that failed to cancel
            error: Error that occurred
        """
        # TODO: Integrate with Logger component
        pass
