# HFT Simulator

A High-Frequency Trading (HFT) simulator with various trading strategies and real-time market data connectivity.

## Features

- Multiple trading strategies (Mean Reversion, Momentum, Bollinger Bands, VWAP, and more)
- Real-time market data integration with Yahoo Finance
- Simulated and real market trading modes
- Performance tracking and visualization
- Customizable trading parameters
- Paper trading functionality

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
```

## Usage

```bash
# Run with a specific strategy (simulated data)
python -m hft_simulator --strategy mean_reversion --symbols AAPL,MSFT,GOOGL

# Run with real-time market data
python -m hft_simulator --strategy bollinger_bands --symbols AAPL,MSFT,GOOGL --real-data

# Run with custom parameters
python -m hft_simulator --strategy momentum --symbols AAPL,MSFT,GOOGL --initial-cash 100000 --tick-interval 500
```

## Available Strategies

1. **Mean Reversion** - Trades based on price returning to historical average
2. **Momentum** - Trades based on price movement trends
3. **Bollinger Bands** - Uses price volatility and bands for trading signals
4. **VWAP (Volume-Weighted Average Price)** - Uses volume-weighted price average
5. **Order Book Imbalance** - Trades based on order book buy/sell pressure

## Command-Line Options

- `--strategy` - Trading strategy to use
- `--symbols` - Comma-separated list of stock symbols
- `--initial-cash` - Starting capital (default: 100000)
- `--tick-interval` - Milliseconds between market updates in simulation (default: 1000)
- `--real-data` - Use real-time market data instead of simulation
- `--update-interval` - Seconds between real market data updates (default: 5)

## Architecture

The simulator is organized into the following components:

- Market Data Providers (real-time and simulated)
- Trading Engine (order processing and position management)
- Strategy Engine (trading algorithm implementations)
- Performance Monitoring (tracking and analytics)
- User Interface (data visualization and control)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 