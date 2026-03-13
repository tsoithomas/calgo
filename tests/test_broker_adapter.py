"""Unit tests for broker adapter interface and implementations"""
import pytest
from decimal import Decimal
from datetime import datetime

from src.broker_adapter import BrokerAdapter, OrderError, CancelConfirmation
from src.paper_broker_adapter import PaperBrokerAdapter
from src.live_broker_adapter import LiveBrokerAdapter
from src.models import OrderAction, OrderStatus


class TestPaperBrokerAdapter:
    """Test suite for PaperBrokerAdapter"""
    
    def test_place_order_buy_success(self):
        """Test successful BUY order placement"""
        adapter = PaperBrokerAdapter(initial_cash=Decimal("10000.00"))
        
        result = adapter.place_order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type="MARKET"
        )
        
        assert result.is_ok()
        confirmation = result.unwrap()
        assert confirmation.symbol == "AAPL"
        assert confirmation.quantity == 10
        assert confirmation.status == OrderStatus.FILLED
        assert confirmation.execution_price > 0
        assert confirmation.order_id.startswith("PAPER-")
    
    def test_place_order_sell_success(self):
        """Test successful SELL order placement"""
        adapter = PaperBrokerAdapter(initial_cash=Decimal("10000.00"))
        
        result = adapter.place_order(
            symbol="TSLA",
            quantity=5,
            action=OrderAction.SELL,
            order_type="MARKET"
        )
        
        assert result.is_ok()
        confirmation = result.unwrap()
        assert confirmation.symbol == "TSLA"
        assert confirmation.quantity == 5
        assert confirmation.status == OrderStatus.FILLED
    
    def test_place_order_insufficient_funds(self):
        """Test order rejection due to insufficient funds"""
        adapter = PaperBrokerAdapter(initial_cash=Decimal("100.00"))
        
        result = adapter.place_order(
            symbol="AAPL",
            quantity=100,
            action=OrderAction.BUY,
            order_type="MARKET"
        )
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Insufficient funds" in error.message
        assert "required" in error.order_details
        assert "available" in error.order_details
    
    def test_place_order_invalid_quantity(self):
        """Test order rejection for invalid quantity"""
        adapter = PaperBrokerAdapter()
        
        result = adapter.place_order(
            symbol="AAPL",
            quantity=0,
            action=OrderAction.BUY,
            order_type="MARKET"
        )
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid quantity" in error.message
    
    def test_place_order_negative_quantity(self):
        """Test order rejection for negative quantity"""
        adapter = PaperBrokerAdapter()
        
        result = adapter.place_order(
            symbol="AAPL",
            quantity=-10,
            action=OrderAction.BUY,
            order_type="MARKET"
        )
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid quantity" in error.message
    
    def test_place_order_empty_symbol(self):
        """Test order rejection for empty symbol"""
        adapter = PaperBrokerAdapter()
        
        result = adapter.place_order(
            symbol="",
            quantity=10,
            action=OrderAction.BUY,
            order_type="MARKET"
        )
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid symbol" in error.message
    
    def test_cash_balance_updates_on_buy(self):
        """Test cash balance decreases on BUY orders"""
        initial_cash = Decimal("10000.00")
        adapter = PaperBrokerAdapter(initial_cash=initial_cash)
        
        result = adapter.place_order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type="MARKET"
        )
        
        assert result.is_ok()
        confirmation = result.unwrap()
        expected_balance = initial_cash - (confirmation.execution_price * 10)
        assert adapter.get_cash_balance() == expected_balance
    
    def test_cash_balance_updates_on_sell(self):
        """Test cash balance increases on SELL orders"""
        initial_cash = Decimal("10000.00")
        adapter = PaperBrokerAdapter(initial_cash=initial_cash)
        
        result = adapter.place_order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.SELL,
            order_type="MARKET"
        )
        
        assert result.is_ok()
        confirmation = result.unwrap()
        expected_balance = initial_cash + (confirmation.execution_price * 10)
        assert adapter.get_cash_balance() == expected_balance
    
    def test_get_order_status_existing_order(self):
        """Test getting status of existing order"""
        adapter = PaperBrokerAdapter()
        
        result = adapter.place_order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type="MARKET"
        )
        
        assert result.is_ok()
        confirmation = result.unwrap()
        status = adapter.get_order_status(confirmation.order_id)
        assert status == OrderStatus.FILLED
    
    def test_get_order_status_nonexistent_order(self):
        """Test getting status of non-existent order"""
        adapter = PaperBrokerAdapter()
        
        status = adapter.get_order_status("NONEXISTENT-ORDER-ID")
        assert status == OrderStatus.REJECTED
    
    def test_cancel_order_not_found(self):
        """Test canceling non-existent order"""
        adapter = PaperBrokerAdapter()
        
        result = adapter.cancel_order("NONEXISTENT-ORDER-ID")
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Order not found" in error.message
    
    def test_cancel_order_already_filled(self):
        """Test canceling already filled order"""
        adapter = PaperBrokerAdapter()
        
        # Place order (immediately fills in paper trading)
        place_result = adapter.place_order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type="MARKET"
        )
        
        assert place_result.is_ok()
        confirmation = place_result.unwrap()
        
        # Try to cancel filled order
        cancel_result = adapter.cancel_order(confirmation.order_id)
        
        assert cancel_result.is_err()
        error = cancel_result.unwrap_err()
        assert "Cannot cancel" in error.message
    
    def test_order_history_tracking(self):
        """Test that order history is tracked correctly"""
        adapter = PaperBrokerAdapter()
        
        # Place multiple orders
        adapter.place_order("AAPL", 10, OrderAction.BUY, "MARKET")
        adapter.place_order("TSLA", 5, OrderAction.SELL, "MARKET")
        adapter.place_order("MSFT", 20, OrderAction.BUY, "MARKET")
        
        history = adapter.get_order_history()
        assert len(history) == 3
    
    def test_mock_price_consistency(self):
        """Test that mock prices are consistent for same symbol"""
        adapter = PaperBrokerAdapter()
        
        result1 = adapter.place_order("AAPL", 10, OrderAction.BUY, "MARKET")
        result2 = adapter.place_order("AAPL", 5, OrderAction.BUY, "MARKET")
        
        assert result1.is_ok()
        assert result2.is_ok()
        
        price1 = result1.unwrap().execution_price
        price2 = result2.unwrap().execution_price
        
        # Same symbol should have same mock price
        assert price1 == price2
    
    def test_unique_order_ids(self):
        """Test that each order gets a unique ID"""
        adapter = PaperBrokerAdapter()
        
        result1 = adapter.place_order("AAPL", 10, OrderAction.BUY, "MARKET")
        result2 = adapter.place_order("AAPL", 10, OrderAction.BUY, "MARKET")
        
        assert result1.is_ok()
        assert result2.is_ok()
        
        id1 = result1.unwrap().order_id
        id2 = result2.unwrap().order_id
        
        assert id1 != id2


