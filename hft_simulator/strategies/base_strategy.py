"""
Base strategy interface for all trading strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    """
    
    def __init__(self, name: str):
        """
        Initialize the strategy.
        
        Args:
            name: Strategy name
        """
        self.name = name
    
    @abstractmethod
    def process_tick(self, tick_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Process a market data tick.
        
        Args:
            tick_data: Market data tick
        """
        pass
    
    def on_trade(self, trade_data: Dict[str, Any]) -> None:
        """
        Called when a trade is executed.
        
        Args:
            trade_data: Trade data
        """
        pass
    
    def on_start(self) -> None:
        """Called when the strategy is started."""
        pass
    
    def on_stop(self) -> None:
        """Called when the strategy is stopped."""
        pass 