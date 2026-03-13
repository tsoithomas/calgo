"""Unit tests for Logger"""
import json
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from src.logger import Logger
from src.models import (
    TradeRecord, PortfolioSnapshot, Signal, Position,
    OrderAction, Recommendation, DataSource
)


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logs"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def logger(temp_log_dir):
    """Create a Logger instance with temporary directory"""
    return Logger(log_directory=temp_log_dir)


class TestLoggerInitialization:
    """Test Logger initialization and directory setup (Task 11.1)"""
    
    def test_logger_creates_directory_structure(self, temp_log_dir):
        """Test that Logger creates required directory structure"""
        logger = Logger(log_directory=temp_log_dir)
        
        # Check main directory exists
        assert Path(temp_log_dir).exists()
        
        # Check subdirectories exist
        assert (Path(temp_log_dir) / "trades").exists()
        assert (Path(temp_log_dir) / "portfolio").exists()
        assert (Path(temp_log_dir) / "signals").exists()
        assert (Path(temp_log_dir) / "errors").exists()
    
    def test_logger_with_existing_directory(self, temp_log_dir):
        """Test Logger works with existing directory"""
        # Create directory first
        Path(temp_log_dir).mkdir(parents=True, exist_ok=True)
        
        # Should not raise error
        logger = Logger(log_directory=temp_log_dir)
        assert logger.log_directory == Path(temp_log_dir)


