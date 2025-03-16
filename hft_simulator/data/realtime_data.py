"""
Real-time market data provider using Yahoo Finance API.
"""

import logging
import time
import threading
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import yfinance as yf
import pandas as pd
import numpy as np

from .market_data import MarketDataGenerator

# Set up logging
logger = logging.getLogger(__name__)

class RealTimeMarketData:
    """
    Provides real-time market data from Yahoo Finance API.
    Falls back to simulation if API fails or hit rate limits.
    """
    
    def __init__(self, 
                 symbols: List[str],
                 update_interval: int = 5,
                 cache_duration: int = 60,
                 fallback_volatility: float = 0.001):
        """
        Initialize the real-time market data provider.
        
        Args:
            symbols: List of symbols to get data for
            update_interval: Update interval in seconds
            cache_duration: Cache duration in seconds
            fallback_volatility: Volatility for fallback simulator
        """
        self.symbols = symbols
        self.update_interval = update_interval
        self.cache_duration = cache_duration
        
        # Dictionary to store the latest market data
        self.latest_data = {}
        
        # Dictionary to store data cache with timestamps
        self.data_cache = {}
        
        # Store the last update time
        self.last_update = datetime.now() - timedelta(seconds=update_interval*2)
        
        # Flag to track if we're in simulation fallback mode
        self.is_simulation_mode = False
        
        # Initialize fallback simulator with high volatility
        self.fallback_simulator = MarketDataGenerator(
            symbols=symbols,
            volatility=fallback_volatility,
            random_seed=42
        )
        
        # Track consecutive errors
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
        
        # Cache initial data
        self._update_market_data()
        
        # Log initialization
        logger.info(f"RealTimeMarketData initialized with symbols: {symbols}, update interval: {update_interval}s")
    
    def _fetch_yahoo_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch real-time data from Yahoo Finance for a symbol.
        
        Args:
            symbol: Symbol to fetch data for
            
        Returns:
            Market data dictionary or None if fetch failed
        """
        try:
            # Get ticker data
            ticker = yf.Ticker(symbol)
            
            # Get the latest data
            hist = ticker.history(period="1d", interval="1m", prepost=True)
            
            if hist.empty:
                logger.warning(f"No data returned from Yahoo Finance for {symbol}")
                return None
            
            # Get latest row
            latest = hist.iloc[-1]
            
            # Get bid/ask from info
            info = ticker.info
            bid = info.get('bid', latest['Close'] * 0.9999)
            ask = info.get('ask', latest['Close'] * 1.0001)
            
            # Ensure bid < ask
            if bid >= ask:
                bid = latest['Close'] * 0.9999
                ask = latest['Close'] * 1.0001
            
            # Create market data dictionary
            market_data = {
                'timestamp': datetime.now(),
                'bid': float(bid),
                'ask': float(ask),
                'bid_volume': int(info.get('bidSize', 100) * 100),
                'ask_volume': int(info.get('askSize', 100) * 100),
                'price': float(latest['Close']),
                'volume': int(latest['Volume']) if 'Volume' in latest else 0
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def _update_market_data(self) -> bool:
        """
        Update market data for all symbols.
        
        Returns:
            True if update successful, False otherwise
        """
        timestamp = datetime.now()
        success = True
        updated_symbols = 0
        
        # Check if enough time has passed since last update
        time_since_update = (timestamp - self.last_update).total_seconds()
        if time_since_update < self.update_interval:
            logger.debug(f"Skipping update, only {time_since_update:.1f}s since last update")
            return True
            
        logger.info(f"Updating market data for {len(self.symbols)} symbols")
        
        # Update for each symbol
        for symbol in self.symbols:
            try:
                market_data = self._fetch_yahoo_data(symbol)
                
                if market_data:
                    # Update cache
                    self.data_cache[symbol] = {
                        'data': market_data,
                        'timestamp': timestamp
                    }
                    updated_symbols += 1
                else:
                    success = False
                    
            except Exception as e:
                logger.error(f"Error updating data for {symbol}: {str(e)}")
                success = False
        
        # Check if update was successful
        if updated_symbols > 0:
            logger.info(f"Successfully updated market data for {updated_symbols}/{len(self.symbols)} symbols")
            self.last_update = timestamp
            self.consecutive_errors = 0
            self.is_simulation_mode = False
            return True
        else:
            self.consecutive_errors += 1
            
            if self.consecutive_errors >= self.max_consecutive_errors:
                if not self.is_simulation_mode:
                    logger.warning(f"Switching to simulation mode after {self.consecutive_errors} consecutive errors")
                    self.is_simulation_mode = True
                
            return False
    
    def generate_tick(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the latest market data for all symbols.
        
        Returns:
            Dictionary of market data for each symbol
        """
        # Check if we need to update
        current_time = datetime.now()
        time_since_update = (current_time - self.last_update).total_seconds()
        
        # Force update if enough time has passed
        if time_since_update >= self.update_interval:
            update_success = self._update_market_data()
            
            # If update failed and we have enough consecutive errors, switch to simulation
            if not update_success and self.consecutive_errors >= self.max_consecutive_errors:
                logger.warning("Using simulation fallback for market data")
                return self.fallback_simulator.generate_tick()
        
        # Check if we're in simulation mode
        if self.is_simulation_mode:
            return self.fallback_simulator.generate_tick()
        
        # Prepare result dictionary
        result = {}
        
        for symbol in self.symbols:
            # Check if we have cached data for this symbol
            if symbol in self.data_cache:
                cached = self.data_cache[symbol]
                cache_age = (current_time - cached['timestamp']).total_seconds()
                
                # Use cached data if it's fresh
                if cache_age < self.cache_duration:
                    result[symbol] = cached['data'].copy()
                else:
                    # Data is stale, use fallback simulation for this symbol
                    logger.warning(f"Cached data for {symbol} is stale ({cache_age:.1f}s old)")
                    tick = self.fallback_simulator.generate_tick()
                    if symbol in tick:
                        result[symbol] = tick[symbol]
            else:
                # No cached data, use fallback simulation for this symbol
                logger.warning(f"No cached data for {symbol}")
                tick = self.fallback_simulator.generate_tick()
                if symbol in tick:
                    result[symbol] = tick[symbol]
        
        return result
    
    def get_historical_data(self, lookback_periods: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get historical data for initialization.
        
        Args:
            lookback_periods: Number of historical data points
            
        Returns:
            Dictionary of historical data for each symbol
        """
        historical_data = {symbol: [] for symbol in self.symbols}
        
        # Try to get real historical data
        for symbol in self.symbols:
            try:
                # Calculate start date (number of days based on lookback)
                days_to_fetch = max(1, lookback_periods // 390)  # ~390 minutes in a trading day
                
                # Fetch data from Yahoo Finance
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{days_to_fetch}d", interval="1m")
                
                if not hist.empty:
                    # Convert to the format we need
                    for i in range(min(lookback_periods, len(hist))):
                        idx = -(i+1)
                        row = hist.iloc[idx]
                        
                        # Create market data entry
                        entry = {
                            'timestamp': hist.index[idx].to_pydatetime(),
                            'bid': float(row['Close'] * 0.9999),
                            'ask': float(row['Close'] * 1.0001),
                            'bid_volume': 100,
                            'ask_volume': 100,
                            'price': float(row['Close']),
                            'volume': int(row['Volume'])
                        }
                        
                        historical_data[symbol].append(entry)
                    
                    logger.info(f"Retrieved {len(historical_data[symbol])} historical data points for {symbol}")
                else:
                    logger.warning(f"No historical data found for {symbol}, using simulation")
                    
            except Exception as e:
                logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
        
        # For any symbol without data, use simulation
        for symbol in self.symbols:
            if not historical_data[symbol]:
                logger.warning(f"Using simulated historical data for {symbol}")
                
                # Generate simulated historical data
                sim_data = self.fallback_simulator.get_historical_data(lookback_periods)
                
                if symbol in sim_data:
                    historical_data[symbol] = sim_data[symbol]
        
        return historical_data 