class TestLiveBrokerAdapter:
    """Test suite for LiveBrokerAdapter stub"""
    
    def test_initialization_with_valid_credentials(self):
        """Test that adapter initializes with valid credentials"""
        adapter = LiveBrokerAdapter(
            api_key="test_key_12345",
            api_secret="test_secret_12345",
            base_url="https://api.example.com",
            broker_name="test_broker"
        )
        
        assert adapter._api_key == "test_key_12345"
        assert adapter._api_secret == "test_secret_12345"
        assert adapter._base_url == "https://api.example.com"
        assert adapter._broker_name == "test_broker"
        assert adapter._authenticated is True
        assert adapter._connection_verified is True
    
    def test_initialization_empty_api_key(self):
        """Test that initialization fails with empty API key"""
        with pytest.raises(OrderError) as exc_info:
            LiveBrokerAdapter(
                api_key="",
                api_secret="test_secret_12345",
                base_url="https://api.example.com"
            )
        
        assert "API key cannot be empty" in str(exc_info.value)
    
    def test_initialization_empty_api_secret(self):
        """Test that initialization fails with empty API secret"""
        with pytest.raises(OrderError) as exc_info:
            LiveBrokerAdapter(
                api_key="test_key_12345",
                api_secret="",
                base_url="https://api.example.com"
            )
        
        assert "API secret cannot be empty" in str(exc_info.value)
    
    def test_initialization_empty_base_url(self):
        """Test that initialization fails with empty base URL"""
        with pytest.raises(OrderError) as exc_info:
            LiveBrokerAdapter(
                api_key="test_key_12345",
                api_secret="test_secret_12345",
                base_url=""
            )
        
        assert "Base URL cannot be empty" in str(exc_info.value)
    
    def test_initialization_short_api_key(self):
        """Test that initialization fails with too short API key"""
        with pytest.raises(OrderError) as exc_info:
            LiveBrokerAdapter(
                api_key="short",
                api_secret="test_secret_12345",
                base_url="https://api.example.com"
            )
        
        assert "Invalid API key format" in str(exc_info.value)
    
    def test_initialization_short_api_secret(self):
        """Test that initialization fails with too short API secret"""
        with pytest.raises(OrderError) as exc_info:
            LiveBrokerAdapter(
                api_key="test_key_12345",
                api_secret="short",
                base_url="https://api.example.com"
            )
        
        assert "Invalid API secret format" in str(exc_info.value)
    
    def test_base_url_normalization(self):
        """Test that base URL trailing slash is removed"""
        adapter = LiveBrokerAdapter(
            api_key="test_key_12345",
            api_secret="test_secret_12345",
            base_url="https://api.example.com/"
        )
        
        assert adapter._base_url == "https://api.example.com"
    
    def test_verify_connection(self):
        """Test connection verification"""
        adapter = LiveBrokerAdapter(
            api_key="test_key_12345",
            api_secret="test_secret_12345",
            base_url="https://api.example.com"
        )
        
        assert adapter.verify_connection() is True
    
    def test_get_connection_info(self):
        """Test getting connection information"""
        adapter = LiveBrokerAdapter(
            api_key="test_key_12345",
            api_secret="test_secret_12345",
            base_url="https://api.example.com",
            broker_name="alpaca_live"
        )
        
        info = adapter.get_connection_info()
        
        assert info["broker"] == "alpaca_live"
        assert info["base_url"] == "https://api.example.com"
        assert info["authenticated"] is True
        assert info["connection_verified"] is True
        assert info["connected_at"] is not None
    
    def test_place_order_not_implemented(self):
        """Test that live broker adapter returns not implemented error"""
        adapter = LiveBrokerAdapter(
            api_key="test_key_12345",
            api_secret="test_secret_12345",
            base_url="https://api.example.com"
        )
        
        result = adapter.place_order(
            symbol="AAPL",
            quantity=10,
            action=OrderAction.BUY,
            order_type="MARKET"
        )
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "not implemented" in error.message.lower()
        assert error.order_details["authenticated"] is True
    
    def test_place_order_validates_symbol(self):
        """Test that place_order validates empty symbol"""
        adapter = LiveBrokerAdapter(
            api_key="test_key_12345",
            api_secret="test_secret_12345",
            base_url="https://api.example.com"
        )
        
        result = adapter.place_order(
            symbol="",
            quantity=10,
            action=OrderAction.BUY,
            order_type="MARKET"
        )
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid symbol" in error.message
    
    def test_place_order_validates_quantity(self):
        """Test that place_order validates invalid quantity"""
        adapter = LiveBrokerAdapter(
            api_key="test_key_12345",
            api_secret="test_secret_12345",
            base_url="https://api.example.com"
        )
        
        result = adapter.place_order(
            symbol="AAPL",
            quantity=0,
            action=OrderAction.BUY,
            order_type="MARKET"
        )
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid quantity" in error.message
    
    def test_cancel_order_not_implemented(self):
        """Test that cancel order returns not implemented error"""
        adapter = LiveBrokerAdapter(
            api_key="test_key_12345",
            api_secret="test_secret_12345",
            base_url="https://api.example.com"
        )
        
        result = adapter.cancel_order("ORDER-123")
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "not implemented" in error.message.lower()
        assert error.order_details["authenticated"] is True
    
    def test_cancel_order_validates_order_id(self):
        """Test that cancel_order validates empty order ID"""
        adapter = LiveBrokerAdapter(
            api_key="test_key_12345",
            api_secret="test_secret_12345",
            base_url="https://api.example.com"
        )
        
        result = adapter.cancel_order("")
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid order ID" in error.message
    
    def test_get_order_status_not_implemented(self):
        """Test that get order status returns REJECTED for stub"""
        adapter = LiveBrokerAdapter(
            api_key="test_key_12345",
            api_secret="test_secret_12345",
            base_url="https://api.example.com"
        )
        
        status = adapter.get_order_status("ORDER-123")
        
        assert status == OrderStatus.REJECTED
