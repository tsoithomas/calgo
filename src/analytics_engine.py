"""Analytics Engine for performance metrics and visualization"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
import math

from src.logger import Logger
from src.models import PortfolioSnapshot, TradeRecord, Signal, OrderAction


@dataclass
class ModelMetrics:
    """Performance metrics for a specific model"""
    model_id: str
    total_signals: int
    profitable_signals: int
    win_rate: float
    average_return: float
    sharpe_ratio: float


class AnalyticsEngine:
    """Analytics Engine for calculating performance metrics and generating visualizations"""
    
    def __init__(self, logger: Logger):
        """
        Initialize Analytics Engine
        
        Args:
            logger: Logger instance for retrieving historical data
        """
        self.logger = logger
    
    def calculate_cumulative_returns(
        self,
        portfolio_history: List[PortfolioSnapshot]
    ) -> float:
        """
        Calculate cumulative returns from portfolio history
        
        Formula: (final_value - initial_value) / initial_value
        
        Args:
            portfolio_history: List of PortfolioSnapshot objects sorted by timestamp
            
        Returns:
            Cumulative return as a decimal (e.g., 0.15 for 15% return)
        """
        if not portfolio_history or len(portfolio_history) < 2:
            return 0.0
        
        initial_value = float(portfolio_history[0].total_value)
        final_value = float(portfolio_history[-1].total_value)
        
        if initial_value == 0:
            return 0.0
        
        return (final_value - initial_value) / initial_value
    
    def calculate_sharpe_ratio(
        self,
        portfolio_history: List[PortfolioSnapshot],
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sharpe ratio from portfolio history
        
        Formula: mean(returns) / std(returns) × sqrt(periods)
        
        Args:
            portfolio_history: List of PortfolioSnapshot objects sorted by timestamp
            periods_per_year: Number of periods per year (252 for daily trading days)
            
        Returns:
            Annualized Sharpe ratio
        """
        if not portfolio_history or len(portfolio_history) < 2:
            return 0.0
        
        # Calculate period returns
        returns = []
        for i in range(1, len(portfolio_history)):
            prev_value = float(portfolio_history[i-1].total_value)
            curr_value = float(portfolio_history[i].total_value)
            
            if prev_value == 0:
                continue
            
            period_return = (curr_value - prev_value) / prev_value
            returns.append(period_return)
        
        if not returns:
            return 0.0
        
        # Calculate mean and standard deviation
        mean_return = sum(returns) / len(returns)
        
        if len(returns) < 2:
            return 0.0
        
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_return = math.sqrt(variance)
        
        if std_return == 0:
            return 0.0
        
        # Annualize the Sharpe ratio
        sharpe = (mean_return / std_return) * math.sqrt(periods_per_year)
        
        return sharpe
    
    def calculate_max_drawdown(
        self,
        portfolio_history: List[PortfolioSnapshot]
    ) -> float:
        """
        Calculate maximum drawdown from portfolio history
        
        Maximum drawdown is the largest peak-to-trough decline
        
        Args:
            portfolio_history: List of PortfolioSnapshot objects sorted by timestamp
            
        Returns:
            Maximum drawdown as a decimal (e.g., 0.20 for 20% drawdown)
        """
        if not portfolio_history:
            return 0.0
        
        max_drawdown = 0.0
        peak_value = float(portfolio_history[0].total_value)
        
        for snapshot in portfolio_history:
            current_value = float(snapshot.total_value)
            
            # Update peak if we have a new high
            if current_value > peak_value:
                peak_value = current_value
            
            # Calculate drawdown from peak
            if peak_value > 0:
                drawdown = (peak_value - current_value) / peak_value
                max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def get_model_performance(
        self,
        start_date: datetime,
        end_date: datetime,
        model_id: Optional[str] = None
    ) -> Dict[str, ModelMetrics]:
        """
        Calculate performance metrics per model
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            model_id: Optional specific model ID to filter by
            
        Returns:
            Dictionary mapping model_id to ModelMetrics
        """
        # Get signal and trade history
        signals = self.logger.get_signal_history(start_date, end_date)
        trades = self.logger.get_trade_history(start_date, end_date)
        
        # Filter by model_id if specified
        if model_id:
            signals = [s for s in signals if s.model_id == model_id]
        
        # Group signals by model
        model_signals: Dict[str, List[Signal]] = {}
        for signal in signals:
            if signal.model_id not in model_signals:
                model_signals[signal.model_id] = []
            model_signals[signal.model_id].append(signal)
        
        # Calculate metrics for each model
        model_metrics = {}
        
        for mid, sigs in model_signals.items():
            # Match signals to trades to determine profitability
            profitable_count = 0
            returns = []
            
            # Create a mapping of symbol/timestamp to trades
            buy_trades = {(t.symbol, t.timestamp): t for t in trades if t.action == OrderAction.BUY}
            sell_trades = {(t.symbol, t.timestamp): t for t in trades if t.action == OrderAction.SELL}
            
            # For each signal, try to find corresponding trades
            for sig in sigs:
                # Find trades that occurred shortly after this signal (within reasonable time window)
                matching_buys = [t for t in trades 
                               if t.symbol == sig.symbol 
                               and t.action == OrderAction.BUY
                               and abs((t.timestamp - sig.timestamp).total_seconds()) < 3600]
                
                matching_sells = [t for t in trades 
                                if t.symbol == sig.symbol 
                                and t.action == OrderAction.SELL
                                and abs((t.timestamp - sig.timestamp).total_seconds()) < 3600]
                
                # Calculate return if we have matching trades
                if matching_buys and matching_sells:
                    buy_price = float(matching_buys[0].execution_price)
                    sell_price = float(matching_sells[0].execution_price)
                    
                    if buy_price > 0:
                        trade_return = (sell_price - buy_price) / buy_price
                        returns.append(trade_return)
                        
                        if trade_return > 0:
                            profitable_count += 1
            
            # Calculate metrics
            total_signals = len(sigs)
            win_rate = profitable_count / total_signals if total_signals > 0 else 0.0
            avg_return = sum(returns) / len(returns) if returns else 0.0
            
            # Calculate Sharpe ratio for this model's returns
            if len(returns) >= 2:
                mean_ret = sum(returns) / len(returns)
                variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
                std_ret = math.sqrt(variance)
                model_sharpe = (mean_ret / std_ret) * math.sqrt(252) if std_ret > 0 else 0.0
            else:
                model_sharpe = 0.0
            
            model_metrics[mid] = ModelMetrics(
                model_id=mid,
                total_signals=total_signals,
                profitable_signals=profitable_count,
                win_rate=win_rate,
                average_return=avg_return,
                sharpe_ratio=model_sharpe
            )
        
        return model_metrics
    
    def generate_pnl_chart(
        self,
        portfolio_history: List[PortfolioSnapshot],
        output_path: str
    ) -> None:
        """
        Generate time-series P&L visualization
        
        Args:
            portfolio_history: List of PortfolioSnapshot objects sorted by timestamp
            output_path: Path to save the chart image
        """
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        if not portfolio_history:
            # Create empty chart
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'No data available', 
                   ha='center', va='center', transform=ax.transAxes)
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close()
            return
        
        # Extract timestamps and values
        timestamps = [snapshot.timestamp for snapshot in portfolio_history]
        total_values = [float(snapshot.total_value) for snapshot in portfolio_history]
        realized_pnl = [float(snapshot.realized_pnl) for snapshot in portfolio_history]
        unrealized_pnl = [float(snapshot.unrealized_pnl) for snapshot in portfolio_history]
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Plot total portfolio value
        ax1.plot(timestamps, total_values, linewidth=2, color='blue', label='Total Value')
        ax1.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax1.set_title('Portfolio Performance Over Time', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper left')
        
        # Plot P&L breakdown
        ax2.plot(timestamps, realized_pnl, linewidth=2, color='green', label='Realized P&L')
        ax2.plot(timestamps, unrealized_pnl, linewidth=2, color='orange', label='Unrealized P&L')
        ax2.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('P&L ($)', fontsize=12)
        ax2.set_title('Profit & Loss Breakdown', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper left')
        
        # Format x-axis
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
    
    def generate_allocation_chart(
        self,
        portfolio_snapshot: PortfolioSnapshot,
        output_path: str
    ) -> None:
        """
        Generate position allocation pie chart
        
        Args:
            portfolio_snapshot: Current portfolio snapshot
            output_path: Path to save the chart image
        """
        import matplotlib.pyplot as plt
        
        if not portfolio_snapshot.positions:
            # Create empty chart with cash only
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.pie([100], labels=['Cash'], autopct='%1.1f%%', startangle=90)
            ax.set_title('Portfolio Allocation', fontsize=14, fontweight='bold')
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close()
            return
        
        # Calculate position values
        position_values = {}
        for position in portfolio_snapshot.positions:
            value = float(position.current_price) * position.quantity
            position_values[position.symbol] = value
        
        # Add cash balance
        cash = float(portfolio_snapshot.cash_balance)
        if cash > 0:
            position_values['Cash'] = cash
        
        # Prepare data for pie chart
        labels = list(position_values.keys())
        sizes = list(position_values.values())
        
        # Create color palette
        colors = plt.cm.Set3(range(len(labels)))
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 8))
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 10}
        )
        
        # Enhance text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('Portfolio Allocation', fontsize=14, fontweight='bold')
        
        # Add legend with values
        legend_labels = [f'{label}: ${value:,.2f}' for label, value in zip(labels, sizes)]
        ax.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
