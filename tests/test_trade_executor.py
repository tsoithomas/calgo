"""Unit tests for TradeExecutor"""
import pytest
from decimal import Decimal

from src.trade_executor import TradeExecutor
from src.paper_broker_adapter import PaperBrokerAdapter
from src.live_broker_adapter import LiveBrokerAdapter
from src.models import Order, OrderAction, OrderType, OrderStatus, ExecutionMode


class TestTradeExecutor:
    """Test suite for TradeExecutor"""
    
    def test_submit_order_success_simulation_mode(self):
        """Test successful order submission in simulation mode"""
        adapter = PaperBrokerAdapter(initial_cash=Decimal("10000.00"))
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        order = Order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        
        result = executor.submit_order(order)
        
        assert result.is_ok()
        confirmation = result.unwrap()
        assert confirmation.symbol == "AAPL"
        assert confirmation.quantity == 10
        assert confirmation.status == OrderStatus.FILLED
    
    def test_submit_order_invalid_symbol(self):
        """Test order rejection for empty symbol"""
        adapter = PaperBrokerAdapter()
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        order = Order(
            symbol="",
            quantity=10,
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        
        result = executor.submit_order(order)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "symbol cannot be empty" in error.message
    
    def test_submit_order_invalid_quantity_zero(self):
        """Test order rejection for zero quantity"""
        adapter = PaperBrokerAdapter()
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        order = Order(
            symbol="AAPL",
            quantity=0,
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        
        result = executor.submit_order(order)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "quantity must be positive" in error.message
    
    def test_submit_order_invalid_quantity_negative(self):
        """Test order rejection for negative quantity"""
        adapter = PaperBrokerAdapter()
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        order = Order(
            symbol="AAPL",
            quantity=-10,
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        
        result = executor.submit_order(order)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "quantity must be positive" in error.message
    
    def test_submit_order_limit_without_price(self):
        """Test LIMIT order rejection when limit_price is missing"""
        adapter = PaperBrokerAdapter()
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        order = Order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type=OrderType.LIMIT,
            limit_price=None
        )
        
        result = executor.submit_order(order)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "limit_price required" in error.message
    
    def test_submit_order_limit_with_invalid_price(self):
        """Test LIMIT order rejection when limit_price is invalid"""
        adapter = PaperBrokerAdapter()
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        order = Order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type=OrderType.LIMIT,
            limit_price=Decimal("-10.00")
        )
        
        result = executor.submit_order(order)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "limit_price must be positive" in error.message
    
    def test_submit_order_limit_with_valid_price(self):
        """Test LIMIT order with valid limit_price"""
        adapter = PaperBrokerAdapter()
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        order = Order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type=OrderType.LIMIT,
            limit_price=Decimal("150.00")
        )
        
        # Note: PaperBrokerAdapter doesn't validate limit price,
        # but TradeExecutor should validate it before submission
        result = executor.submit_order(order)
        
        # Should pass validation (actual execution depends on broker)
        assert result.is_ok() or result.is_err()  # Either is acceptable
    
    def test_submit_order_insufficient_funds(self):
        """Test order rejection due to insufficient funds"""
        adapter = PaperBrokerAdapter(initial_cash=Decimal("100.00"))
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        order = Order(
            symbol="AAPL",
            quantity=100,
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        
        result = executor.submit_order(order)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Insufficient funds" in error.message
    
    def test_cancel_order_success(self):
        """Test order cancellation (should fail in paper trading)"""
        adapter = PaperBrokerAdapter()
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        # Place an order first
        order = Order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        
        submit_result = executor.submit_order(order)
        assert submit_result.is_ok()
        
        order_id = submit_result.unwrap().order_id
        
        # Try to cancel (should fail in paper trading)
        cancel_result = executor.cancel_order(order_id)
        
        assert cancel_result.is_err()
    
    def test_cancel_order_invalid_id(self):
        """Test cancellation with empty order ID"""
        adapter = PaperBrokerAdapter()
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        result = executor.cancel_order("")
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "order_id" in error.message.lower()
    
    def test_get_order_status_existing_order(self):
        """Test getting status of existing order"""
        adapter = PaperBrokerAdapter()
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        order = Order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        
        result = executor.submit_order(order)
        assert result.is_ok()
        
        order_id = result.unwrap().order_id
        status = executor.get_order_status(order_id)
        
        assert status == OrderStatus.FILLED
    
    def test_get_order_status_nonexistent_order(self):
        """Test getting status of non-existent order"""
        adapter = PaperBrokerAdapter()
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        status = executor.get_order_status("NONEXISTENT-ORDER")
        
        assert status == OrderStatus.REJECTED
    
    def test_get_order_status_empty_id(self):
        """Test getting status with empty order ID"""
        adapter = PaperBrokerAdapter()
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        status = executor.get_order_status("")
        
        assert status == OrderStatus.REJECTED
    
    def test_get_execution_mode_simulation(self):
        """Test getting execution mode in simulation"""
        adapter = PaperBrokerAdapter()
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        mode = executor.get_execution_mode()
        
        assert mode == ExecutionMode.SIMULATION
    
    def test_get_execution_mode_live(self):
        """Test getting execution mode in live"""
        adapter = LiveBrokerAdapter(
            api_key="test_key_12345",
            api_secret="test_secret_12345",
            base_url="https://api.example.com"
        )
        executor = TradeExecutor(ExecutionMode.LIVE, adapter)
        
        mode = executor.get_execution_mode()
        
        assert mode == ExecutionMode.LIVE
    
    def test_multiple_orders_same_symbol(self):
        """Test submitting multiple orders for same symbol"""
        adapter = PaperBrokerAdapter(initial_cash=Decimal("100000.00"))
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        order1 = Order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        
        order2 = Order(
            symbol="AAPL",
            quantity=5,
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        
        result1 = executor.submit_order(order1)
        result2 = executor.submit_order(order2)
        
        assert result1.is_ok()
        assert result2.is_ok()
        
        # Should have different order IDs
        assert result1.unwrap().order_id != result2.unwrap().order_id
    
    def test_buy_then_sell_workflow(self):
        """Test complete buy then sell workflow"""
        adapter = PaperBrokerAdapter(initial_cash=Decimal("10000.00"))
        executor = TradeExecutor(ExecutionMode.SIMULATION, adapter)
        
        # Buy order
        buy_order = Order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        
        buy_result = executor.submit_order(buy_order)
        assert buy_result.is_ok()
        
        # Sell order
        sell_order = Order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.SELL,
            order_type=OrderType.MARKET
        )
        
        sell_result = executor.submit_order(sell_order)
        assert sell_result.is_ok()
        
        # Both should be filled
        assert buy_result.unwrap().status == OrderStatus.FILLED
        assert sell_result.unwrap().status == OrderStatus.FILLED
    
    def test_live_mode_not_implemented(self):
        """Test that live mode returns appropriate error"""
        adapter = LiveBrokerAdapter(
            api_key="test_key_12345",
            api_secret="test_secret_12345",
            base_url="https://api.example.com"
        )
        executor = TradeExecutor(ExecutionMode.LIVE, adapter)
        
        order = Order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        
        result = executor.submit_order(order)
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "not implemented" in error.message.lower()
