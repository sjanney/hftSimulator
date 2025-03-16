"""
Performance monitoring utilities.
"""

import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Set up logging
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Monitors and calculates trading performance metrics.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        # Track equity curve
        self.equity_points = []
        
        # Track trades
        self.trades = []
        
        # Performance metrics
        self.metrics = {}
    
    def add_equity_point(self, timestamp: datetime, equity: float) -> None:
        """
        Add an equity point to the equity curve.
        
        Args:
            timestamp: Timestamp
            equity: Equity value
        """
        self.equity_points.append({
            'timestamp': timestamp,
            'equity': equity
        })
    
    def add_trade(self, trade: Dict[str, Any]) -> None:
        """
        Add a trade to the trade history.
        
        Args:
            trade: Trade data
        """
        self.trades.append(trade)
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculate performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        # Check if we have enough data
        if len(self.equity_points) < 2:
            self.metrics = {
                'total_return': 0.0,
                'annualized_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_trades': 0
            }
            return self.metrics
        
        # Calculate total return
        initial_equity = self.equity_points[0]['equity']
        final_equity = self.equity_points[-1]['equity']
        total_return = (final_equity - initial_equity) / initial_equity
        
        # Calculate annualized return
        start_time = self.equity_points[0]['timestamp']
        end_time = self.equity_points[-1]['timestamp']
        days = (end_time - start_time).total_seconds() / (60 * 60 * 24)
        
        if days > 0:
            annualized_return = ((1 + total_return) ** (365 / days)) - 1
        else:
            annualized_return = 0.0
        
        # Calculate Sharpe ratio
        returns = []
        for i in range(1, len(self.equity_points)):
            prev_equity = self.equity_points[i-1]['equity']
            curr_equity = self.equity_points[i]['equity']
            returns.append((curr_equity - prev_equity) / prev_equity)
        
        if len(returns) > 0:
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = mean_return / std_return * np.sqrt(252) if std_return > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        # Calculate maximum drawdown
        max_drawdown = 0.0
        peak_equity = initial_equity
        
        for point in self.equity_points:
            equity = point['equity']
            
            if equity > peak_equity:
                peak_equity = equity
            else:
                drawdown = (peak_equity - equity) / peak_equity
                max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate win rate and profit factor
        winning_trades = 0
        losing_trades = 0
        gross_profit = 0.0
        gross_loss = 0.0
        
        for trade in self.trades:
            if trade['side'] == 'buy':
                profit = trade['quantity'] * (trade['price'] - trade['commission'])
            else:
                profit = trade['quantity'] * (trade['commission'] - trade['price'])
            
            if profit > 0:
                winning_trades += 1
                gross_profit += profit
            else:
                losing_trades += 1
                gross_loss += abs(profit)
        
        total_trades = winning_trades + losing_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Store metrics
        self.metrics = {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': total_trades
        }
        
        return self.metrics
    
    def get_equity_curve(self) -> List[Dict[str, Any]]:
        """
        Get the equity curve.
        
        Returns:
            List of equity points
        """
        return self.equity_points
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """
        Get the trade history.
        
        Returns:
            List of trades
        """
        return self.trades
    
    def __str__(self) -> str:
        """
        Return string representation of performance metrics.
        
        Returns:
            String representation
        """
        if not self.metrics:
            self.calculate_metrics()
            
        return (
            f"Performance Metrics:\n"
            f"  Total Return: {self.metrics['total_return']:.2%}\n"
            f"  Annualized Return: {self.metrics['annualized_return']:.2%}\n"
            f"  Sharpe Ratio: {self.metrics['sharpe_ratio']:.2f}\n"
            f"  Maximum Drawdown: {self.metrics['max_drawdown']:.2%}\n"
            f"  Win Rate: {self.metrics['win_rate']:.2%}\n"
            f"  Profit Factor: {self.metrics['profit_factor']:.2f}\n"
            f"  Total Trades: {self.metrics['total_trades']}"
        ) 