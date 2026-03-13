"""Unit tests for Portfolio Manager"""
import pytest
from decimal import Decimal
from datetime import datetime

from src.portfolio_manager import PortfolioManager, PortfolioError
from src.models import Position, ClosedPosition, OrderAction


class TestPositionTrackingDataStructures:
    """Test position tracking data structures (Task 6.1)"""
    
    def test_portfolio_manager_initialization(self):
        """Test Portfolio Manager initializes with correct data structures"""
        initial_cash = Decimal("10000.00")
        max_portfolio_value = Decimal("50000.00")
        max_position_size_pct = Decimal("0.20")
        
        pm = PortfolioManager(
            initial_cash=initial_cash,
            max_portfolio_value=max_portfolio_value,
            max_position_size_pct=max_position_size_pct
        )
        
        # Verify internal storage structures exist and are empty
        assert hasattr(pm, '_open_positions')
        assert hasattr(pm, '_closed_positions')
        assert isinstance(pm._open_positions, dict)
        assert isinstance(pm._closed_positions, list)
        assert len(pm._open_positions) == 0
        assert len(pm._closed_positions) == 0
        
        # Verify cash balance initialized correctly
        assert pm._cash_balance == initial_cash
        assert pm._initial_cash == initial_cash
        
        # Verify limits stored correctly
        assert pm._max_portfolio_value == max_portfolio_value
        assert pm._max_position_size_pct == max_position_size_pct
        
        # Verify peak value initialized to initial cash
        assert pm._peak_value == initial_cash
    
    def test_open_positions_storage_structure(self):
        """Test open positions storage is a dictionary keyed by symbol"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        # Verify storage structure
        assert isinstance(pm._open_positions, dict)
        
        # Manually add a position to verify structure works
        position = Position(
            symbol="AAPL",
            quantity=10,
            entry_price=Decimal("150.00"),
            current_price=Decimal("150.00"),
            entry_timestamp=datetime.now(),
            unrealized_pnl=Decimal("0.00")
        )
        pm._open_positions["AAPL"] = position
        
        # Verify retrieval
        assert "AAPL" in pm._open_positions
        assert pm._open_positions["AAPL"].symbol == "AAPL"
        assert pm._open_positions["AAPL"].quantity == 10
    
    def test_closed_positions_storage_structure(self):
        """Test closed positions storage is a list"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        # Verify storage structure
        assert isinstance(pm._closed_positions, list)
        
        # Manually add a closed position to verify structure works
        closed_position = ClosedPosition(
            symbol="AAPL",
            quantity=10,
            entry_price=Decimal("150.00"),
            exit_price=Decimal("155.00"),
            entry_timestamp=datetime.now(),
            exit_timestamp=datetime.now(),
            realized_pnl=Decimal("50.00")
        )
        pm._closed_positions.append(closed_position)
        
        # Verify retrieval
        assert len(pm._closed_positions) == 1
        assert pm._closed_positions[0].symbol == "AAPL"
        assert pm._closed_positions[0].realized_pnl == Decimal("50.00")
    
    def test_position_dataclass_fields(self):
        """Test Position dataclass has all required fields per Requirements 3.1"""
        position = Position(
            symbol="AAPL",
            quantity=10,
            entry_price=Decimal("150.00"),
            current_price=Decimal("152.00"),
            entry_timestamp=datetime.now(),
            unrealized_pnl=Decimal("20.00")
        )
        
        # Verify all required fields exist
        assert hasattr(position, 'symbol')
        assert hasattr(position, 'quantity')
        assert hasattr(position, 'entry_price')
        assert hasattr(position, 'current_price')
        assert hasattr(position, 'entry_timestamp')
        assert hasattr(position, 'unrealized_pnl')
        
        # Verify field values
        assert position.symbol == "AAPL"
        assert position.quantity == 10
        assert position.entry_price == Decimal("150.00")
        assert position.current_price == Decimal("152.00")
        assert position.unrealized_pnl == Decimal("20.00")
    
    def test_closed_position_dataclass_fields(self):
        """Test ClosedPosition dataclass has all required fields per Requirements 3.2"""
        entry_time = datetime.now()
        exit_time = datetime.now()
        
        closed_position = ClosedPosition(
            symbol="AAPL",
            quantity=10,
            entry_price=Decimal("150.00"),
            exit_price=Decimal("155.00"),
            entry_timestamp=entry_time,
            exit_timestamp=exit_time,
            realized_pnl=Decimal("50.00")
        )
        
        # Verify all required fields exist
        assert hasattr(closed_position, 'symbol')
        assert hasattr(closed_position, 'quantity')
        assert hasattr(closed_position, 'entry_price')
        assert hasattr(closed_position, 'exit_price')
        assert hasattr(closed_position, 'entry_timestamp')
        assert hasattr(closed_position, 'exit_timestamp')
        assert hasattr(closed_position, 'realized_pnl')
        
        # Verify field values
        assert closed_position.symbol == "AAPL"
        assert closed_position.quantity == 10
        assert closed_position.entry_price == Decimal("150.00")
        assert closed_position.exit_price == Decimal("155.00")
        assert closed_position.entry_timestamp == entry_time
        assert closed_position.exit_timestamp == exit_time
        assert closed_position.realized_pnl == Decimal("50.00")


