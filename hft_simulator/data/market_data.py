"""
Market data generator for simulated market data.
"""

import random
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class MarketDataGenerator:
    """
    Generates simulated market data for testing trading strategies.
    """
    
    def __init__(self, 
                 symbols: List[str], 
                 volatility: float = 0.001,
                 initial_price: Optional[Dict[str, float]] = None,
                 tick_size: float = 0.01,
                 random_seed: Optional[int] = None):
        """
        Initialize the market data generator.
        
        Args:
            symbols: List of symbols to generate data for
            volatility: Volatility parameter for random price movements
            initial_price: Initial price for each symbol (optional)
            tick_size: Minimum price increment
            random_seed: Random seed for reproducibility
        """
        self.symbols = symbols
        self.volatility = volatility
        self.tick_size = tick_size
        
        # Set random seed if provided
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)
            
        # Initialize prices
        self.current_prices = {}
        if initial_price is None:
            initial_price = {}
            
        for symbol in symbols:
            if symbol in initial_price:
                self.current_prices[symbol] = initial_price[symbol]
            else:
                # Random initial price between 50 and 500
                self.current_prices[symbol] = round(random.uniform(50, 500), 2)
        
        # Initialize price history
        self.price_history = {symbol: [] for symbol in symbols}
        
        # Track last update time
        self.last_update = datetime.now()
        
    def generate_tick(self) -> Dict[str, Dict[str, Any]]:
        """
        Generate a market data tick with bid/ask prices and volumes.
        
        Returns:
            Dictionary with market data for each symbol
        """
        tick_data = {}
        
        # Current timestamp
        now = datetime.now()
        
        for symbol in self.symbols:
            # Get current price
            current_price = self.current_prices[symbol]
            
            # Generate random price movement based on volatility
            price_change = np.random.normal(0, self.volatility * current_price)
            
            # Round to tick size
            price_change = round(price_change / self.tick_size) * self.tick_size
            
            # Update price
            new_price = max(0.01, current_price + price_change)
            self.current_prices[symbol] = new_price
            
            # Add to price history
            self.price_history[symbol].append(new_price)
            
            # Keep history limited to 1000 data points
            if len(self.price_history[symbol]) > 1000:
                self.price_history[symbol].pop(0)
            
            # Calculate bid-ask spread (typically 0.01% to 0.05% of price)
            spread = max(self.tick_size, round(new_price * random.uniform(0.0001, 0.0005) / self.tick_size) * self.tick_size)
            
            # Calculate bid/ask
            bid_price = round((new_price - spread/2) / self.tick_size) * self.tick_size
            ask_price = round((new_price + spread/2) / self.tick_size) * self.tick_size
            
            # Ensure bid and ask are different
            if bid_price == ask_price:
                ask_price += self.tick_size
            
            # Generate random volumes
            bid_volume = int(random.lognormvariate(5, 0.5)) * 100  # Typical lot sizes
            ask_volume = int(random.lognormvariate(5, 0.5)) * 100
            
            # Create tick data
            tick_data[symbol] = {
                'timestamp': now,
                'bid': bid_price,
                'ask': ask_price,
                'bid_volume': bid_volume,
                'ask_volume': ask_volume,
                'price': new_price,
                'volume': random.randint(1000, 10000)
            }
        
        self.last_update = now
        return tick_data
        
    def get_historical_data(self, lookback_periods: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate historical data for initialization.
        
        Args:
            lookback_periods: Number of historical data points to generate
            
        Returns:
            Dictionary with historical data for each symbol
        """
        historical_data = {symbol: [] for symbol in self.symbols}
        
        # Save current state
        saved_prices = self.current_prices.copy()
        saved_history = {symbol: self.price_history[symbol].copy() for symbol in self.symbols}
        
        # Reset prices to generate historical data
        for symbol in self.symbols:
            self.current_prices[symbol] = saved_prices[symbol] * random.uniform(0.9, 1.1)
            self.price_history[symbol] = []
        
        # Generate historical data
        start_time = datetime.now() - timedelta(minutes=lookback_periods)
        
        for i in range(lookback_periods):
            time_point = start_time + timedelta(minutes=i)
            
            # Generate tick
            tick = self.generate_tick()
            
            # Set timestamp
            for symbol in tick:
                tick[symbol]['timestamp'] = time_point
                historical_data[symbol].append(tick[symbol])
        
        # Restore current state
        self.current_prices = saved_prices
        self.price_history = saved_history
        
        return historical_data 