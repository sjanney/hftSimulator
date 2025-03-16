"""
Momentum trading strategy.
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

class MomentumStrategy(BaseStrategy):
    """
    Momentum strategy that trades based on price trends.
    """
    
    def __init__(self, 
                 trading_engine: TradingEngine, 
                 symbols: List[str],
                 short_window: int = 10,
                 long_window: int = 30,
                 max_position: int = 100,
                 stop_loss_pct: float = 0.02,
                 take_profit_pct: float = 0.05):
        """
        Initialize the momentum strategy.
        
        Args:
            trading_engine: Trading engine
            symbols: List of symbols to trade
            short_window: Short window size for moving average
            long_window: Long window size for moving average
            max_position: Maximum position size
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
        """
        super().__init__(name="Momentum")
        self.trading_engine = trading_engine
        self.symbols = symbols
        self.short_window = short_window
        self.long_window = long_window
        self.max_position = max_position
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # Price history for each symbol
        self.price_history = {symbol: deque(maxlen=max(short_window, long_window)) for symbol in symbols}
        
        # Track active orders
        self.active_orders = {}
        
        # Track entry prices for stop loss and take profit
        self.entry_prices = {}
        
        # Track previous signals
        self.previous_signals = {symbol: 0 for symbol in symbols}  # 0: no signal, 1: buy, -1: sell
        
        logger.info(f"Momentum strategy initialized with short window {short_window}, "
                   f"long window {long_window}")
    
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
            if len(self.price_history[symbol]) < self.long_window:
                continue
                
            # Calculate moving averages
            prices = list(self.price_history[symbol])
            short_ma = np.mean(prices[-self.short_window:])
            long_ma = np.mean(prices[-self.long_window:])
            
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
            
            # Generate signal
            signal = 0
            
            if short_ma > long_ma:
                # Bullish signal
                signal = 1
            elif short_ma < long_ma:
                # Bearish signal
                signal = -1
            
            # Check if signal changed
            if signal != self.previous_signals[symbol]:
                # Signal changed
                if signal == 1 and current_position <= 0:
                    # Bullish signal, buy/cover
                    quantity = min(self.max_position, abs(current_position) + self.max_position)
                    
                    if quantity > 0:
                        self._place_order(symbol, OrderSide.BUY, quantity)
                        self.entry_prices[symbol] = current_price
                        
                elif signal == -1 and current_position >= 0:
                    # Bearish signal, sell/short
                    quantity = min(self.max_position, current_position + self.max_position)
                    
                    if quantity > 0:
                        self._place_order(symbol, OrderSide.SELL, quantity)
                        self.entry_prices[symbol] = current_price
                
                # Update previous signal
                self.previous_signals[symbol] = signal
    
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