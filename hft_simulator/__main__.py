"""
Main entry point for the HFT Simulator.
"""

import argparse
import logging
import sys
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from hft_simulator.data.market_data import MarketDataGenerator
from hft_simulator.data.realtime_data import RealTimeMarketData
from hft_simulator.data.expanded_markets import (
    ExpandedMarketData,
    DEFAULT_STOCK_SYMBOLS,
    DEFAULT_CRYPTO_SYMBOLS,
    DEFAULT_FOREX_SYMBOLS,
    MARKET_TYPE_STOCK,
    MARKET_TYPE_CRYPTO,
    MARKET_TYPE_FOREX
)
from hft_simulator.engine.trading_engine import TradingEngine
from hft_simulator.strategies import create_strategy, get_available_strategies
from hft_simulator.ui.terminal_ui import TerminalUI
from hft_simulator.utils.performance import PerformanceMonitor

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Generate log filename with timestamp
log_filename = os.path.join(logs_dir, f'hft_simulator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# Configure logging to file instead of terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        # Uncomment if you want critical errors to still appear in terminal
        # logging.StreamHandler(sys.stderr)
    ]
)

# Log the session start
logger = logging.getLogger(__name__)
logger.info(f"Starting new HFT Simulator session. Logs will be written to {log_filename}")

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="HFT Simulator")
    
    # Strategy
    parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        choices=get_available_strategies(),
        help="Trading strategy to use"
    )
    
    # Symbols
    parser.add_argument(
        "--symbols",
        type=str,
        required=False,
        default="",
        help="Comma-separated list of symbols to trade (traditional mode)"
    )
    
    # Initial cash
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=100000.0,
        help="Initial cash amount"
    )
    
    # Tick interval
    parser.add_argument(
        "--tick-interval",
        type=int,
        default=1000,
        help="Tick interval in milliseconds (for simulation)"
    )
    
    # Volatility
    parser.add_argument(
        "--volatility",
        type=float,
        default=0.001,
        help="Volatility parameter for simulated market data"
    )
    
    # Random seed
    parser.add_argument(
        "--random-seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    
    # Real-time data
    parser.add_argument(
        "--real-data",
        action="store_true",
        help="Use real-time market data instead of simulation"
    )
    
    # Update interval for real-time data
    parser.add_argument(
        "--update-interval",
        type=int,
        default=5,
        help="Update interval in seconds for real-time market data"
    )
    
    # Strategy parameters
    parser.add_argument(
        "--strategy-params",
        type=str,
        default="",
        help="Comma-separated list of strategy parameters in key=value format"
    )
    
    # EXPANDED MARKETS SUPPORT
    parser.add_argument(
        "--expanded-markets", 
        action="store_true",
        help="Use expanded markets functionality (stocks, crypto, forex)"
    )
    
    # Stock symbols
    parser.add_argument(
        "--stocks",
        type=str,
        default=",".join(DEFAULT_STOCK_SYMBOLS[:3]),
        help="Comma-separated list of stock symbols to trade"
    )
    
    # Crypto symbols
    parser.add_argument(
        "--crypto",
        type=str,
        default=",".join(DEFAULT_CRYPTO_SYMBOLS[:2]),
        help="Comma-separated list of crypto symbols to trade (use format like 'BTC-USD')"
    )
    
    # Forex symbols
    parser.add_argument(
        "--forex",
        type=str,
        default=",".join(DEFAULT_FOREX_SYMBOLS[:2]),
        help="Comma-separated list of forex pairs to trade (use format like 'EUR-USD')"
    )
    
    # Market volatility multipliers
    parser.add_argument(
        "--crypto-volatility",
        type=float,
        default=3.0,
        help="Multiplier for crypto volatility relative to stock volatility"
    )
    
    parser.add_argument(
        "--forex-volatility",
        type=float,
        default=0.5,
        help="Multiplier for forex volatility relative to stock volatility"
    )
    
    return parser.parse_args()

def parse_strategy_params(params_str: str) -> Dict[str, Any]:
    """
    Parse strategy parameters from string.
    
    Args:
        params_str: Strategy parameters string
        
    Returns:
        Dictionary of strategy parameters
    """
    if not params_str:
        return {}
        
    params = {}
    
    for param in params_str.split(","):
        if "=" in param:
            key, value = param.split("=", 1)
            
            # Try to convert to appropriate type
            try:
                # Try as int
                params[key] = int(value)
            except ValueError:
                try:
                    # Try as float
                    params[key] = float(value)
                except ValueError:
                    # Keep as string
                    params[key] = value
    
    return params

def main():
    """Main entry point."""
    # Parse command-line arguments
    args = parse_args()
    
    # Parse symbols based on mode (traditional or expanded markets)
    if args.expanded_markets:
        # Parse symbols for each market type
        stock_symbols = [s.strip() for s in args.stocks.split(",") if s.strip()]
        crypto_symbols = [s.strip() for s in args.crypto.split(",") if s.strip()]
        forex_symbols = [s.strip() for s in args.forex.split(",") if s.strip()]
        all_symbols = stock_symbols + crypto_symbols + forex_symbols
        
        if not all_symbols:
            logger.error("No symbols provided for expanded markets")
            print("Error: No symbols provided for expanded markets")
            return
            
        symbols = all_symbols
        
        logger.info(f"Using expanded markets with {len(stock_symbols)} stocks, "
                   f"{len(crypto_symbols)} cryptocurrencies, and {len(forex_symbols)} forex pairs")
    else:
        # Traditional mode with a simple list of symbols
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
        stock_symbols = symbols
        crypto_symbols = []
        forex_symbols = []
        
        if not symbols:
            logger.error("No symbols provided")
            print("Error: No symbols provided. Use --symbols to specify symbols to trade.")
            return
    
    # Parse strategy parameters
    strategy_params = parse_strategy_params(args.strategy_params)
    
    logger.info(f"Starting HFT Simulator with strategy: {args.strategy}")
    logger.info(f"Trading symbols: {symbols}")
    
    # Clear terminal before starting
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Print welcome message
    print("\n" + "=" * 80)
    print(" " * 30 + "HFT SIMULATOR" + " " * 30)
    print("=" * 80)
    print(f"\nStrategy: {args.strategy}")
    
    if args.expanded_markets:
        print("\nMarkets:")
        if stock_symbols:
            print(f"  - Stocks: {', '.join(stock_symbols)}")
        if crypto_symbols:
            print(f"  - Crypto: {', '.join(crypto_symbols)}")
        if forex_symbols:
            print(f"  - Forex:  {', '.join(forex_symbols)}")
    else:
        print(f"Symbols: {', '.join(symbols)}")
        
    print(f"Using {'real-time' if args.real_data else 'simulated'} market data")
    print("\nInitializing simulator...")
    print("=" * 80 + "\n")
    
    # Initialize market data generator
    if args.expanded_markets:
        # Set up volatility multipliers
        volatility_multipliers = {
            MARKET_TYPE_STOCK: 1.0,
            MARKET_TYPE_CRYPTO: args.crypto_volatility,
            MARKET_TYPE_FOREX: args.forex_volatility
        }
        
        logger.info(f"Using expanded markets with volatility multipliers: {volatility_multipliers}")
        
        market_data = ExpandedMarketData(
            stocks=stock_symbols,
            crypto=crypto_symbols,
            forex=forex_symbols,
            volatility_multipliers=volatility_multipliers,
            use_real_data=args.real_data,
            update_interval=args.update_interval
        )
    elif args.real_data:
        logger.info("Using real-time market data")
        market_data = RealTimeMarketData(
            symbols=symbols,
            update_interval=args.update_interval
        )
    else:
        logger.info("Using simulated market data")
        market_data = MarketDataGenerator(
            symbols=symbols,
            volatility=args.volatility,
            random_seed=args.random_seed
        )
    
    # Get historical data for initialization
    historical_data = market_data.get_historical_data(lookback_periods=100)
    
    # Initialize trading engine
    trading_engine = TradingEngine(
        initial_cash=args.initial_cash,
        commission=0.001,  # 0.1% commission
        slippage=0.0005    # 0.05% slippage
    )
    
    # Create strategy
    strategy = create_strategy(
        strategy_name=args.strategy,
        trading_engine=trading_engine,
        symbols=symbols,
        **strategy_params
    )
    
    if not strategy:
        logger.error(f"Failed to create strategy: {args.strategy}")
        print(f"Error: Failed to create strategy: {args.strategy}")
        return
    
    # Initialize UI
    ui = TerminalUI(
        trading_engine=trading_engine,
        strategy=strategy,
        symbols=symbols,
        refresh_rate=0.5  # 2 updates per second
    )
    
    # Initialize performance monitor
    performance_monitor = PerformanceMonitor()
    
    # Start UI in background thread
    ui_thread = ui.run_in_thread()
    
    # Main simulation loop
    logger.info("Starting simulation...")
    
    try:
        tick_interval_sec = args.tick_interval / 1000.0
        
        while True:
            # Generate market data tick
            tick_data = market_data.generate_tick()
            
            # Update UI with latest market data
            ui.update_market_data(tick_data)
            
            # Process market data with strategy
            strategy.process_tick(tick_data)
            
            # Process market data with trading engine
            trades = trading_engine.process_market_data(tick_data)
            
            # Notify strategy of trades
            for trade in trades:
                strategy.on_trade(trade.to_dict())
                
                # Add trade to performance monitor
                performance_monitor.add_trade(trade.to_dict())
            
            # Update performance monitor
            if tick_data and list(tick_data.keys()):
                first_symbol = list(tick_data.keys())[0]
                performance_monitor.add_equity_point(
                    timestamp=tick_data.get(first_symbol, {}).get('timestamp', datetime.now()),
                    equity=trading_engine.equity
                )
            
            # Sleep until next tick
            time.sleep(tick_interval_sec)
            
    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")
    finally:
        # Stop UI
        ui.stop()
        ui_thread.join(timeout=1.0)
        
        # Clear terminal
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Print performance metrics
        print("\n" + "=" * 80)
        print(" " * 25 + "SIMULATION SUMMARY" + " " * 25)
        print("=" * 80 + "\n")
        metrics = performance_monitor.calculate_metrics()
        print(performance_monitor)
        print(f"\nLog file: {log_filename}")
        print("\n" + "=" * 80)

if __name__ == "__main__":
    main() 