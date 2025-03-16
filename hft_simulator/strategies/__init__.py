"""
Strategy factory for creating trading strategies.
"""

from typing import Dict, List, Any, Optional

from hft_simulator.engine.trading_engine import TradingEngine
from .base_strategy import BaseStrategy
from .mean_reversion import MeanReversionStrategy
from .momentum import MomentumStrategy
from .bollinger_bands import BollingerBandsStrategy

def create_strategy(strategy_name: str, 
                   trading_engine: TradingEngine, 
                   symbols: List[str],
                   **kwargs) -> Optional[BaseStrategy]:
    """
    Create a trading strategy.
    
    Args:
        strategy_name: Name of strategy to create
        trading_engine: Trading engine
        symbols: List of symbols to trade
        **kwargs: Additional strategy parameters
        
    Returns:
        Strategy instance or None if strategy not found
    """
    strategy_name = strategy_name.lower()
    
    if strategy_name == "mean_reversion":
        return MeanReversionStrategy(
            trading_engine=trading_engine,
            symbols=symbols,
            window_size=kwargs.get("window_size", 20),
            entry_threshold=kwargs.get("entry_threshold", 1.5),
            exit_threshold=kwargs.get("exit_threshold", 0.5),
            max_position=kwargs.get("max_position", 100),
            stop_loss_pct=kwargs.get("stop_loss_pct", 0.02)
        )
    elif strategy_name == "momentum":
        return MomentumStrategy(
            trading_engine=trading_engine,
            symbols=symbols,
            short_window=kwargs.get("short_window", 10),
            long_window=kwargs.get("long_window", 30),
            max_position=kwargs.get("max_position", 100),
            stop_loss_pct=kwargs.get("stop_loss_pct", 0.02),
            take_profit_pct=kwargs.get("take_profit_pct", 0.05)
        )
    elif strategy_name == "bollinger_bands":
        return BollingerBandsStrategy(
            trading_engine=trading_engine,
            symbols=symbols,
            window_size=kwargs.get("window_size", 20),
            num_std=kwargs.get("num_std", 2.0),
            max_position=kwargs.get("max_position", 100),
            stop_loss_pct=kwargs.get("stop_loss_pct", 0.02),
            take_profit_pct=kwargs.get("take_profit_pct", 0.05)
        )
    else:
        return None

def get_available_strategies() -> List[str]:
    """
    Get list of available strategies.
    
    Returns:
        List of strategy names
    """
    return ["mean_reversion", "momentum", "bollinger_bands"]