class TestTradeLogging:
    """Test trade logging functionality (Task 11.2)"""
    
    def test_log_trade_creates_file(self, logger, temp_log_dir):
        """Test that logging a trade creates the appropriate file"""
        trade = TradeRecord(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            order_id="ORD-12345",
            symbol="AAPL",
            action=OrderAction.BUY,
            quantity=10,
            execution_price=Decimal("150.25")
        )
        
        logger.log_trade(trade)
        
        # Check file was created
        expected_file = Path(temp_log_dir) / "trades" / "2024-01-15.json"
        assert expected_file.exists()
    
    def test_log_trade_records_all_fields(self, logger, temp_log_dir):
        """Test that all trade fields are recorded (Requirements 5.1)"""
        trade = TradeRecord(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            order_id="ORD-12345",
            symbol="AAPL",
            action=OrderAction.BUY,
            quantity=10,
            execution_price=Decimal("150.25")
        )
        
        logger.log_trade(trade)
        
        # Read and verify
        file_path = Path(temp_log_dir) / "trades" / "2024-01-15.json"
        with open(file_path, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 1
        log = logs[0]
        assert log["timestamp"] == "2024-01-15T10:30:00"
        assert log["order_id"] == "ORD-12345"
        assert log["symbol"] == "AAPL"
        assert log["action"] == "buy"
        assert log["quantity"] == 10
        assert log["execution_price"] == "150.25"
    
    def test_log_multiple_trades_same_day(self, logger, temp_log_dir):
        """Test logging multiple trades on the same day"""
        trade1 = TradeRecord(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            order_id="ORD-001",
            symbol="AAPL",
            action=OrderAction.BUY,
            quantity=10,
            execution_price=Decimal("150.00")
        )
        
        trade2 = TradeRecord(
            timestamp=datetime(2024, 1, 15, 14, 45, 0),
            order_id="ORD-002",
            symbol="GOOGL",
            action=OrderAction.SELL,
            quantity=5,
            execution_price=Decimal("100.00")
        )
        
        logger.log_trade(trade1)
        logger.log_trade(trade2)
        
        # Read and verify
        file_path = Path(temp_log_dir) / "trades" / "2024-01-15.json"
        with open(file_path, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 2
        assert logs[0]["order_id"] == "ORD-001"
        assert logs[1]["order_id"] == "ORD-002"
    
    def test_log_trades_different_days(self, logger, temp_log_dir):
        """Test logging trades on different days creates separate files"""
        trade1 = TradeRecord(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            order_id="ORD-001",
            symbol="AAPL",
            action=OrderAction.BUY,
            quantity=10,
            execution_price=Decimal("150.00")
        )
        
        trade2 = TradeRecord(
            timestamp=datetime(2024, 1, 16, 10, 30, 0),
            order_id="ORD-002",
            symbol="GOOGL",
            action=OrderAction.BUY,
            quantity=5,
            execution_price=Decimal("100.00")
        )
        
        logger.log_trade(trade1)
        logger.log_trade(trade2)
        
        # Check both files exist
        file1 = Path(temp_log_dir) / "trades" / "2024-01-15.json"
        file2 = Path(temp_log_dir) / "trades" / "2024-01-16.json"
        assert file1.exists()
        assert file2.exists()


class TestPortfolioLogging:
    """Test portfolio logging functionality (Task 11.2)"""
    
    def test_log_portfolio_change_creates_file(self, logger, temp_log_dir):
        """Test that logging portfolio change creates the appropriate file"""
        snapshot = PortfolioSnapshot(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            positions=[],
            total_value=Decimal("10000.00"),
            cash_balance=Decimal("10000.00"),
            unrealized_pnl=Decimal("0.00"),
            realized_pnl=Decimal("0.00"),
            drawdown=Decimal("0.00")
        )
        
        logger.log_portfolio_change(snapshot)
        
        # Check file was created
        expected_file = Path(temp_log_dir) / "portfolio" / "2024-01-15.json"
        assert expected_file.exists()
    
    def test_log_portfolio_change_records_all_fields(self, logger, temp_log_dir):
        """Test that all portfolio fields are recorded (Requirements 5.2)"""
        position = Position(
            symbol="AAPL",
            quantity=10,
            entry_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            entry_timestamp=datetime(2024, 1, 15, 9, 0, 0),
            unrealized_pnl=Decimal("50.00")
        )
        
        snapshot = PortfolioSnapshot(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            positions=[position],
            total_value=Decimal("10050.00"),
            cash_balance=Decimal("8500.00"),
            unrealized_pnl=Decimal("50.00"),
            realized_pnl=Decimal("0.00"),
            drawdown=Decimal("0.00")
        )
        
        logger.log_portfolio_change(snapshot)
        
        # Read and verify
        file_path = Path(temp_log_dir) / "portfolio" / "2024-01-15.json"
        with open(file_path, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 1
        log = logs[0]
        assert log["timestamp"] == "2024-01-15T10:30:00"
        assert len(log["positions"]) == 1
        assert log["positions"][0]["symbol"] == "AAPL"
        assert log["positions"][0]["quantity"] == 10
        assert log["total_value"] == "10050.00"
        assert log["cash_balance"] == "8500.00"
        assert log["unrealized_pnl"] == "50.00"
        assert log["realized_pnl"] == "0.00"
        assert log["drawdown"] == "0.00"
    
    def test_log_portfolio_with_multiple_positions(self, logger, temp_log_dir):
        """Test logging portfolio with multiple positions"""
        positions = [
            Position(
                symbol="AAPL",
                quantity=10,
                entry_price=Decimal("150.00"),
                current_price=Decimal("155.00"),
                entry_timestamp=datetime(2024, 1, 15, 9, 0, 0),
                unrealized_pnl=Decimal("50.00")
            ),
            Position(
                symbol="GOOGL",
                quantity=5,
                entry_price=Decimal("100.00"),
                current_price=Decimal("105.00"),
                entry_timestamp=datetime(2024, 1, 15, 9, 30, 0),
                unrealized_pnl=Decimal("25.00")
            )
        ]
        
        snapshot = PortfolioSnapshot(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            positions=positions,
            total_value=Decimal("10075.00"),
            cash_balance=Decimal("8500.00"),
            unrealized_pnl=Decimal("75.00"),
            realized_pnl=Decimal("0.00"),
            drawdown=Decimal("0.00")
        )
        
        logger.log_portfolio_change(snapshot)
        
        # Read and verify
        file_path = Path(temp_log_dir) / "portfolio" / "2024-01-15.json"
        with open(file_path, 'r') as f:
            logs = json.load(f)
        
        assert len(logs[0]["positions"]) == 2
        assert logs[0]["positions"][0]["symbol"] == "AAPL"
        assert logs[0]["positions"][1]["symbol"] == "GOOGL"


class TestSignalLogging:
    """Test signal logging functionality (Task 11.2)"""
    
    def test_log_signal_creates_file(self, logger, temp_log_dir):
        """Test that logging a signal creates the appropriate file"""
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            recommendation=Recommendation.BUY,
            confidence=0.85,
            model_id="ma_crossover_v1",
            metadata={"short_ma": 149.50, "long_ma": 148.00}
        )
        
        logger.log_signal(signal)
        
        # Check file was created
        expected_file = Path(temp_log_dir) / "signals" / "2024-01-15.json"
        assert expected_file.exists()
    
    def test_log_signal_records_all_fields(self, logger, temp_log_dir):
        """Test that all signal fields are recorded (Requirements 5.3)"""
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            recommendation=Recommendation.BUY,
            confidence=0.85,
            model_id="ma_crossover_v1",
            metadata={"short_ma": 149.50, "long_ma": 148.00}
        )
        
        logger.log_signal(signal)
        
        # Read and verify
        file_path = Path(temp_log_dir) / "signals" / "2024-01-15.json"
        with open(file_path, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 1
        log = logs[0]
        assert log["symbol"] == "AAPL"
        assert log["timestamp"] == "2024-01-15T10:30:00"
        assert log["recommendation"] == "buy"
        assert log["confidence"] == 0.85
        assert log["model_id"] == "ma_crossover_v1"
        assert log["metadata"]["short_ma"] == 149.50
        assert log["metadata"]["long_ma"] == 148.00
    
    def test_log_multiple_signals_same_day(self, logger, temp_log_dir):
        """Test logging multiple signals on the same day"""
        signal1 = Signal(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            recommendation=Recommendation.BUY,
            confidence=0.85,
            model_id="model_1",
            metadata={}
        )
        
        signal2 = Signal(
            symbol="GOOGL",
            timestamp=datetime(2024, 1, 15, 14, 45, 0),
            recommendation=Recommendation.SELL,
            confidence=0.75,
            model_id="model_2",
            metadata={}
        )
        
        logger.log_signal(signal1)
        logger.log_signal(signal2)
        
        # Read and verify
        file_path = Path(temp_log_dir) / "signals" / "2024-01-15.json"
        with open(file_path, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 2
        assert logs[0]["symbol"] == "AAPL"
        assert logs[1]["symbol"] == "GOOGL"


class TestErrorLogging:
    """Test error logging functionality (Task 11.2)"""
    
    def test_log_error_creates_file(self, logger, temp_log_dir):
        """Test that logging an error creates the appropriate file"""
        error = {
            "timestamp": "2024-01-15T10:30:00",
            "severity": "ERROR",
            "component": "Trade_Executor",
            "error_type": "OrderRejection",
            "message": "Order rejected by broker",
            "context": {"order_id": "ORD-12345"}
        }
        
        logger.log_error(error)
        
        # Check file was created
        expected_file = Path(temp_log_dir) / "errors" / "2024-01-15.json"
        assert expected_file.exists()
    
    def test_log_error_records_all_fields(self, logger, temp_log_dir):
        """Test that all error fields are recorded"""
        error = {
            "timestamp": "2024-01-15T10:30:00",
            "severity": "ERROR",
            "component": "Trade_Executor",
            "error_type": "OrderRejection",
            "message": "Order rejected by broker: insufficient buying power",
            "context": {
                "order_id": "ORD-12345",
                "symbol": "AAPL",
                "quantity": 100
            }
        }
        
        logger.log_error(error)
        
        # Read and verify
        file_path = Path(temp_log_dir) / "errors" / "2024-01-15.json"
        with open(file_path, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 1
        log = logs[0]
        assert log["timestamp"] == "2024-01-15T10:30:00"
        assert log["severity"] == "ERROR"
        assert log["component"] == "Trade_Executor"
        assert log["error_type"] == "OrderRejection"
        assert log["message"] == "Order rejected by broker: insufficient buying power"
        assert log["context"]["order_id"] == "ORD-12345"


class TestLogRetrieval:
    """Test log retrieval methods (Task 11.3)"""
    
    def test_get_trade_history_single_day(self, logger, temp_log_dir):
        """Test retrieving trade history for a single day"""
        # Log some trades
        trade1 = TradeRecord(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            order_id="ORD-001",
            symbol="AAPL",
            action=OrderAction.BUY,
            quantity=10,
            execution_price=Decimal("150.00")
        )
        
        trade2 = TradeRecord(
            timestamp=datetime(2024, 1, 15, 14, 45, 0),
            order_id="ORD-002",
            symbol="GOOGL",
            action=OrderAction.SELL,
            quantity=5,
            execution_price=Decimal("100.00")
        )
        
        logger.log_trade(trade1)
        logger.log_trade(trade2)
        
        # Retrieve history
        start_date = datetime(2024, 1, 15, 0, 0, 0)
        end_date = datetime(2024, 1, 15, 23, 59, 59)
        history = logger.get_trade_history(start_date, end_date)
        
        assert len(history) == 2
        assert history[0].order_id == "ORD-001"
        assert history[1].order_id == "ORD-002"
    
    def test_get_trade_history_multiple_days(self, logger, temp_log_dir):
        """Test retrieving trade history across multiple days (Requirements 5.8)"""
        # Log trades on different days
        trade1 = TradeRecord(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            order_id="ORD-001",
            symbol="AAPL",
            action=OrderAction.BUY,
            quantity=10,
            execution_price=Decimal("150.00")
        )
        
        trade2 = TradeRecord(
            timestamp=datetime(2024, 1, 16, 10, 30, 0),
            order_id="ORD-002",
            symbol="GOOGL",
            action=OrderAction.BUY,
            quantity=5,
            execution_price=Decimal("100.00")
        )
        
        trade3 = TradeRecord(
            timestamp=datetime(2024, 1, 17, 10, 30, 0),
            order_id="ORD-003",
            symbol="MSFT",
            action=OrderAction.SELL,
            quantity=8,
            execution_price=Decimal("200.00")
        )
        
        logger.log_trade(trade1)
        logger.log_trade(trade2)
        logger.log_trade(trade3)
        
        # Retrieve history for date range
        start_date = datetime(2024, 1, 15, 0, 0, 0)
        end_date = datetime(2024, 1, 17, 23, 59, 59)
        history = logger.get_trade_history(start_date, end_date)
        
        assert len(history) == 3
        assert history[0].order_id == "ORD-001"
        assert history[1].order_id == "ORD-002"
        assert history[2].order_id == "ORD-003"
    
    def test_get_trade_history_partial_range(self, logger, temp_log_dir):
        """Test retrieving trade history for partial date range"""
        # Log trades on different days
        trade1 = TradeRecord(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            order_id="ORD-001",
            symbol="AAPL",
            action=OrderAction.BUY,
            quantity=10,
            execution_price=Decimal("150.00")
        )
        
        trade2 = TradeRecord(
            timestamp=datetime(2024, 1, 16, 10, 30, 0),
            order_id="ORD-002",
            symbol="GOOGL",
            action=OrderAction.BUY,
            quantity=5,
            execution_price=Decimal("100.00")
        )
        
        trade3 = TradeRecord(
            timestamp=datetime(2024, 1, 17, 10, 30, 0),
            order_id="ORD-003",
            symbol="MSFT",
            action=OrderAction.SELL,
            quantity=8,
            execution_price=Decimal("200.00")
        )
        
        logger.log_trade(trade1)
        logger.log_trade(trade2)
        logger.log_trade(trade3)
        
        # Retrieve only middle day
        start_date = datetime(2024, 1, 16, 0, 0, 0)
        end_date = datetime(2024, 1, 16, 23, 59, 59)
        history = logger.get_trade_history(start_date, end_date)
        
        assert len(history) == 1
        assert history[0].order_id == "ORD-002"
    
    def test_get_trade_history_empty_range(self, logger, temp_log_dir):
        """Test retrieving trade history when no trades exist in range"""
        # Log a trade
        trade = TradeRecord(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            order_id="ORD-001",
            symbol="AAPL",
            action=OrderAction.BUY,
            quantity=10,
            execution_price=Decimal("150.00")
        )
        logger.log_trade(trade)
        
        # Query different date range
        start_date = datetime(2024, 1, 20, 0, 0, 0)
        end_date = datetime(2024, 1, 21, 23, 59, 59)
        history = logger.get_trade_history(start_date, end_date)
        
        assert len(history) == 0
    
    def test_get_portfolio_history_single_day(self, logger, temp_log_dir):
        """Test retrieving portfolio history for a single day"""
        # Log portfolio snapshots
        snapshot1 = PortfolioSnapshot(
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            positions=[],
            total_value=Decimal("10000.00"),
            cash_balance=Decimal("10000.00"),
            unrealized_pnl=Decimal("0.00"),
            realized_pnl=Decimal("0.00"),
            drawdown=Decimal("0.00")
        )
        
        snapshot2 = PortfolioSnapshot(
            timestamp=datetime(2024, 1, 15, 15, 0, 0),
            positions=[],
            total_value=Decimal("10050.00"),
            cash_balance=Decimal("10050.00"),
            unrealized_pnl=Decimal("0.00"),
            realized_pnl=Decimal("50.00"),
            drawdown=Decimal("0.00")
        )
        
        logger.log_portfolio_change(snapshot1)
        logger.log_portfolio_change(snapshot2)
        
        # Retrieve history
        start_date = datetime(2024, 1, 15, 0, 0, 0)
        end_date = datetime(2024, 1, 15, 23, 59, 59)
        history = logger.get_portfolio_history(start_date, end_date)
        
        assert len(history) == 2
        assert history[0].total_value == Decimal("10000.00")
        assert history[1].total_value == Decimal("10050.00")
    
    def test_get_portfolio_history_multiple_days(self, logger, temp_log_dir):
        """Test retrieving portfolio history across multiple days (Requirements 5.8)"""
        # Log snapshots on different days
        snapshot1 = PortfolioSnapshot(
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            positions=[],
            total_value=Decimal("10000.00"),
            cash_balance=Decimal("10000.00"),
            unrealized_pnl=Decimal("0.00"),
            realized_pnl=Decimal("0.00"),
            drawdown=Decimal("0.00")
        )
        
        snapshot2 = PortfolioSnapshot(
            timestamp=datetime(2024, 1, 16, 10, 0, 0),
            positions=[],
            total_value=Decimal("10050.00"),
            cash_balance=Decimal("10050.00"),
            unrealized_pnl=Decimal("0.00"),
            realized_pnl=Decimal("50.00"),
            drawdown=Decimal("0.00")
        )
        
        logger.log_portfolio_change(snapshot1)
        logger.log_portfolio_change(snapshot2)
        
        # Retrieve history
        start_date = datetime(2024, 1, 15, 0, 0, 0)
        end_date = datetime(2024, 1, 16, 23, 59, 59)
        history = logger.get_portfolio_history(start_date, end_date)
        
        assert len(history) == 2
        assert history[0].timestamp.day == 15
        assert history[1].timestamp.day == 16
    
    def test_get_signal_history_single_day(self, logger, temp_log_dir):
        """Test retrieving signal history for a single day"""
        # Log signals
        signal1 = Signal(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            recommendation=Recommendation.BUY,
            confidence=0.85,
            model_id="model_1",
            metadata={}
        )
        
        signal2 = Signal(
            symbol="GOOGL",
            timestamp=datetime(2024, 1, 15, 14, 45, 0),
            recommendation=Recommendation.SELL,
            confidence=0.75,
            model_id="model_2",
            metadata={}
        )
        
        logger.log_signal(signal1)
        logger.log_signal(signal2)
        
        # Retrieve history
        start_date = datetime(2024, 1, 15, 0, 0, 0)
        end_date = datetime(2024, 1, 15, 23, 59, 59)
        history = logger.get_signal_history(start_date, end_date)
        
        assert len(history) == 2
        assert history[0].symbol == "AAPL"
        assert history[1].symbol == "GOOGL"
    
    def test_get_signal_history_multiple_days(self, logger, temp_log_dir):
        """Test retrieving signal history across multiple days (Requirements 5.8)"""
        # Log signals on different days
        signal1 = Signal(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            recommendation=Recommendation.BUY,
            confidence=0.85,
            model_id="model_1",
            metadata={}
        )
        
        signal2 = Signal(
            symbol="GOOGL",
            timestamp=datetime(2024, 1, 16, 10, 30, 0),
            recommendation=Recommendation.SELL,
            confidence=0.75,
            model_id="model_2",
            metadata={}
        )
        
        signal3 = Signal(
            symbol="MSFT",
            timestamp=datetime(2024, 1, 17, 10, 30, 0),
            recommendation=Recommendation.HOLD,
            confidence=0.60,
            model_id="model_3",
            metadata={}
        )
        
        logger.log_signal(signal1)
        logger.log_signal(signal2)
        logger.log_signal(signal3)
        
        # Retrieve history
        start_date = datetime(2024, 1, 15, 0, 0, 0)
        end_date = datetime(2024, 1, 17, 23, 59, 59)
        history = logger.get_signal_history(start_date, end_date)
        
        assert len(history) == 3
        assert history[0].symbol == "AAPL"
        assert history[1].symbol == "GOOGL"
        assert history[2].symbol == "MSFT"
    
    def test_get_signal_history_empty_range(self, logger, temp_log_dir):
        """Test retrieving signal history when no signals exist in range"""
        # Log a signal
        signal = Signal(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            recommendation=Recommendation.BUY,
            confidence=0.85,
            model_id="model_1",
            metadata={}
        )
        logger.log_signal(signal)
        
        # Query different date range
        start_date = datetime(2024, 1, 20, 0, 0, 0)
        end_date = datetime(2024, 1, 21, 23, 59, 59)
        history = logger.get_signal_history(start_date, end_date)
        
        assert len(history) == 0


class TestSerializationRoundTrip:
    """Test serialization and deserialization round-trip"""
    
    def test_trade_record_round_trip(self, logger, temp_log_dir):
        """Test TradeRecord serialization round-trip"""
        original = TradeRecord(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            order_id="ORD-12345",
            symbol="AAPL",
            action=OrderAction.BUY,
            quantity=10,
            execution_price=Decimal("150.25")
        )
        
        logger.log_trade(original)
        
        # Retrieve and compare
        history = logger.get_trade_history(
            datetime(2024, 1, 15, 0, 0, 0),
            datetime(2024, 1, 15, 23, 59, 59)
        )
        
        assert len(history) == 1
        retrieved = history[0]
        assert retrieved.timestamp == original.timestamp
        assert retrieved.order_id == original.order_id
        assert retrieved.symbol == original.symbol
        assert retrieved.action == original.action
        assert retrieved.quantity == original.quantity
        assert retrieved.execution_price == original.execution_price
    
    def test_portfolio_snapshot_round_trip(self, logger, temp_log_dir):
        """Test PortfolioSnapshot serialization round-trip"""
        position = Position(
            symbol="AAPL",
            quantity=10,
            entry_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            entry_timestamp=datetime(2024, 1, 15, 9, 0, 0),
            unrealized_pnl=Decimal("50.00")
        )
        
        original = PortfolioSnapshot(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            positions=[position],
            total_value=Decimal("10050.00"),
            cash_balance=Decimal("8500.00"),
            unrealized_pnl=Decimal("50.00"),
            realized_pnl=Decimal("0.00"),
            drawdown=Decimal("0.00")
        )
        
        logger.log_portfolio_change(original)
        
        # Retrieve and compare
        history = logger.get_portfolio_history(
            datetime(2024, 1, 15, 0, 0, 0),
            datetime(2024, 1, 15, 23, 59, 59)
        )
        
        assert len(history) == 1
        retrieved = history[0]
        assert retrieved.timestamp == original.timestamp
        assert len(retrieved.positions) == 1
        assert retrieved.positions[0].symbol == position.symbol
        assert retrieved.positions[0].quantity == position.quantity
        assert retrieved.total_value == original.total_value
        assert retrieved.cash_balance == original.cash_balance
    
    def test_signal_round_trip(self, logger, temp_log_dir):
        """Test Signal serialization round-trip"""
        original = Signal(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            recommendation=Recommendation.BUY,
            confidence=0.85,
            model_id="ma_crossover_v1",
            metadata={"short_ma": 149.50, "long_ma": 148.00}
        )
        
        logger.log_signal(original)
        
        # Retrieve and compare
        history = logger.get_signal_history(
            datetime(2024, 1, 15, 0, 0, 0),
            datetime(2024, 1, 15, 23, 59, 59)
        )
        
        assert len(history) == 1
        retrieved = history[0]
        assert retrieved.symbol == original.symbol
        assert retrieved.timestamp == original.timestamp
        assert retrieved.recommendation == original.recommendation
        assert retrieved.confidence == original.confidence
        assert retrieved.model_id == original.model_id
        assert retrieved.metadata == original.metadata
