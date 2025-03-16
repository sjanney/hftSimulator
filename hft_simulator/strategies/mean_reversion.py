"""
Mean reversion trading strategy.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from collections import deque

from hft_simulator.engine.trading_engine import TradingEngine
from hft_simulator.engine.orders import Order, OrderSide, OrderType
from .base_strategy import BaseStrategy

# Set up logging
logger = logging.getLogger(__name__)

class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion strategy that trades when price deviates from moving average.
    """
    
    def __init__(self, 
                 trading_engine: TradingEngine, 
                 symbols: List[str],
                 window_size: int = 20,
                 entry_threshold: float = 1.5,
                 exit_threshold: float = 0.5,
                 max_position: int = 100,
                 stop_loss_pct: float = 0.02):
        """
        Initialize the mean reversion strategy.
        
        Args:
            trading_engine: Trading engine
            symbols: List of symbols to trade
            window_size: Window size for moving average
            entry_threshold: Entry threshold in standard deviations
            exit_threshold: Exit threshold in standard deviations
            max_position: Maximum position size
            stop_loss_pct: Stop loss percentage
        """
        super().__init__(name="Mean Reversion")
        self.trading_engine = trading_engine
        self.symbols = symbols
        self.window_size = window_size
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.max_position = max_position
        self.stop_loss_pct = stop_loss_pct
        
        # Price history for each symbol
        self.price_history = {symbol: deque(maxlen=window_size) for symbol in symbols}
        
        # Track active orders
        self.active_orders = {}
        
        # Track entry prices for stop loss
        self.entry_prices = {}
        
        logger.info(f"Mean reversion strategy initialized with window size {window_size}, "
                   f"entry threshold {entry_threshold}, exit threshold {exit_threshold}")
    
    def process_tick(self, tick_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Process a market data tick.
        
        Args:
            tick_data: Market data tick
        """
        # Process each symbol
        for symbol in self.symbols:
            if symbol not in tick_data:
                continue
                
            # Get market data
            market_data = tick_data[symbol]
            
            # Check if we have necessary price data
            if 'price' not in market_data:
                continue
                
            # Get current price
            current_price = market_data['price']
            
            # Update price history
            self.price_history[symbol].append(current_price)
            
            # Check if we have enough data
            if len(self.price_history[symbol]) < self.window_size:
                continue
                
            # Calculate mean and standard deviation
            prices = np.array(self.price_history[symbol])
            mean = np.mean(prices)
            std = np.std(prices)
            
            # Calculate z-score
            z_score = (current_price - mean) / std if std > 0 else 0
            
            # Get current position
            positions = self.trading_engine.get_open_positions()
            current_position = 0
            
            for position in positions:
                if position['symbol'] == symbol:
                    current_position = position['quantity']
                    break
            
            # Check for stop loss
            if symbol in self.entry_prices and current_position != 0:
                entry_price = self.entry_prices[symbol]
                
                if current_position > 0 and current_price < entry_price * (1 - self.stop_loss_pct):
                    # Stop loss for long position
                    self._place_order(symbol, OrderSide.SELL, current_position)
                    logger.info(f"Stop loss triggered for {symbol} long position at {current_price:.2f}")
                    continue
                    
                elif current_position < 0 and current_price > entry_price * (1 + self.stop_loss_pct):
                    # Stop loss for short position
                    self._place_order(symbol, OrderSide.BUY, abs(current_position))
                    logger.info(f"Stop loss triggered for {symbol} short position at {current_price:.2f}")
                    continue
            
            # Trading logic
            if z_score > self.entry_threshold and current_position >= 0:
                # Price is high, sell/short
                quantity = min(self.max_position, current_position + self.max_position)
                
                if quantity > 0:
                    self._place_order(symbol, OrderSide.SELL, quantity)
                    self.entry_prices[symbol] = current_price
                    
            elif z_score < -self.entry_threshold and current_position <= 0:
                # Price is low, buy/cover
                quantity = min(self.max_position, abs(current_position) + self.max_position)
                
                if quantity > 0:
                    self._place_order(symbol, OrderSide.BUY, quantity)
                    self.entry_prices[symbol] = current_price
                    
            elif abs(z_score) < self.exit_threshold and current_position != 0:
                # Price is near mean, exit position
                if current_position > 0:
                    self._place_order(symbol, OrderSide.SELL, current_position)
                else:
                    self._place_order(symbol, OrderSide.BUY, abs(current_position))
    
    def _place_order(self, symbol: str, side: OrderSide, quantity: float) -> Optional[str]:
        """
        Place an order.
        
        Args:
            symbol: Symbol to trade
            side: Order side
            quantity: Order quantity
            
        Returns:
            Order ID if order was placed, None otherwise
        """
        # Create order
        order = Order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=OrderType.MARKET
        )
        
        # Place order
        order_id = self.trading_engine.place_order(order)
        
        # Track order
        self.active_orders[order_id] = order
        
        logger.info(f"Placed {side.name} order for {quantity} {symbol}")
        
        return order_id
    
    def on_trade(self, trade_data: Dict[str, Any]) -> None:
        """
        Called when a trade is executed.
        
        Args:
            trade_data: Trade data
        """
        # Remove order from active orders
        if trade_data['order_id'] in self.active_orders:
            del self.active_orders[trade_data['order_id']] 