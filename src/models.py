"""Core data models for Calgo trading bot"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


# Enums
class ExecutionMode(Enum):
    """Trading execution mode"""
    SIMULATION = "simulation"
    LIVE = "live"


class Recommendation(Enum):
    """Trading signal recommendation"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class OrderAction(Enum):
    """Order action type"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type"""
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class DataSource(Enum):
    """Market data source"""
    YAHOO_FINANCE = "yahoo_finance"
    ALPACA = "alpaca"
    ALPHA_VANTAGE = "alpha_vantage"


class RiskViolation(Enum):
    """Risk management violation types"""
    STOP_LOSS_BREACHED = "stop_loss_breached"
    TAKE_PROFIT_REACHED = "take_profit_reached"
    POSITION_SIZE_EXCEEDED = "position_size_exceeded"
    PORTFOLIO_LIMIT_EXCEEDED = "portfolio_limit_exceeded"
    DRAWDOWN_LIMIT_EXCEEDED = "drawdown_limit_exceeded"


class SystemState(Enum):
    """System lifecycle states"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    HALTED = "halted"
    SHUTDOWN = "shutdown"


# Core Data Models
@dataclass
class PriceData:
    """Market price data"""
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    source: DataSource


@dataclass
class Signal:
    """Trading signal from AI model"""
    symbol: str
    timestamp: datetime
    recommendation: Recommendation
    confidence: float  # 0.0 to 1.0
    model_id: str
    metadata: Dict[str, Any]


@dataclass
class Position:
    """Open position in portfolio"""
    symbol: str
    quantity: int
    entry_price: Decimal
    current_price: Decimal
    entry_timestamp: datetime
    unrealized_pnl: Decimal


@dataclass
class Order:
    """Order to be submitted"""
    symbol: str
    quantity: int
    action: OrderAction
    order_type: OrderType
    limit_price: Optional[Decimal] = None


@dataclass
class OrderConfirmation:
    """Order execution confirmation"""
    order_id: str
    symbol: str
    quantity: int
    execution_price: Decimal
    timestamp: datetime
    status: OrderStatus


@dataclass
class ClosedPosition:
    """Closed position with realized P&L"""
    symbol: str
    quantity: int
    entry_price: Decimal
    exit_price: Decimal
    entry_timestamp: datetime
    exit_timestamp: datetime
    realized_pnl: Decimal


@dataclass
class PortfolioSnapshot:
    """Complete portfolio state at a point in time"""
    timestamp: datetime
    positions: List[Position]
    total_value: Decimal
    cash_balance: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    drawdown: Decimal


@dataclass
class TradeRecord:
    """Record of executed trade"""
    timestamp: datetime
    order_id: str
    symbol: str
    action: OrderAction
    quantity: int
    execution_price: Decimal
