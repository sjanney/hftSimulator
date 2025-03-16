"""
Bollinger Bands trading strategy.
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

class BollingerBandsStrategy(BaseStrategy):
    """
    Bollinger Bands strategy that trades based on price volatility.
    """
    
    def __init__(self, 
                 trading_engine: TradingEngine, 
                 symbols: List[str],
                 window_size: int = 20,
                 num_std: float = 2.0,
                 max_position: int = 100,
                 stop_loss_pct: float = 0.02,
                 take_profit_pct: float = 0.05):
        """
        Initialize the Bollinger Bands strategy.
        
        Args:
            trading_engine: Trading engine
            symbols: List of symbols to trade
            window_size: Window size for moving average
            num_std: Number of standard deviations for bands
            max_position: Maximum position size
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
        """
        super().__init__(name="Bollinger Bands")
        self.trading_engine = trading_engine
        self.symbols = symbols
        self.window_size = window_size
        self.num_std = num_std
        self.max_position = max_position
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # Price history for each symbol
        self.price_history = {symbol: deque(maxlen=window_size) for symbol in symbols}
        
        # Track active orders
        self.active_orders = {}
        
        # Track entry prices for stop loss and take profit
        self.entry_prices = {}
        
        logger.info(f"Bollinger Bands strategy initialized with window size {window_size}, "
                   f"num_std {num_std}")
    
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
                
            # Calculate Bollinger Bands
            prices = np.array(self.price_history[symbol])
            mean = np.mean(prices)
            std = np.std(prices)
            
            upper_band = mean + (self.num_std * std)
            lower_band = mean - (self.num_std * std)
            
            # Calculate %B (position within bands)
            percent_b = (current_price - lower_band) / (upper_band - lower_band) if upper_band != lower_band else 0.5
            
            # Get current position
            positions = self.trading_engine.get_open_positions()
            current_position = 0
            
            for position in positions:
                if position['symbol'] == symbol:
                    current_position = position['quantity']
                    break
            
            # Check for stop loss and take profit
            if symbol in self.entry_prices and current_position != 0:
                entry_price = self.entry_prices[symbol]
                
                if current_position > 0:
                    # Long position
                    if current_price < entry_price * (1 - self.stop_loss_pct):
                        # Stop loss
                        self._place_order(symbol, OrderSide.SELL, current_position)
                        logger.info(f"Stop loss triggered for {symbol} long position at {current_price:.2f}")
                        continue
                        
                    if current_price > entry_price * (1 + self.take_profit_pct):
                        # Take profit
                        self._place_order(symbol, OrderSide.SELL, current_position)
                        logger.info(f"Take profit triggered for {symbol} long position at {current_price:.2f}")
                        continue
                        
                elif current_position < 0:
                    # Short position
                    if current_price > entry_price * (1 + self.stop_loss_pct):
                        # Stop loss
                        self._place_order(symbol, OrderSide.BUY, abs(current_position))
                        logger.info(f"Stop loss triggered for {symbol} short position at {current_price:.2f}")
                        continue
                        
                    if current_price < entry_price * (1 - self.take_profit_pct):
                        # Take profit
                        self._place_order(symbol, OrderSide.BUY, abs(current_position))
                        logger.info(f"Take profit triggered for {symbol} short position at {current_price:.2f}")
                        continue
            
            # Trading logic
            if percent_b <= 0.05 and current_position <= 0:
                # Price is at or below lower band, buy/cover
                quantity = min(self.max_position, abs(current_position) + self.max_position)
                
                if quantity > 0:
                    self._place_order(symbol, OrderSide.BUY, quantity)
                    self.entry_prices[symbol] = current_price
                    logger.info(f"Buy signal for {symbol} at {current_price:.2f} (percent_b: {percent_b:.2f})")
                    
            elif percent_b >= 0.95 and current_position >= 0:
                # Price is at or above upper band, sell/short
                quantity = min(self.max_position, current_position + self.max_position)
                
                if quantity > 0:
                    self._place_order(symbol, OrderSide.SELL, quantity)
                    self.entry_prices[symbol] = current_price
                    logger.info(f"Sell signal for {symbol} at {current_price:.2f} (percent_b: {percent_b:.2f})")
                    
            elif 0.4 <= percent_b <= 0.6 and current_position != 0:
                # Price is near the middle band, exit position
                if current_position > 0:
                    self._place_order(symbol, OrderSide.SELL, current_position)
                    logger.info(f"Exit long signal for {symbol} at {current_price:.2f} (percent_b: {percent_b:.2f})")
                else:
                    self._place_order(symbol, OrderSide.BUY, abs(current_position))
                    logger.info(f"Exit short signal for {symbol} at {current_price:.2f} (percent_b: {percent_b:.2f})")
    
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