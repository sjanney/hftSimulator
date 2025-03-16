# HFT Simulator

A High-Frequency Trading (HFT) simulator with various trading strategies and real-time market data connectivity across multiple market types.

## Features

- **Multiple Asset Classes**: Trade stocks, cryptocurrencies, and forex markets with realistic market behavior
- **Advanced Trading Strategies**: Mean Reversion, Momentum, Bollinger Bands, and more
- **Real-time Market Data**: Integration with Yahoo Finance API for live market data
- **Enhanced Visualization**: Beautiful color-coded terminal UI with market-specific displays
- **Performance Tracking**: Detailed metrics and portfolio analytics
- **Customizable Parameters**: Adjust market volatility, trading behavior, and more
- **Realistic Market Simulation**: Market-specific volatility and price ranges

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/hft-simulator.git
cd hft-simulator

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Make the main script executable
chmod +x run_simulator.py
```

## Quick Start

```bash
# Run with a specific strategy (simulated stock data)
./run_simulator.py --strategy mean_reversion --symbols AAPL,MSFT,GOOGL

# Run with multiple market types (stocks, crypto, forex)
./run_simulator.py --strategy bollinger_bands --expanded-markets --stocks AAPL,MSFT --crypto BTC-USD,ETH-USD --forex EUR-USD,GBP-USD

# Run with real-time market data across multiple markets
./run_simulator.py --strategy momentum --expanded-markets --real-data
```

## Market Types

The simulator supports three market types, each with realistic behavior:

### Stocks (Equities)
- Default symbols: AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA
- Medium volatility (base volatility)
- Prices typically in the $50-$500 range
- Small bid-ask spreads (0.01-0.05% of price)

### Cryptocurrencies
- Default symbols: BTC-USD, ETH-USD, SOL-USD, ADA-USD, XRP-USD
- High volatility (3x stock volatility by default)
- Wide price ranges (Bitcoin ~$30-40k, Ethereum ~$1.5-2.5k, others $10-1000)
- Wider bid-ask spreads (0.1-0.5% of price)

### Forex (Currency Pairs)
- Default symbols: EUR-USD, GBP-USD, USD-JPY, AUD-USD, USD-CAD
- Low volatility (0.5x stock volatility by default)
- Prices typically around 1.0 (except JPY pairs ~100-150)
- Very tight bid-ask spreads (measured in pips)

## Available Strategies

1. **Mean Reversion** - Trades based on price returning to historical average
2. **Momentum** - Trades based on price movement trends
3. **Bollinger Bands** - Uses price volatility and bands for trading signals
4. **VWAP (Volume-Weighted Average Price)** - Uses volume-weighted price average
5. **Order Book Imbalance** - Trades based on order book buy/sell pressure

## Command-Line Options

### Basic Options
- `--strategy` - Trading strategy to use (required)
- `--symbols` - Comma-separated list of stock symbols (for traditional mode)
- `--initial-cash` - Starting capital (default: 100000)
- `--tick-interval` - Milliseconds between market updates in simulation (default: 1000)
- `--volatility` - Volatility parameter for simulated market data (default: 0.001)
- `--random-seed` - Random seed for reproducibility

### Real-Time Data Options
- `--real-data` - Use real-time market data instead of simulation
- `--update-interval` - Seconds between real market data updates (default: 5)

### Multi-Market Options
- `--expanded-markets` - Enable multi-market functionality (stocks, crypto, forex)
- `--stocks` - Comma-separated list of stock symbols to trade
- `--crypto` - Comma-separated list of crypto symbols to trade (e.g., BTC-USD)
- `--forex` - Comma-separated list of forex pairs to trade (e.g., EUR-USD)
- `--crypto-volatility` - Multiplier for crypto volatility (default: 3.0)
- `--forex-volatility` - Multiplier for forex volatility (default: 0.5)

### Strategy Parameters
- `--strategy-params` - Comma-separated list of parameters in key=value format

## Example Commands

### Basic Usage
```bash
# Run with simulated data and the Mean Reversion strategy
./run_simulator.py --strategy mean_reversion --symbols AAPL,MSFT,GOOGL

# Run with real-time market data and the Bollinger Bands strategy
./run_simulator.py --strategy bollinger_bands --symbols AAPL,MSFT,GOOGL --real-data

# Run with custom parameters for the Momentum strategy
./run_simulator.py --strategy momentum --symbols AAPL,MSFT,GOOGL --initial-cash 500000 --tick-interval 500 --strategy-params short_window=5,long_window=20,max_position=200
```

### Multi-Market Examples
```bash
# Run with all market types (stocks, crypto, forex)
./run_simulator.py --strategy bollinger_bands --expanded-markets --stocks AAPL,MSFT,GOOGL --crypto BTC-USD,ETH-USD --forex EUR-USD,GBP-USD

# Run with custom volatility settings for different markets
./run_simulator.py --strategy mean_reversion --expanded-markets --crypto-volatility 5.0 --forex-volatility 0.3

# Run with real-time data across all market types
./run_simulator.py --strategy momentum --expanded-markets --real-data

# Comprehensive example with multiple features
./run_simulator.py --strategy bollinger_bands --expanded-markets --stocks AAPL,MSFT,GOOGL,AMZN,TSLA --crypto BTC-USD,ETH-USD,SOL-USD --forex EUR-USD,GBP-USD,USD-JPY --initial-cash 500000 --tick-interval 250 --volatility 0.002 --random-seed 42 --strategy-params window=20,num_std=2.0,position_size=100
```

## Terminal UI

The simulator features a rich terminal UI with:

- Color-coded market data (stocks in blue, crypto in orange, forex in green)
- Market-specific icons and grouping
- Price movement indicators (up/down arrows)
- Portfolio summary with equity chart
- Position tracking with profit/loss display
- Active orders panel
- Recent trades with animation effects

Press `Ctrl+C` to exit the simulation and view performance summary.

## Logs

Logs are stored in the `logs` directory with timestamped filenames (`hft_simulator_YYYYMMDD_HHMMSS.log`). The log file path is displayed at the end of the simulation summary.

## Architecture

The simulator is organized into these components:

- **Market Data Providers**: Real-time and simulated data across multiple market types
- **Trading Engine**: Order processing and position management
- **Strategy Engine**: Trading algorithm implementations
- **Performance Monitoring**: Tracking and analytics
- **Terminal UI**: Rich, color-coded visualization of market data and trading activity

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 