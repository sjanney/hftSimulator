"""
Expanded markets module to support multiple market types.
This module provides functionality for working with different market types
including stocks, cryptocurrencies, and forex.
"""

import random
import logging
import re
from typing import Dict, List, Any, Optional, Tuple

from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np

# Market type constants
MARKET_TYPE_STOCK = 'stock'
MARKET_TYPE_CRYPTO = 'crypto'
MARKET_TYPE_FOREX = 'forex'

# Market-specific constants
DEFAULT_STOCK_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA']
DEFAULT_CRYPTO_SYMBOLS = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'XRP-USD']
DEFAULT_FOREX_SYMBOLS = ['EUR-USD', 'GBP-USD', 'USD-JPY', 'AUD-USD', 'USD-CAD']

# Set up logging
logger = logging.getLogger(__name__)

class ExpandedMarketData:
    """
    Enhanced market data provider supporting multiple market types:
    - Stocks (equities)
    - Cryptocurrencies
    - Forex (currency pairs)
    
    Can work with both simulated and real market data.
    """
    
    def __init__(self, 
                 stocks: List[str] = None,
                 crypto: List[str] = None,
                 forex: List[str] = None,
                 volatility_multipliers: Dict[str, float] = None,
                 use_real_data: bool = False,
                 update_interval: int = 5):
        """
        Initialize the expanded market data provider.
        
        Args:
            stocks: List of stock symbols
            crypto: List of crypto symbols
            forex: List of forex pairs
            volatility_multipliers: Multipliers for simulated volatility by market type
            use_real_data: Whether to use real data from Yahoo Finance
            update_interval: Update interval for real data (seconds)
        """
        # Set default symbol lists if none provided
        self.stocks = stocks or []
        self.crypto = crypto or []
        self.forex = forex or []
        
        # Default volatility multipliers
        self.volatility_multipliers = volatility_multipliers or {
            MARKET_TYPE_STOCK: 1.0,    # Base volatility
            MARKET_TYPE_CRYPTO: 3.0,   # 3x stock volatility
            MARKET_TYPE_FOREX: 0.5,    # Half of stock volatility
        }
        
        # Track all symbols across all markets
        self.all_symbols = self.stocks + self.crypto + self.forex
        
        # Map symbols to their market type
        self.symbol_market_map = {}
        for symbol in self.stocks:
            self.symbol_market_map[symbol] = MARKET_TYPE_STOCK
        for symbol in self.crypto:
            self.symbol_market_map[symbol] = MARKET_TYPE_CRYPTO
        for symbol in self.forex:
            self.symbol_market_map[symbol] = MARKET_TYPE_FOREX
            
        # Real data settings
        self.use_real_data = use_real_data
        self.update_interval = update_interval
        
        # Track last update time
        self.last_update = datetime.now()
        
        # Market data cache
        self.market_data = {}
        
        # Initialize with current data
        if self.all_symbols:
            self._initialize_market_data()
            
        logger.info(f"Expanded market data initialized with {len(self.stocks)} stocks, "
                   f"{len(self.crypto)} cryptocurrencies, and {len(self.forex)} forex pairs")
    
    def _initialize_market_data(self):
        """Initialize market data for all symbols."""
        if self.use_real_data:
            self._fetch_real_data()
        else:
            self._initialize_simulated_data()
    
    def _initialize_simulated_data(self):
        """Initialize simulated market data."""
        for symbol in self.all_symbols:
            market_type = self.get_market_type(symbol)
            
            # Get base price range based on market type
            if market_type == MARKET_TYPE_STOCK:
                base_price = random.uniform(50, 500)  # $50-$500 for stocks
            elif market_type == MARKET_TYPE_CRYPTO:
                if symbol.startswith('BTC'):
                    base_price = random.uniform(30000, 40000)  # $30k-$40k for Bitcoin
                elif symbol.startswith('ETH'):
                    base_price = random.uniform(1500, 2500)    # $1500-$2500 for Ethereum
                else:
                    base_price = random.uniform(10, 1000)      # $10-$1000 for other crypto
            elif market_type == MARKET_TYPE_FOREX:
                # Most forex pairs are around 1.0 (e.g., EUR/USD)
                base_price = random.uniform(0.8, 1.2)
                # Exception for pairs like USD/JPY which are around 100-150
                if symbol.endswith('JPY'):
                    base_price = random.uniform(100, 150)
            
            # Create initial market data entry
            price = round(base_price, 2)
            spread = self._get_spread_for_market_type(market_type, price)
            
            self.market_data[symbol] = {
                'symbol': symbol,
                'price': price,
                'bid': round(price - spread/2, 2),
                'ask': round(price + spread/2, 2),
                'volume': random.randint(1000, 10000),
                'timestamp': datetime.now(),
                'market_type': market_type
            }
    
    def _fetch_real_data(self):
        """Fetch real market data from Yahoo Finance."""
        try:
            # Yahoo Finance requires a slightly different format
            yf_symbols = [self._format_symbol_for_yf(symbol) for symbol in self.all_symbols]
            data = yf.download(yf_symbols, period="1d", interval="1m", group_by="ticker")
            
            for symbol in self.all_symbols:
                yf_symbol = self._format_symbol_for_yf(symbol)
                if yf_symbol in data.columns.levels[0]:
                    # Get the latest data point
                    symbol_data = data[yf_symbol].iloc[-1]
                    
                    market_type = self.get_market_type(symbol)
                    price = symbol_data.get('Close', 0)
                    
                    # Create spread based on market type
                    spread = self._get_spread_for_market_type(market_type, price)
                    
                    self.market_data[symbol] = {
                        'symbol': symbol,
                        'price': price,
                        'bid': round(price - spread/2, 4),
                        'ask': round(price + spread/2, 4),
                        'volume': int(symbol_data.get('Volume', 0)),
                        'timestamp': datetime.now(),
                        'market_type': market_type
                    }
                else:
                    logger.warning(f"Could not get data for {symbol}, using simulated data")
                    # Fall back to simulated data for this symbol
                    self._initialize_simulated_data_for_symbol(symbol)
                    
        except Exception as e:
            logger.error(f"Error fetching real market data: {e}")
            # Fall back to simulated data
            self._initialize_simulated_data()
    
    def _initialize_simulated_data_for_symbol(self, symbol):
        """Initialize simulated market data for a single symbol."""
        market_type = self.get_market_type(symbol)
        
        # Similar logic as in _initialize_simulated_data
        if market_type == MARKET_TYPE_STOCK:
            base_price = random.uniform(50, 500)
        elif market_type == MARKET_TYPE_CRYPTO:
            if symbol.startswith('BTC'):
                base_price = random.uniform(30000, 40000)
            elif symbol.startswith('ETH'):
                base_price = random.uniform(1500, 2500)
            else:
                base_price = random.uniform(10, 1000)
        elif market_type == MARKET_TYPE_FOREX:
            base_price = random.uniform(0.8, 1.2)
            if symbol.endswith('JPY'):
                base_price = random.uniform(100, 150)
        
        price = round(base_price, 2)
        spread = self._get_spread_for_market_type(market_type, price)
        
        self.market_data[symbol] = {
            'symbol': symbol,
            'price': price,
            'bid': round(price - spread/2, 2),
            'ask': round(price + spread/2, 2),
            'volume': random.randint(1000, 10000),
            'timestamp': datetime.now(),
            'market_type': market_type
        }
    
    def _get_spread_for_market_type(self, market_type, price):
        """Get appropriate spread based on market type and price."""
        if market_type == MARKET_TYPE_STOCK:
            # Stock spread is usually small, around 0.01-0.05% of price
            return max(0.01, price * 0.0002)
        elif market_type == MARKET_TYPE_CRYPTO:
            # Crypto spreads are wider, around 0.1-0.5% of price
            return max(0.01, price * 0.002)
        elif market_type == MARKET_TYPE_FOREX:
            # Forex spreads are very small, typically measured in pips
            # 1 pip is 0.0001 for most pairs
            if price > 50:  # JPY pairs
                return 0.02  # 2 pips for JPY pairs
            else:
                return 0.0002  # 2 pips for other forex pairs
    
    def _format_symbol_for_yf(self, symbol):
        """Format symbol for Yahoo Finance API."""
        # Replace dash with forward slash for forex and some crypto
        if self.get_market_type(symbol) in [MARKET_TYPE_FOREX, MARKET_TYPE_CRYPTO]:
            return symbol.replace('-', '/')
        return symbol
    
    def get_market_type(self, symbol):
        """Get market type for a symbol."""
        return self.symbol_market_map.get(symbol, MARKET_TYPE_STOCK)
    
    def generate_tick(self):
        """Generate a market data tick for all symbols."""
        result = {}
        
        # Check if we need to update real data
        if self.use_real_data:
            time_since_update = (datetime.now() - self.last_update).total_seconds()
            if time_since_update >= self.update_interval:
                self._fetch_real_data()
                self.last_update = datetime.now()
        
        # Update simulated data or use cached real data
        for symbol in self.all_symbols:
            if symbol not in self.market_data:
                self._initialize_simulated_data_for_symbol(symbol)
                
            current_data = self.market_data[symbol].copy()
            
            if not self.use_real_data:
                # Update simulated data
                market_type = self.get_market_type(symbol)
                volatility = 0.001 * self.volatility_multipliers[market_type]
                
                # Generate random price movement
                price_change = current_data['price'] * random.normalvariate(0, volatility)
                new_price = max(0.01, current_data['price'] + price_change)
                
                # Round to appropriate precision
                if market_type == MARKET_TYPE_STOCK:
                    new_price = round(new_price, 2)  # 2 decimal places for stocks
                elif market_type == MARKET_TYPE_CRYPTO:
                    if new_price > 1000:
                        new_price = round(new_price, 2)  # 2 decimal places for high-value crypto
                    elif new_price > 10:
                        new_price = round(new_price, 3)  # 3 decimal places for mid-value crypto
                    else:
                        new_price = round(new_price, 4)  # 4 decimal places for low-value crypto
                elif market_type == MARKET_TYPE_FOREX:
                    if new_price > 50:  # JPY pairs
                        new_price = round(new_price, 3)  # 3 decimal places for JPY
                    else:
                        new_price = round(new_price, 4)  # 4 decimal places for other forex
                
                # Update spread based on new price
                spread = self._get_spread_for_market_type(market_type, new_price)
                
                # Update volume (random walk with mean reversion)
                volume_change = random.randint(-500, 500)
                new_volume = max(1000, min(100000, current_data['volume'] + volume_change))
                
                # Update market data
                current_data.update({
                    'price': new_price,
                    'bid': round(new_price - spread/2, 4),
                    'ask': round(new_price + spread/2, 4),
                    'volume': new_volume,
                    'timestamp': datetime.now()
                })
                
                # Save updated data
                self.market_data[symbol] = current_data
            
            # Add to result
            result[symbol] = current_data
            
        return result
    
    def get_historical_data(self, lookback_periods=100):
        """
        Generate or fetch historical data for all symbols.
        
        Args:
            lookback_periods: Number of periods to look back
            
        Returns:
            Dictionary with historical data for each symbol
        """
        result = {}
        
        if self.use_real_data:
            # Fetch real historical data from Yahoo Finance
            try:
                # Calculate date range
                end_date = datetime.now()
                # For daily data, we need to go back much further to get enough bars
                start_date = end_date - pd.Timedelta(days=lookback_periods)
                
                yf_symbols = [self._format_symbol_for_yf(symbol) for symbol in self.all_symbols]
                data = yf.download(yf_symbols, start=start_date, end=end_date, interval="1d", group_by="ticker")
                
                for symbol in self.all_symbols:
                    yf_symbol = self._format_symbol_for_yf(symbol)
                    market_type = self.get_market_type(symbol)
                    
                    if yf_symbol in data.columns.levels[0]:
                        symbol_data = data[yf_symbol]
                        # Convert DataFrame to list of dictionaries
                        history = []
                        for i, row in symbol_data.iterrows():
                            price = row.get('Close', 0)
                            spread = self._get_spread_for_market_type(market_type, price)
                            
                            history.append({
                                'symbol': symbol,
                                'price': price,
                                'bid': price - spread/2,
                                'ask': price + spread/2,
                                'volume': int(row.get('Volume', 0)),
                                'timestamp': i.to_pydatetime(),
                                'market_type': market_type
                            })
                        
                        result[symbol] = history
                    else:
                        # Fall back to simulated history
                        logger.warning(f"Could not get historical data for {symbol}, using simulated data")
                        result[symbol] = self._generate_simulated_history(symbol, lookback_periods)
            except Exception as e:
                logger.error(f"Error fetching historical data: {e}")
                # Fall back to simulated history for all symbols
                for symbol in self.all_symbols:
                    result[symbol] = self._generate_simulated_history(symbol, lookback_periods)
        else:
            # Generate simulated historical data for all symbols
            for symbol in self.all_symbols:
                result[symbol] = self._generate_simulated_history(symbol, lookback_periods)
        
        return result
    
    def _generate_simulated_history(self, symbol, lookback_periods):
        """Generate simulated historical data for a symbol."""
        market_type = self.get_market_type(symbol)
        history = []
        
        # Get initial price from current data or generate a new one
        if symbol in self.market_data:
            current_price = self.market_data[symbol]['price']
        else:
            if market_type == MARKET_TYPE_STOCK:
                current_price = random.uniform(50, 500)
            elif market_type == MARKET_TYPE_CRYPTO:
                if symbol.startswith('BTC'):
                    current_price = random.uniform(30000, 40000)
                elif symbol.startswith('ETH'):
                    current_price = random.uniform(1500, 2500)
                else:
                    current_price = random.uniform(10, 1000)
            elif market_type == MARKET_TYPE_FOREX:
                current_price = random.uniform(0.8, 1.2)
                if symbol.endswith('JPY'):
                    current_price = random.uniform(100, 150)
        
        # Generate random walk backwards in time
        prices = [current_price]
        volatility = 0.01 * self.volatility_multipliers[market_type]  # Daily volatility is higher
        
        for i in range(lookback_periods - 1):
            # Generate random price change (drift toward a mean)
            mean_reversion = 0.05 * (random.uniform(0.8, 1.2) * current_price - prices[-1])
            random_change = prices[-1] * random.normalvariate(0, volatility)
            new_price = max(0.01, prices[-1] + mean_reversion + random_change)
            prices.append(new_price)
        
        # Reverse to get chronological order
        prices.reverse()
        
        # Current timestamp
        now = datetime.now()
        
        # Generate history data
        for i in range(lookback_periods):
            price = prices[i]
            # Adjust precision based on market type
            if market_type == MARKET_TYPE_STOCK:
                price = round(price, 2)
            elif market_type == MARKET_TYPE_CRYPTO:
                if price > 1000:
                    price = round(price, 2)
                elif price > 10:
                    price = round(price, 3)
                else:
                    price = round(price, 4)
            elif market_type == MARKET_TYPE_FOREX:
                if price > 50:
                    price = round(price, 3)
                else:
                    price = round(price, 4)
                    
            # Calculate spread based on market type
            spread = self._get_spread_for_market_type(market_type, price)
            
            # Calculate timestamp (each step is 1 day ago)
            timestamp = now - pd.Timedelta(days=lookback_periods-i-1)
            
            history.append({
                'symbol': symbol,
                'price': price,
                'bid': round(price - spread/2, 4),
                'ask': round(price + spread/2, 4),
                'volume': random.randint(10000, 1000000),  # Higher volume for daily data
                'timestamp': timestamp,
                'market_type': market_type
            })
        
        return history 