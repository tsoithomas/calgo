"""Logger for recording trades, portfolio changes, and signals"""
import json
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List

from src.models import TradeRecord, PortfolioSnapshot, Signal, Position, OrderAction, Recommendation


class Logger:
    """Logger for recording all trading activity and portfolio state changes"""
    
    def __init__(self, log_directory: str = "logs"):
        """
        Initialize Logger with log directory
        
        Args:
            log_directory: Directory path for storing log files
        """
        self.log_directory = Path(log_directory)
        self._ensure_log_directories()
    
    def _ensure_log_directories(self) -> None:
        """Create log directory structure if it doesn't exist"""
        # Create main log directory
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different log types
        (self.log_directory / "trades").mkdir(exist_ok=True)
        (self.log_directory / "portfolio").mkdir(exist_ok=True)
        (self.log_directory / "signals").mkdir(exist_ok=True)
        (self.log_directory / "errors").mkdir(exist_ok=True)
    
    def _get_log_file_path(self, log_type: str, date: datetime) -> Path:
        """
        Get log file path for a specific type and date
        
        Args:
            log_type: Type of log (trades, portfolio, signals, errors)
            date: Date for the log file
            
        Returns:
            Path to the log file
        """
        date_str = date.strftime("%Y-%m-%d")
        return self.log_directory / log_type / f"{date_str}.json"
    
    def _serialize_decimal(self, obj):
        """Helper to serialize Decimal objects to string"""
        if isinstance(obj, Decimal):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def _serialize_trade_record(self, trade: TradeRecord) -> dict:
        """Serialize TradeRecord to dictionary"""
        return {
            "timestamp": trade.timestamp.isoformat(),
            "order_id": trade.order_id,
            "symbol": trade.symbol,
            "action": trade.action.value,
            "quantity": trade.quantity,
            "execution_price": str(trade.execution_price)
        }
    
    def _serialize_position(self, position: Position) -> dict:
        """Serialize Position to dictionary"""
        return {
            "symbol": position.symbol,
            "quantity": position.quantity,
            "entry_price": str(position.entry_price),
            "current_price": str(position.current_price),
            "entry_timestamp": position.entry_timestamp.isoformat(),
            "unrealized_pnl": str(position.unrealized_pnl)
        }
    
    def _serialize_portfolio_snapshot(self, snapshot: PortfolioSnapshot) -> dict:
        """Serialize PortfolioSnapshot to dictionary"""
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "positions": [self._serialize_position(p) for p in snapshot.positions],
            "total_value": str(snapshot.total_value),
            "cash_balance": str(snapshot.cash_balance),
            "unrealized_pnl": str(snapshot.unrealized_pnl),
            "realized_pnl": str(snapshot.realized_pnl),
            "drawdown": str(snapshot.drawdown)
        }
    
    def _serialize_signal(self, signal: Signal) -> dict:
        """Serialize Signal to dictionary"""
        return {
            "symbol": signal.symbol,
            "timestamp": signal.timestamp.isoformat(),
            "recommendation": signal.recommendation.value,
            "confidence": signal.confidence,
            "model_id": signal.model_id,
            "metadata": signal.metadata
        }
    
    def _append_to_log_file(self, file_path: Path, data: dict) -> None:
        """
        Append data to log file
        
        Args:
            file_path: Path to log file
            data: Dictionary to append
        """
        # Read existing data if file exists
        if file_path.exists():
            with open(file_path, 'r') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
        else:
            logs = []
        
        # Append new data
        logs.append(data)
        
        # Write back to file
        with open(file_path, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def log_trade(self, trade: TradeRecord) -> None:
        """
        Log a trade record
        
        Args:
            trade: TradeRecord to log
        """
        file_path = self._get_log_file_path("trades", trade.timestamp)
        data = self._serialize_trade_record(trade)
        self._append_to_log_file(file_path, data)
    
    def log_portfolio_change(self, snapshot: PortfolioSnapshot) -> None:
        """
        Log a portfolio state change
        
        Args:
            snapshot: PortfolioSnapshot to log
        """
        file_path = self._get_log_file_path("portfolio", snapshot.timestamp)
        data = self._serialize_portfolio_snapshot(snapshot)
        self._append_to_log_file(file_path, data)
    
    def log_signal(self, signal: Signal) -> None:
        """
        Log a generated signal
        
        Args:
            signal: Signal to log
        """
        file_path = self._get_log_file_path("signals", signal.timestamp)
        data = self._serialize_signal(signal)
        self._append_to_log_file(file_path, data)
    
    def log_error(self, error: dict) -> None:
        """
        Log a system error
        
        Args:
            error: Error dictionary with timestamp, severity, component, error_type, message, context
        """
        timestamp = datetime.fromisoformat(error["timestamp"])
        file_path = self._get_log_file_path("errors", timestamp)
        self._append_to_log_file(file_path, error)
    
    def _deserialize_trade_record(self, data: dict) -> TradeRecord:
        """Deserialize dictionary to TradeRecord"""
        return TradeRecord(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            order_id=data["order_id"],
            symbol=data["symbol"],
            action=OrderAction(data["action"]),
            quantity=data["quantity"],
            execution_price=Decimal(data["execution_price"])
        )
    
    def _deserialize_position(self, data: dict) -> Position:
        """Deserialize dictionary to Position"""
        return Position(
            symbol=data["symbol"],
            quantity=data["quantity"],
            entry_price=Decimal(data["entry_price"]),
            current_price=Decimal(data["current_price"]),
            entry_timestamp=datetime.fromisoformat(data["entry_timestamp"]),
            unrealized_pnl=Decimal(data["unrealized_pnl"])
        )
    
    def _deserialize_portfolio_snapshot(self, data: dict) -> PortfolioSnapshot:
        """Deserialize dictionary to PortfolioSnapshot"""
        return PortfolioSnapshot(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            positions=[self._deserialize_position(p) for p in data["positions"]],
            total_value=Decimal(data["total_value"]),
            cash_balance=Decimal(data["cash_balance"]),
            unrealized_pnl=Decimal(data["unrealized_pnl"]),
            realized_pnl=Decimal(data["realized_pnl"]),
            drawdown=Decimal(data["drawdown"])
        )
    
    def _deserialize_signal(self, data: dict) -> Signal:
        """Deserialize dictionary to Signal"""
        return Signal(
            symbol=data["symbol"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            recommendation=Recommendation(data["recommendation"]),
            confidence=data["confidence"],
            model_id=data["model_id"],
            metadata=data["metadata"]
        )
    
    def _read_logs_in_date_range(self, log_type: str, start_date: datetime, end_date: datetime) -> List[dict]:
        """
        Read all logs of a specific type within a date range
        
        Args:
            log_type: Type of log (trades, portfolio, signals, errors)
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            List of log entries as dictionaries
        """
        logs = []
        
        # Iterate through each day in the range
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date_normalized = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        while current_date <= end_date_normalized:
            file_path = self._get_log_file_path(log_type, current_date)
            
            if file_path.exists():
                with open(file_path, 'r') as f:
                    try:
                        daily_logs = json.load(f)
                        # Filter by timestamp within range
                        for log in daily_logs:
                            log_timestamp = datetime.fromisoformat(log["timestamp"])
                            if start_date <= log_timestamp <= end_date:
                                logs.append(log)
                    except json.JSONDecodeError:
                        pass  # Skip corrupted files
            
            # Move to next day
            from datetime import timedelta
            current_date += timedelta(days=1)
        
        return logs
    
    def get_trade_history(self, start_date: datetime, end_date: datetime) -> List[TradeRecord]:
        """
        Retrieve trade history within a date range
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            List of TradeRecord objects
        """
        logs = self._read_logs_in_date_range("trades", start_date, end_date)
        return [self._deserialize_trade_record(log) for log in logs]
    
    def get_portfolio_history(self, start_date: datetime, end_date: datetime) -> List[PortfolioSnapshot]:
        """
        Retrieve portfolio history within a date range
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            List of PortfolioSnapshot objects
        """
        logs = self._read_logs_in_date_range("portfolio", start_date, end_date)
        return [self._deserialize_portfolio_snapshot(log) for log in logs]
    
    def get_signal_history(self, start_date: datetime, end_date: datetime) -> List[Signal]:
        """
        Retrieve signal history within a date range
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            List of Signal objects
        """
        logs = self._read_logs_in_date_range("signals", start_date, end_date)
        return [self._deserialize_signal(log) for log in logs]
