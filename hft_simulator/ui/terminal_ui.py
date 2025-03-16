"""
Terminal UI for HFT simulator with enhanced visuals.
"""

import logging
import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
from rich.box import Box, ROUNDED, DOUBLE, HEAVY, DOUBLE_EDGE
from rich.style import Style
from rich.align import Align
from rich import box
from rich.console import Group
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from hft_simulator.engine.trading_engine import TradingEngine
from hft_simulator.strategies.base_strategy import BaseStrategy

# Set up logging
logger = logging.getLogger(__name__)

# Try to import market type constants
try:
    from hft_simulator.data.expanded_markets import (
        MARKET_TYPE_STOCK, MARKET_TYPE_CRYPTO, MARKET_TYPE_FOREX
    )
    MARKET_TYPES_AVAILABLE = True
except ImportError:
    # Define fallback constants
    MARKET_TYPE_STOCK = 'stock'
    MARKET_TYPE_CRYPTO = 'crypto'
    MARKET_TYPE_FOREX = 'forex'
    MARKET_TYPES_AVAILABLE = False

# Custom color schemes
COLOR_SCHEME = {
    "header_bg": "rgb(25,25,37)",
    "header_fg": "rgb(255,255,255)",
    "panel_border": "rgb(114,137,218)",
    "positive": "rgb(67,181,129)",
    "negative": "rgb(240,71,71)",
    "neutral": "rgb(255,204,77)",
    "symbol": "rgb(114,137,218)",
    "price": "rgb(255,204,77)",
    "quantity": "rgb(67,181,129)",
    "time": "rgb(114,137,218)",
    "title": "rgb(255,255,255)",
    "subtitle": "rgb(220,221,222)",
    # Market type colors
    "stock": "rgb(114,137,218)",      # Blue
    "crypto": "rgb(255,165,0)",       # Orange
    "forex": "rgb(50,205,50)"         # Green
}

# Market type icons
MARKET_TYPE_ICONS = {
    MARKET_TYPE_STOCK: "🏢 ",    # Building for stocks/companies
    MARKET_TYPE_CRYPTO: "🔶 ",   # Diamond for crypto
    MARKET_TYPE_FOREX: "💱 "     # Currency exchange for forex
}