class TestPositionManagement:
    """Test position management methods (Task 6.2)"""
    
    def test_add_position_success(self):
        """Test successfully adding a new position"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        result = pm.add_position("AAPL", 10, Decimal("150.00"))
        
        assert result.is_ok()
        position = result.unwrap()
        assert position.symbol == "AAPL"
        assert position.quantity == 10
        assert position.entry_price == Decimal("150.00")
        assert position.current_price == Decimal("150.00")
        assert position.unrealized_pnl == Decimal("0.00")
        
        # Verify cash balance updated
        assert pm._cash_balance == Decimal("8500.00")  # 10000 - (10 * 150)
        
        # Verify position stored
        assert "AAPL" in pm._open_positions
    
    def test_add_position_duplicate_symbol(self):
        """Test adding position for symbol that already exists"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        result = pm.add_position("AAPL", 5, Decimal("155.00"))
        
        assert result.is_err()
        assert "already exists" in str(result.unwrap_err())
    
    def test_add_position_insufficient_cash(self):
        """Test adding position with insufficient cash"""
        pm = PortfolioManager(
            initial_cash=Decimal("1000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        result = pm.add_position("AAPL", 10, Decimal("150.00"))
        
        assert result.is_err()
        assert "Insufficient cash" in str(result.unwrap_err())
    
    def test_add_position_invalid_quantity(self):
        """Test adding position with invalid quantity"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        result = pm.add_position("AAPL", 0, Decimal("150.00"))
        assert result.is_err()
        
        result = pm.add_position("AAPL", -5, Decimal("150.00"))
        assert result.is_err()
    
    def test_add_position_invalid_price(self):
        """Test adding position with invalid price"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        result = pm.add_position("AAPL", 10, Decimal("0.00"))
        assert result.is_err()
        
        result = pm.add_position("AAPL", 10, Decimal("-150.00"))
        assert result.is_err()
    
    def test_close_position_success(self):
        """Test successfully closing a position"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        result = pm.close_position("AAPL", Decimal("155.00"))
        
        assert result.is_ok()
        closed = result.unwrap()
        assert closed.symbol == "AAPL"
        assert closed.quantity == 10
        assert closed.entry_price == Decimal("150.00")
        assert closed.exit_price == Decimal("155.00")
        assert closed.realized_pnl == Decimal("50.00")  # (155 - 150) * 10
        
        # Verify cash balance updated
        assert pm._cash_balance == Decimal("10050.00")  # 8500 + (10 * 155)
        
        # Verify position removed from open and added to closed
        assert "AAPL" not in pm._open_positions
        assert len(pm._closed_positions) == 1
    
    def test_close_position_with_loss(self):
        """Test closing a position with a loss"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        result = pm.close_position("AAPL", Decimal("145.00"))
        
        assert result.is_ok()
        closed = result.unwrap()
        assert closed.realized_pnl == Decimal("-50.00")  # (145 - 150) * 10
        
        # Verify cash balance
        assert pm._cash_balance == Decimal("9950.00")  # 8500 + (10 * 145)
    
    def test_close_position_nonexistent(self):
        """Test closing a position that doesn't exist"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        result = pm.close_position("AAPL", Decimal("155.00"))
        
        assert result.is_err()
        assert "No open position" in str(result.unwrap_err())
    
    def test_close_position_invalid_price(self):
        """Test closing position with invalid price"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        
        result = pm.close_position("AAPL", Decimal("0.00"))
        assert result.is_err()
        
        result = pm.close_position("AAPL", Decimal("-155.00"))
        assert result.is_err()
    
    def test_update_position_success(self):
        """Test successfully updating a position"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        pm.update_position("AAPL", Decimal("155.00"))
        
        position = pm._open_positions["AAPL"]
        assert position.current_price == Decimal("155.00")
        assert position.unrealized_pnl == Decimal("50.00")  # (155 - 150) * 10
    
    def test_update_position_with_loss(self):
        """Test updating position with a loss"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        pm.update_position("AAPL", Decimal("145.00"))
        
        position = pm._open_positions["AAPL"]
        assert position.current_price == Decimal("145.00")
        assert position.unrealized_pnl == Decimal("-50.00")  # (145 - 150) * 10
    
    def test_update_position_nonexistent(self):
        """Test updating a position that doesn't exist"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        with pytest.raises(PortfolioError):
            pm.update_position("AAPL", Decimal("155.00"))
    
    def test_update_position_invalid_price(self):
        """Test updating position with invalid price"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        
        with pytest.raises(PortfolioError):
            pm.update_position("AAPL", Decimal("0.00"))
        
        with pytest.raises(PortfolioError):
            pm.update_position("AAPL", Decimal("-155.00"))
    
    def test_get_position_exists(self):
        """Test getting an existing position"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        option = pm.get_position("AAPL")
        
        assert option.is_some()
        position = option.unwrap()
        assert position.symbol == "AAPL"
        assert position.quantity == 10
    
    def test_get_position_nonexistent(self):
        """Test getting a position that doesn't exist"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        option = pm.get_position("AAPL")
        assert option.is_none()
    
    def test_get_all_positions_empty(self):
        """Test getting all positions when none exist"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        positions = pm.get_all_positions()
        assert len(positions) == 0
    
    def test_get_all_positions_multiple(self):
        """Test getting all positions with multiple open positions"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        pm.add_position("GOOGL", 5, Decimal("100.00"))
        pm.add_position("MSFT", 20, Decimal("50.00"))
        
        positions = pm.get_all_positions()
        assert len(positions) == 3
        
        symbols = {p.symbol for p in positions}
        assert symbols == {"AAPL", "GOOGL", "MSFT"}


class TestPortfolioMetrics:
    """Test portfolio metrics calculation (Task 6.3)"""
    
    def test_calculate_unrealized_pnl_empty(self):
        """Test unrealized P&L with no positions"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        assert pm.calculate_unrealized_pnl() == Decimal("0.00")
    
    def test_calculate_unrealized_pnl_single_position(self):
        """Test unrealized P&L with single position"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        pm.update_position("AAPL", Decimal("155.00"))
        
        assert pm.calculate_unrealized_pnl() == Decimal("50.00")
    
    def test_calculate_unrealized_pnl_multiple_positions(self):
        """Test unrealized P&L with multiple positions"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        pm.update_position("AAPL", Decimal("155.00"))  # +50
        
        pm.add_position("GOOGL", 5, Decimal("100.00"))
        pm.update_position("GOOGL", Decimal("95.00"))  # -25
        
        assert pm.calculate_unrealized_pnl() == Decimal("25.00")  # 50 - 25
    
    def test_calculate_realized_pnl_empty(self):
        """Test realized P&L with no closed positions"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        assert pm.calculate_realized_pnl() == Decimal("0.00")
    
    def test_calculate_realized_pnl_single_position(self):
        """Test realized P&L with single closed position"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        pm.close_position("AAPL", Decimal("155.00"))
        
        assert pm.calculate_realized_pnl() == Decimal("50.00")
    
    def test_calculate_realized_pnl_multiple_positions(self):
        """Test realized P&L with multiple closed positions"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        pm.close_position("AAPL", Decimal("155.00"))  # +50
        
        pm.add_position("GOOGL", 5, Decimal("100.00"))
        pm.close_position("GOOGL", Decimal("95.00"))  # -25
        
        assert pm.calculate_realized_pnl() == Decimal("25.00")  # 50 - 25
    
    def test_get_allocation_empty_portfolio(self):
        """Test allocation with no positions"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        assert pm.get_allocation("AAPL") == Decimal("0.00")
    
    def test_get_allocation_nonexistent_position(self):
        """Test allocation for position that doesn't exist"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        
        assert pm.get_allocation("GOOGL") == Decimal("0.00")
    
    def test_get_allocation_single_position(self):
        """Test allocation with single position"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        # Total value: 8500 cash + 1500 position = 10000
        # Position value: 1500
        # Allocation: 1500 / 10000 = 0.15
        
        allocation = pm.get_allocation("AAPL")
        assert allocation == Decimal("0.15")
    
    def test_get_allocation_multiple_positions(self):
        """Test allocation with multiple positions"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))  # 1500
        pm.add_position("GOOGL", 5, Decimal("100.00"))  # 500
        # Total value: 8000 cash + 1500 + 500 = 10000
        
        assert pm.get_allocation("AAPL") == Decimal("0.15")
        assert pm.get_allocation("GOOGL") == Decimal("0.05")
    
    def test_get_total_value_cash_only(self):
        """Test total value with only cash"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        assert pm.get_total_value() == Decimal("10000.00")
    
    def test_get_total_value_with_positions(self):
        """Test total value with positions"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        # Cash: 8500, Position: 1500, Total: 10000
        
        assert pm.get_total_value() == Decimal("10000.00")
    
    def test_get_total_value_with_price_changes(self):
        """Test total value after price changes"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        pm.update_position("AAPL", Decimal("155.00"))
        # Cash: 8500, Position: 1550, Total: 10050
        
        assert pm.get_total_value() == Decimal("10050.00")
    
    def test_get_snapshot_empty_portfolio(self):
        """Test snapshot with empty portfolio"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        snapshot = pm.get_snapshot()
        
        assert len(snapshot.positions) == 0
        assert snapshot.total_value == Decimal("10000.00")
        assert snapshot.cash_balance == Decimal("10000.00")
        assert snapshot.unrealized_pnl == Decimal("0.00")
        assert snapshot.realized_pnl == Decimal("0.00")
        assert snapshot.drawdown == Decimal("0.00")
    
    def test_get_snapshot_with_positions(self):
        """Test snapshot with open positions"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        pm.update_position("AAPL", Decimal("155.00"))
        
        snapshot = pm.get_snapshot()
        
        assert len(snapshot.positions) == 1
        assert snapshot.positions[0].symbol == "AAPL"
        assert snapshot.total_value == Decimal("10050.00")
        assert snapshot.cash_balance == Decimal("8500.00")
        assert snapshot.unrealized_pnl == Decimal("50.00")
        assert snapshot.realized_pnl == Decimal("0.00")
        assert snapshot.drawdown == Decimal("0.00")  # No drawdown yet
    
    def test_get_snapshot_with_drawdown(self):
        """Test snapshot with drawdown"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        pm.add_position("AAPL", 10, Decimal("150.00"))
        pm.update_position("AAPL", Decimal("160.00"))
        pm.get_snapshot()  # Peak value: 10100
        
        pm.update_position("AAPL", Decimal("145.00"))
        snapshot = pm.get_snapshot()
        
        # Peak: 10100, Current: 9950
        # Drawdown: (10100 - 9950) / 10100 = 150 / 10100 ≈ 0.0148...
        assert snapshot.drawdown > Decimal("0.01")
        assert snapshot.drawdown < Decimal("0.02")
    
    def test_get_snapshot_with_realized_and_unrealized_pnl(self):
        """Test snapshot with both realized and unrealized P&L"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        # First position: close with profit
        pm.add_position("AAPL", 10, Decimal("150.00"))
        pm.close_position("AAPL", Decimal("155.00"))  # +50 realized
        
        # Second position: open with unrealized profit
        pm.add_position("GOOGL", 5, Decimal("100.00"))
        pm.update_position("GOOGL", Decimal("110.00"))  # +50 unrealized
        
        snapshot = pm.get_snapshot()
        
        assert snapshot.realized_pnl == Decimal("50.00")
        assert snapshot.unrealized_pnl == Decimal("50.00")


class TestPortfolioLimits:
    """Test portfolio limits enforcement (Task 6.4)"""
    
    def test_check_position_limit_within_limit(self):
        """Test position within size limit"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")  # 20% max
        )
        
        # Position value: 1500, Total: 10000, Percentage: 15%
        assert pm.check_position_limit("AAPL", 10, Decimal("150.00")) is True
    
    def test_check_position_limit_at_limit(self):
        """Test position exactly at size limit"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")  # 20% max
        )
        
        # Position value: 2000, Total: 10000, Percentage: 20%
        assert pm.check_position_limit("AAPL", 10, Decimal("200.00")) is True
    
    def test_check_position_limit_exceeds_limit(self):
        """Test position exceeding size limit"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")  # 20% max
        )
        
        # Position value: 2500, Total: 10000, Percentage: 25%
        assert pm.check_position_limit("AAPL", 10, Decimal("250.00")) is False
    
    def test_check_position_limit_zero_portfolio_value(self):
        """Test position limit check with zero portfolio value"""
        pm = PortfolioManager(
            initial_cash=Decimal("0.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        # Should return False when total value is zero
        assert pm.check_position_limit("AAPL", 10, Decimal("150.00")) is False
    
    def test_check_portfolio_limit_within_limit(self):
        """Test portfolio value within limit"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        assert pm.check_portfolio_limit(Decimal("30000.00")) is True
    
    def test_check_portfolio_limit_at_limit(self):
        """Test portfolio value exactly at limit"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        assert pm.check_portfolio_limit(Decimal("50000.00")) is True
    
    def test_check_portfolio_limit_exceeds_limit(self):
        """Test portfolio value exceeding limit"""
        pm = PortfolioManager(
            initial_cash=Decimal("10000.00"),
            max_portfolio_value=Decimal("50000.00"),
            max_position_size_pct=Decimal("0.20")
        )
        
        assert pm.check_portfolio_limit(Decimal("50001.00")) is False