class TerminalUI:
    """
    Enhanced Terminal UI for displaying market data and trading information.
    """
    
    def __init__(self, 
                 trading_engine: TradingEngine, 
                 strategy: BaseStrategy,
                 symbols: List[str],
                 refresh_rate: float = 1.0):
        """
        Initialize the terminal UI.
        
        Args:
            trading_engine: Trading engine
            strategy: Trading strategy
            symbols: List of symbols to display
            refresh_rate: UI refresh rate in seconds
        """
        self.trading_engine = trading_engine
        self.strategy = strategy
        self.symbols = symbols
        self.refresh_rate = refresh_rate
        
        # Market data
        self.market_data = {}
        
        # Console for output
        self.console = Console()
        
        # Layout
        self.layout = Layout()
        
        # Track last trade timestamp for animation
        self.last_trade_time = datetime.now()
        self.trade_animation_frames = 10
        self.current_animation_frame = 0
        
        # Track price changes
        self.previous_prices = {symbol: 0.0 for symbol in symbols}
        
        # Track portfolio equity history (last 10 points)
        self.equity_history = []
        
        # Track symbols by market type
        self.symbols_by_market = {
            MARKET_TYPE_STOCK: [],
            MARKET_TYPE_CRYPTO: [],
            MARKET_TYPE_FOREX: []
        }
        
        # Set up layout
        self._setup_layout()
        
        # Thread for UI updates
        self.ui_thread = None
        self.stop_event = threading.Event()
        
        logger.info(f"Enhanced Terminal UI initialized with refresh rate {refresh_rate}s")
    
    def _setup_layout(self) -> None:
        """Set up the UI layout."""
        # Split into header, body, and footer
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Split body into left and right
        self.layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        # Split left into market data and positions
        self.layout["left"].split(
            Layout(name="market_data"),
            Layout(name="positions")
        )
        
        # Split right into portfolio, orders, and trades
        self.layout["right"].split(
            Layout(name="portfolio", size=10),
            Layout(name="orders"),
            Layout(name="trades")
        )
    
    def update_market_data(self, market_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Update market data.
        
        Args:
            market_data: Market data dictionary
        """
        # Update price changes
        for symbol, data in market_data.items():
            if symbol in self.previous_prices and 'price' in data:
                current_price = data['price']
                self.previous_prices[symbol] = current_price
                
            # Update symbols by market type if available
            if 'market_type' in data:
                market_type = data['market_type']
                if symbol not in self.symbols_by_market[market_type]:
                    self.symbols_by_market[market_type].append(symbol)
        
        self.market_data = market_data
        
        # Update equity history
        portfolio_summary = self.trading_engine.get_portfolio_summary()
        equity = portfolio_summary['equity']
        self.equity_history.append(equity)
        
        # Keep only the last 20 points
        if len(self.equity_history) > 20:
            self.equity_history = self.equity_history[-20:]
    
    def _get_market_type(self, symbol: str) -> str:
        """
        Get market type for a symbol.
        
        Args:
            symbol: Symbol to get market type for
            
        Returns:
            Market type string
        """
        # First check if it's in the market data
        if symbol in self.market_data and 'market_type' in self.market_data[symbol]:
            return self.market_data[symbol]['market_type']
        
        # Otherwise guess based on symbol format
        if '-USD' in symbol or symbol in ['BTC', 'ETH', 'XRP', 'LTC', 'SOL', 'ADA']:
            return MARKET_TYPE_CRYPTO
        
        # Check for forex pairs
        if len(symbol) == 6 and symbol[:3] != symbol[3:]:
            return MARKET_TYPE_FOREX
            
        # Default to stock
        return MARKET_TYPE_STOCK
    
    def _render_header(self) -> Panel:
        """
        Render the header panel.
        
        Returns:
            Header panel
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        text = Text()
        text.append("🚀 ", style="bold")
        text.append("HFT Simulator ", style=f"bold {COLOR_SCHEME['header_fg']}")
        text.append("│ ", style="dim")
        text.append(f"Strategy: {self.strategy.name} ", style=f"bold {COLOR_SCHEME['positive']}")
        text.append("│ ", style="dim")
        text.append(f"Time: {now}", style=f"bold {COLOR_SCHEME['symbol']}")
        
        return Panel(
            Align.center(text),
            title="[bold white]High-Frequency Trading Simulator[/]",
            title_align="center",
            border_style=COLOR_SCHEME["panel_border"],
            box=box.ROUNDED
        )
    
    def _render_footer(self) -> Panel:
        """
        Render the footer panel.
        
        Returns:
            Footer panel
        """
        text = Text()
        text.append("Press ", style="dim")
        text.append("Ctrl+C", style="bold")
        text.append(" to exit  ", style="dim")
        text.append("│ ", style="dim")
        text.append("🔄 ", style=COLOR_SCHEME["neutral"])
        text.append(f"Refresh: {self.refresh_rate}s", style="bold")
        
        # Add market type legend if we have multiple markets
        markets_count = sum(1 for market, symbols in self.symbols_by_market.items() if symbols)
        if markets_count > 1:
            text.append("  │ ", style="dim")
            text.append("Markets: ", style="dim")
            
            if self.symbols_by_market[MARKET_TYPE_STOCK]:
                text.append(MARKET_TYPE_ICONS[MARKET_TYPE_STOCK], style=COLOR_SCHEME["stock"])
                text.append("Stock ", style=COLOR_SCHEME["stock"])
            
            if self.symbols_by_market[MARKET_TYPE_CRYPTO]:
                text.append(MARKET_TYPE_ICONS[MARKET_TYPE_CRYPTO], style=COLOR_SCHEME["crypto"])
                text.append("Crypto ", style=COLOR_SCHEME["crypto"])
            
            if self.symbols_by_market[MARKET_TYPE_FOREX]:
                text.append(MARKET_TYPE_ICONS[MARKET_TYPE_FOREX], style=COLOR_SCHEME["forex"])
                text.append("Forex", style=COLOR_SCHEME["forex"])
        
        return Panel(
            Align.center(text),
            border_style=COLOR_SCHEME["panel_border"],
            box=box.ROUNDED
        )
    
    def _render_market_data_panel(self) -> Panel:
        """
        Render the market data panel with price direction indicators.
        
        Returns:
            Market data panel
        """
        table = Table(
            title_style=f"bold {COLOR_SCHEME['title']}",
            border_style=COLOR_SCHEME["panel_border"],
            box=box.SIMPLE_HEAD
        )
        
        # Add columns
        table.add_column("Market", style="bold", justify="left", width=7)
        table.add_column("Symbol", style=COLOR_SCHEME["symbol"], justify="left")
        table.add_column("Price", style=COLOR_SCHEME["price"], justify="right")
        table.add_column("Change", justify="right")
        table.add_column("Bid", style=COLOR_SCHEME["positive"], justify="right")
        table.add_column("Ask", style=COLOR_SCHEME["negative"], justify="right")
        table.add_column("Volume", style="cyan", justify="right")
        
        # Collect symbols by market type
        markets_with_data = {}
        
        # First check if we have market_type in the data
        has_market_type = any('market_type' in data for symbol, data in self.market_data.items())
        
        # If not, assign market types by format
        if not has_market_type:
            for symbol in self.symbols:
                market_type = self._get_market_type(symbol)
                if market_type not in markets_with_data:
                    markets_with_data[market_type] = []
                markets_with_data[market_type].append(symbol)
        else:
            # Use market types from the data
            for symbol, data in self.market_data.items():
                if 'market_type' in data:
                    market_type = data['market_type']
                    if market_type not in markets_with_data:
                        markets_with_data[market_type] = []
                    markets_with_data[market_type].append(symbol)
        
        # Sort market types in the order: stocks, crypto, forex
        market_order = [MARKET_TYPE_STOCK, MARKET_TYPE_CRYPTO, MARKET_TYPE_FOREX]
        
        # Add rows by market type
        for market_type in market_order:
            if market_type in markets_with_data and markets_with_data[market_type]:
                symbols = sorted(markets_with_data[market_type])
                
                # Add a market type header row
                market_icon = MARKET_TYPE_ICONS.get(market_type, "")
                market_name = market_type.capitalize()
                market_style = COLOR_SCHEME.get(market_type, "white")
                
                table.add_row(
                    Text(f"{market_icon}{market_name}", style=f"bold {market_style}"),
                    "", "", "", "", "", "",
                    style=f"on rgb(20,20,30) {market_style}"
                )
                
                # Add symbol rows
                for symbol in symbols:
                    if symbol in self.market_data:
                        data = self.market_data[symbol]
                        
                        price = data.get('price', 0)
                        bid = data.get('bid', 0)
                        ask = data.get('ask', 0)
                        volume = data.get('volume', 0)
                        
                        # Determine price change direction
                        prev_price = self.previous_prices.get(symbol, price)
                        if price > prev_price:
                            price_change = f"▲ ${price - prev_price:.2f}"
                            change_style = COLOR_SCHEME["positive"]
                        elif price < prev_price:
                            price_change = f"▼ ${prev_price - price:.2f}"
                            change_style = COLOR_SCHEME["negative"]
                        else:
                            price_change = f"• ${0:.2f}"
                            change_style = COLOR_SCHEME["neutral"]
                        
                        # Format values with appropriate precision based on market type
                        if market_type == MARKET_TYPE_STOCK:
                            price_str = f"${price:.2f}"
                            bid_str = f"${bid:.2f}"
                            ask_str = f"${ask:.2f}"
                        elif market_type == MARKET_TYPE_CRYPTO:
                            if price > 1000:
                                price_str = f"${price:.2f}"
                                bid_str = f"${bid:.2f}"
                                ask_str = f"${ask:.2f}"
                            elif price > 10:
                                price_str = f"${price:.3f}"
                                bid_str = f"${bid:.3f}"
                                ask_str = f"${ask:.3f}"
                            else:
                                price_str = f"${price:.4f}"
                                bid_str = f"${bid:.4f}"
                                ask_str = f"${ask:.4f}"
                        elif market_type == MARKET_TYPE_FOREX:
                            if price > 50:  # JPY pairs
                                price_str = f"{price:.3f}"
                                bid_str = f"{bid:.3f}"
                                ask_str = f"{ask:.3f}"
                            else:
                                price_str = f"{price:.4f}"
                                bid_str = f"{bid:.4f}"
                                ask_str = f"{ask:.4f}"
                        else:
                            price_str = f"${price:.2f}"
                            bid_str = f"${bid:.2f}"
                            ask_str = f"${ask:.2f}"
                            
                        volume_str = f"{volume:,}"
                        
                        table.add_row(
                            "",  # No market icon in row
                            symbol,
                            price_str,
                            Text(price_change, style=change_style),
                            bid_str,
                            ask_str,
                            volume_str
                        )
                    else:
                        table.add_row("", symbol, "N/A", "N/A", "N/A", "N/A", "N/A")
        
        if not self.market_data:
            table.add_row("", "[dim]No market data available[/dim]", "", "", "", "", "")
        
        return Panel(
            table,
            title="📊 Market Data",
            border_style=COLOR_SCHEME["panel_border"],
            box=box.ROUNDED
        )
    
    def _render_positions_panel(self) -> Panel:
        """
        Render the positions panel with enhanced visuals.
        
        Returns:
            Positions panel
        """
        table = Table(
            title_style=f"bold {COLOR_SCHEME['title']}",
            border_style=COLOR_SCHEME["panel_border"],
            box=box.SIMPLE_HEAD
        )
        
        # Add columns
        table.add_column("Market", style="bold", justify="left", width=7)
        table.add_column("Symbol", style=COLOR_SCHEME["symbol"], justify="left")
        table.add_column("Quantity", style=COLOR_SCHEME["quantity"], justify="right")
        table.add_column("Avg Price", style=COLOR_SCHEME["price"], justify="right")
        table.add_column("Current", style="bold cyan", justify="right")
        table.add_column("P&L", justify="right")
        table.add_column("P&L %", justify="right")
        
        # Get positions
        positions = self.trading_engine.get_open_positions()
        
        # Group positions by market type
        positions_by_market = {}
        
        for position in positions:
            symbol = position['symbol']
            market_type = self._get_market_type(symbol)
            
            if market_type not in positions_by_market:
                positions_by_market[market_type] = []
                
            positions_by_market[market_type].append(position)
        
        # Sort market types in the order: stocks, crypto, forex
        market_order = [MARKET_TYPE_STOCK, MARKET_TYPE_CRYPTO, MARKET_TYPE_FOREX]
        
        # Add rows by market type
        for market_type in market_order:
            if market_type in positions_by_market and positions_by_market[market_type]:
                # Add a market type header row
                market_icon = MARKET_TYPE_ICONS.get(market_type, "")
                market_name = market_type.capitalize()
                market_style = COLOR_SCHEME.get(market_type, "white")
                
                table.add_row(
                    Text(f"{market_icon}{market_name}", style=f"bold {market_style}"),
                    "", "", "", "", "", "",
                    style=f"on rgb(20,20,30) {market_style}"
                )
                
                # Add position rows for this market
                for position in positions_by_market[market_type]:
                    symbol = position['symbol']
                    quantity = f"{position['quantity']}"
                    
                    # Format average price based on market type
                    if market_type == MARKET_TYPE_FOREX and not symbol.endswith('JPY'):
                        avg_price = f"{position['average_price']:.4f}"
                    else:
                        avg_price = f"${position['average_price']:.2f}"
                    
                    # Get current price
                    current_price = 0.0
                    if symbol in self.market_data and 'price' in self.market_data[symbol]:
                        current_price = self.market_data[symbol]['price']
                    
                    # Format current price based on market type
                    if market_type == MARKET_TYPE_FOREX and not symbol.endswith('JPY'):
                        current = f"{current_price:.4f}"
                    else:
                        current = f"${current_price:.2f}"
                    
                    # Calculate P&L
                    pnl = (current_price - position['average_price']) * position['quantity']
                    pnl_pct = (current_price / position['average_price'] - 1) * 100 * (1 if position['quantity'] > 0 else -1)
                    
                    # Format P&L with colors
                    pnl_str = f"${pnl:.2f}"
                    pnl_pct_str = f"{pnl_pct:.2f}%"
                    
                    pnl_style = COLOR_SCHEME["positive"] if pnl >= 0 else COLOR_SCHEME["negative"]
                    
                    table.add_row(
                        "",  # No market icon in row
                        symbol,
                        quantity,
                        avg_price,
                        current,
                        Text(pnl_str, style=pnl_style),
                        Text(pnl_pct_str, style=pnl_style)
                    )
        
        if not positions:
            table.add_row("", "[dim]No open positions[/dim]", "", "", "", "", "")
        
        return Panel(
            table,
            title="📈 Positions",
            border_style=COLOR_SCHEME["panel_border"],
            box=box.ROUNDED
        )
    
    def _render_portfolio_panel(self) -> Panel:
        """
        Render the portfolio panel with mini equity chart.
        
        Returns:
            Portfolio panel
        """
        # Get portfolio summary
        summary = self.trading_engine.get_portfolio_summary()
        
        # Create a simple chart of equity values using blocks
        chart = ""
        if len(self.equity_history) > 1:
            min_equity = min(self.equity_history)
            max_equity = max(self.equity_history)
            range_equity = max_equity - min_equity if max_equity > min_equity else 1.0
            
            # Make sure we have a valid range
            if range_equity > 0:
                blocks = "▁▂▃▄▅▆▇█"
                for equity in self.equity_history:
                    # Calculate height (0-7)
                    normalized = (equity - min_equity) / range_equity
                    idx = min(int(normalized * 7), 7)
                    chart += blocks[idx]
        
        # Count positions by market
        positions_count = {
            MARKET_TYPE_STOCK: 0,
            MARKET_TYPE_CRYPTO: 0,
            MARKET_TYPE_FOREX: 0
        }
        
        for position in self.trading_engine.get_open_positions():
            market_type = self._get_market_type(position['symbol'])
            positions_count[market_type] += 1
        
        # Create market allocation text
        market_allocation = []
        for market_type, count in positions_count.items():
            if count > 0:
                market_name = market_type.capitalize()
                market_icon = MARKET_TYPE_ICONS.get(market_type, "")
                market_style = COLOR_SCHEME.get(market_type, "white")
                market_allocation.append(
                    Text(f"{market_icon}{market_name}: {count}", style=market_style)
                )
        
        allocation_text = Text()
        for i, text in enumerate(market_allocation):
            allocation_text.append(text)
            if i < len(market_allocation) - 1:
                allocation_text.append(" | ")
        
        # Create portfolio summary
        portfolio_items = [
            Text(f"Cash: ${summary['cash']:.2f}", style=f"bold {COLOR_SCHEME['positive']}"),
            Text(f"Equity: ${summary['equity']:.2f}", style=f"bold {COLOR_SCHEME['symbol']}"),
            Text(""),
            Text("Equity Trend:", style="dim"),
            Text(chart or "Not enough data", style=COLOR_SCHEME["neutral"]),
            Text(""),
            # Calculate return with color
            Text(f"Return: {summary['return']:.2%}", 
                style=f"bold {COLOR_SCHEME['positive'] if summary['return'] >= 0 else COLOR_SCHEME['negative']}"),
        ]
        
        # Add market allocation if we have multiple markets
        if sum(positions_count.values()) > 0 and len([c for c in positions_count.values() if c > 0]) > 1:
            portfolio_items.extend([
                Text(""),
                Text("Market Allocation:", style="dim"),
                allocation_text
            ])
        else:
            portfolio_items.extend([
                Text(f"Positions: {summary['position_count']}", style=COLOR_SCHEME["neutral"]),
                Text(f"Trades: {summary['total_trades']}", style=COLOR_SCHEME["symbol"])
            ])
        
        text = Group(*portfolio_items)
        
        return Panel(
            text,
            title="💰 Portfolio",
            border_style=COLOR_SCHEME["panel_border"],
            box=box.ROUNDED
        )
    
    def _render_orders_panel(self) -> Panel:
        """
        Render the orders panel with enhanced visuals.
        
        Returns:
            Orders panel
        """
        table = Table(
            title_style=f"bold {COLOR_SCHEME['title']}",
            border_style=COLOR_SCHEME["panel_border"],
            box=box.SIMPLE_HEAD
        )
        
        # Add columns
        table.add_column("Market", style="bold", justify="left", width=7)
        table.add_column("Symbol", style=COLOR_SCHEME["symbol"], justify="left")
        table.add_column("Side", justify="center")
        table.add_column("Qty", style=COLOR_SCHEME["quantity"], justify="right")
        table.add_column("Type", style="cyan", justify="center")
        table.add_column("Price", style=COLOR_SCHEME["price"], justify="right")
        
        # Get active orders
        orders = self.trading_engine.get_active_orders()
        
        # Group orders by market type
        orders_by_market = {}
        
        for order in orders:
            symbol = order['symbol']
            market_type = self._get_market_type(symbol)
            
            if market_type not in orders_by_market:
                orders_by_market[market_type] = []
                
            orders_by_market[market_type].append(order)
        
        # Sort market types in the order: stocks, crypto, forex
        market_order = [MARKET_TYPE_STOCK, MARKET_TYPE_CRYPTO, MARKET_TYPE_FOREX]
        
        # Add rows by market type
        for market_type in market_order:
            if market_type in orders_by_market and orders_by_market[market_type]:
                # Add a market type header row
                market_icon = MARKET_TYPE_ICONS.get(market_type, "")
                market_name = market_type.capitalize()
                market_style = COLOR_SCHEME.get(market_type, "white")
                
                table.add_row(
                    Text(f"{market_icon}{market_name}", style=f"bold {market_style}"),
                    "", "", "", "", "",
                    style=f"on rgb(20,20,30) {market_style}"
                )
                
                # Add order rows for this market
                for order in orders_by_market[market_type]:
                    symbol = order['symbol']
                    
                    # Format side with icon
                    side = order['side']
                    if side == "buy":
                        side_text = Text("🔼 BUY", style=COLOR_SCHEME["positive"])
                    else:
                        side_text = Text("🔽 SELL", style=COLOR_SCHEME["negative"])
                        
                    quantity = f"{order['quantity']}"
                    order_type = order['order_type'].upper()
                    
                    # Format price based on order type and market type
                    if order['price']:
                        if market_type == MARKET_TYPE_FOREX and not symbol.endswith('JPY'):
                            price = f"{order['price']:.4f}"
                        else:
                            price = f"${order['price']:.2f}"
                    else:
                        price = "MARKET"
                    
                    table.add_row(
                        "",
                        symbol,
                        side_text,
                        quantity,
                        order_type,
                        price
                    )
        
        if not orders:
            table.add_row("", "[dim]No active orders[/dim]", "", "", "", "")
        
        return Panel(
            table,
            title="📋 Active Orders",
            border_style=COLOR_SCHEME["panel_border"],
            box=box.ROUNDED
        )
    
    def _render_trades_panel(self) -> Panel:
        """
        Render the trades panel with animations for recent trades.
        
        Returns:
            Trades panel
        """
        table = Table(
            title_style=f"bold {COLOR_SCHEME['title']}",
            border_style=COLOR_SCHEME["panel_border"],
            box=box.SIMPLE_HEAD
        )
        
        # Add columns
        table.add_column("Market", style="bold", justify="left", width=7)
        table.add_column("Symbol", style=COLOR_SCHEME["symbol"], justify="left")
        table.add_column("Side", justify="center")
        table.add_column("Qty", style=COLOR_SCHEME["quantity"], justify="right")
        table.add_column("Price", style=COLOR_SCHEME["price"], justify="right")
        table.add_column("Time", style=COLOR_SCHEME["time"], justify="right")
        
        # Get recent trades
        trades = self.trading_engine.get_recent_trades(count=5)
        
        # Check if we have new trades for animation
        if trades and trades[0]['timestamp'] > self.last_trade_time:
            self.last_trade_time = trades[0]['timestamp']
            self.current_animation_frame = self.trade_animation_frames
        
        # Animation frames countdown
        if self.current_animation_frame > 0:
            self.current_animation_frame -= 1
        
        # Group trades by market type (just for display)
        last_market_type = None
        
        # Add rows
        for i, trade in enumerate(trades):
            symbol = trade['symbol']
            market_type = self._get_market_type(symbol)
            
            # Format side with animation for new trades
            side = trade['side']
            highlight = i == 0 and self.current_animation_frame > 0
            
            if side == "buy":
                side_style = f"{COLOR_SCHEME['positive']} bold" if highlight else COLOR_SCHEME["positive"]
                side_text = "🔼 BUY"
            else:
                side_style = f"{COLOR_SCHEME['negative']} bold" if highlight else COLOR_SCHEME["negative"]
                side_text = "🔽 SELL"
                
            quantity = f"{trade['quantity']}"
            
            # Format price based on market type
            if market_type == MARKET_TYPE_FOREX and not symbol.endswith('JPY'):
                price = f"{trade['price']:.4f}"
            else:
                price = f"${trade['price']:.2f}"
                
            time_str = trade['timestamp'].strftime("%H:%M:%S")
            
            # Check if we need to add a market header
            show_market = last_market_type != market_type
            last_market_type = market_type
            
            if show_market:
                # Add a market type header row
                market_icon = MARKET_TYPE_ICONS.get(market_type, "")
                market_name = market_type.capitalize()
                market_style = COLOR_SCHEME.get(market_type, "white")
                
                table.add_row(
                    Text(f"{market_icon}{market_name}", style=f"bold {market_style}"),
                    "", "", "", "", "",
                    style=f"on rgb(20,20,30) {market_style}"
                )
            
            # Highlight new trade row
            if highlight:
                row_style = "bold"
                # Pulsing effect
                intensity = int(255 * (self.current_animation_frame / self.trade_animation_frames) * 0.3 + 0.7)
                bg_style = f"on rgb({intensity},{intensity},{intensity})"
                
                table.add_row(
                    Text("", style=f"{row_style} {bg_style}"),
                    Text(symbol, style=f"{row_style} {bg_style}"),
                    Text(side_text, style=f"{side_style} {bg_style}"),
                    Text(quantity, style=f"{row_style} {bg_style}"),
                    Text(price, style=f"{row_style} {bg_style}"),
                    Text(time_str, style=f"{row_style} {bg_style}")
                )
            else:
                table.add_row(
                    "",
                    symbol,
                    Text(side_text, style=side_style),
                    quantity,
                    price,
                    time_str
                )
        
        if not trades:
            table.add_row("", "[dim]No recent trades[/dim]", "", "", "", "")
        
        return Panel(
            table,
            title="🔄 Recent Trades",
            border_style=COLOR_SCHEME["panel_border"],
            box=box.ROUNDED
        )
    
    def update(self) -> None:
        """Update the UI."""
        # Update panels
        self.layout["header"].update(self._render_header())
        self.layout["footer"].update(self._render_footer())
        self.layout["market_data"].update(self._render_market_data_panel())
        self.layout["positions"].update(self._render_positions_panel())
        self.layout["portfolio"].update(self._render_portfolio_panel())
        self.layout["orders"].update(self._render_orders_panel())
        self.layout["trades"].update(self._render_trades_panel())
    
    def start(self) -> None:
        """Start the UI."""
        # Create live display
        with Live(self.layout, refresh_per_second=1/self.refresh_rate, screen=True):
            try:
                while not self.stop_event.is_set():
                    self.update()
                    time.sleep(self.refresh_rate)
            except KeyboardInterrupt:
                pass
    
    def stop(self) -> None:
        """Stop the UI."""
        self.stop_event.set()
    
    def run_in_thread(self) -> threading.Thread:
        """
        Run the UI in a background thread.
        
        Returns:
            UI thread
        """
        self.ui_thread = threading.Thread(target=self.start)
        self.ui_thread.daemon = True
        self.ui_thread.start()
        
        return self.ui_thread 