"""
Trading engine for HFT simulator.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from .orders import Order, OrderSide, OrderType, OrderStatus, Trade

# Set up logging
logger = logging.getLogger(__name__)

class TradingEngine:
    """
    Trading engine that processes orders and maintains positions.
    """
    
    def __init__(self, 
                 initial_cash: float = 100000.0, 
                 commission: float = 0.001, 
                 slippage: float = 0.0005):
        """
        Initialize the trading engine.
        
        Args:
            initial_cash: Initial cash amount
            commission: Commission rate (as a fraction)
            slippage: Slippage rate (as a fraction)
        """
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.commission_rate = commission
        self.slippage_rate = slippage
        
        # Track positions, orders, and trades
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Order] = {}
        self.trades: List[Trade] = []
        
        # Calculate equity (cash + position value)
        self.equity = initial_cash
        
        logger.info(f"Trading engine initialized with ${initial_cash:.2f} cash")
    
    def place_order(self, order: Order) -> str:
        """
        Place an order in the trading engine.
        
        Args:
            order: Order to place
            
        Returns:
            Order ID
        """
        # Store order
        self.orders[order.id] = order
        
        logger.info(f"Placed {order.side.value} order for {order.quantity} {order.symbol} "
                   f"({order.order_type.value}{f' at {order.price:.2f}' if order.price else ''})")
        
        return order.id
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: ID of order to cancel
            
        Returns:
            True if order was cancelled, False otherwise
        """
        if order_id not in self.orders:
            logger.warning(f"Order {order_id} not found")
            return False
            
        order = self.orders[order_id]
        
        # Can only cancel active orders
        if not order.is_active():
            logger.warning(f"Order {order_id} is not active (status: {order.status.value})")
            return False
            
        # Cancel order
        order.status = OrderStatus.CANCELLED
        
        logger.info(f"Cancelled order {order_id}")
        return True
    
    def process_market_data(self, market_data: Dict[str, Dict[str, Any]]) -> List[Trade]:
        """
        Process market data and execute orders.
        
        Args:
            market_data: Market data dictionary
            
        Returns:
            List of trades executed
        """
        executed_trades: List[Trade] = []
        
        # Process active orders for symbols in market data
        for symbol, data in market_data.items():
            # Find active orders for this symbol
            active_orders = [
                order for order in self.orders.values()
                if order.symbol == symbol and order.is_active()
            ]
            
            # Execute orders
            for order in active_orders:
                # Try to execute order
                trade = self._execute_order(order, data)
                
                # If trade executed, add to list
                if trade:
                    executed_trades.append(trade)
        
        # Update equity
        self._update_equity(market_data)
        
        return executed_trades
    
    def _execute_order(self, order: Order, market_data: Dict[str, Any]) -> Optional[Trade]:
        """
        Execute an order against market data.
        
        Args:
            order: Order to execute
            market_data: Market data for the order's symbol
            
        Returns:
            Trade if order was executed, None otherwise
        """
        # Check if we have necessary price data
        if 'bid' not in market_data or 'ask' not in market_data:
            logger.warning(f"Missing bid/ask data for {order.symbol}")
            return None
        
        # Get execution price
        execution_price = self._get_execution_price(order, market_data)
        
        # If no execution price, can't execute order
        if execution_price is None:
            return None
            
        # Calculate execution quantity
        quantity_to_execute = order.quantity - order.filled_quantity
        
        # Calculate commission
        commission = execution_price * quantity_to_execute * self.commission_rate
        
        # Check if we have enough cash for buy orders
        if order.is_buy():
            cost = execution_price * quantity_to_execute + commission
            if cost > self.cash:
                # Adjust quantity based on available cash
                max_quantity = (self.cash - commission) / execution_price
                
                if max_quantity <= 0:
                    logger.warning(f"Insufficient cash for order {order.id}")
                    return None
                    
                quantity_to_execute = min(quantity_to_execute, max_quantity)
                commission = execution_price * quantity_to_execute * self.commission_rate
                
                logger.warning(f"Adjusted order quantity to {quantity_to_execute} due to insufficient cash")
        
        # Execute trade
        trade_id = str(uuid.uuid4())
        
        trade = Trade(
            id=trade_id,
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            quantity=quantity_to_execute,
            price=execution_price,
            timestamp=datetime.now(),
            commission=commission
        )
        
        # Update order
        order.filled_quantity += quantity_to_execute
        
        if order.filled_quantity >= order.quantity:
            order.status = OrderStatus.FILLED
        else:
            order.status = OrderStatus.PARTIALLY_FILLED
            
        # For weighted average price calculation
        if order.filled_price is None:
            order.filled_price = execution_price
        else:
            # Weighted average
            order.filled_price = (
                (order.filled_price * (order.filled_quantity - quantity_to_execute) + 
                 execution_price * quantity_to_execute) / 
                order.filled_quantity
            )
        
        # Update cash
        if order.is_buy():
            self.cash -= execution_price * quantity_to_execute + commission
        else:
            self.cash += execution_price * quantity_to_execute - commission
        
        # Update position
        self._update_position(trade)
        
        # Store trade
        self.trades.append(trade)
        
        logger.info(f"Executed {order.side.value} trade for {quantity_to_execute} {order.symbol} "
                   f"at ${execution_price:.2f}, commission ${commission:.2f}")
        
        return trade
    
    def _get_execution_price(self, order: Order, market_data: Dict[str, Any]) -> Optional[float]:
        """
        Calculate execution price for an order.
        
        Args:
            order: Order to execute
            market_data: Market data for the order's symbol
            
        Returns:
            Execution price or None if order can't be executed
        """
        # Get bid/ask prices
        bid_price = market_data['bid']
        ask_price = market_data['ask']
        
        # For market orders
        if order.is_market():
            if order.is_buy():
                # Buy at ask price with slippage
                return ask_price * (1.0 + self.slippage_rate)
            else:
                # Sell at bid price with slippage
                return bid_price * (1.0 - self.slippage_rate)
                
        # For limit orders
        elif order.is_limit():
            if order.is_buy():
                # Check if limit price is high enough
                if order.price >= ask_price:
                    # Execute at ask price (or better if possible)
                    return min(order.price, ask_price * (1.0 + self.slippage_rate))
                else:
                    # Can't execute
                    return None
            else:
                # Check if limit price is low enough
                if order.price <= bid_price:
                    # Execute at bid price (or better if possible)
                    return max(order.price, bid_price * (1.0 - self.slippage_rate))
                else:
                    # Can't execute
                    return None
        
        # Should never get here
        logger.error(f"Unknown order type: {order.order_type}")
        return None
    
    def _update_position(self, trade: Trade) -> None:
        """
        Update position based on trade.
        
        Args:
            trade: Trade that was executed
        """
        symbol = trade.symbol
        
        # Initialize position if needed
        if symbol not in self.positions:
            self.positions[symbol] = {
                'symbol': symbol,
                'quantity': 0,
                'average_price': 0,
                'cost_basis': 0,
                'realized_pnl': 0
            }
            
        position = self.positions[symbol]
        current_quantity = position['quantity']
        current_cost = position['cost_basis']
        
        # Update position
        if trade.side == OrderSide.BUY:
            # Adding to position
            new_quantity = current_quantity + trade.quantity
            
            # Update cost basis
            if new_quantity > 0:
                new_cost = current_cost + (trade.price * trade.quantity)
                position['average_price'] = new_cost / new_quantity
                position['cost_basis'] = new_cost
            
            position['quantity'] = new_quantity
            
        else:  # SELL
            # Reducing position
            new_quantity = current_quantity - trade.quantity
            
            # Calculate realized P&L for this trade
            if current_quantity > 0:
                realized_pnl = (trade.price - position['average_price']) * min(current_quantity, trade.quantity)
                position['realized_pnl'] += realized_pnl
                
                # Update cost basis
                if new_quantity > 0:
                    position['cost_basis'] = position['average_price'] * new_quantity
                else:
                    # Position closed or reversed
                    position['cost_basis'] = 0
                    
                    if new_quantity < 0:
                        # Short position
                        position['average_price'] = trade.price
                        position['cost_basis'] = trade.price * abs(new_quantity)
                        
            else:  # current_quantity <= 0
                # Already short or flat
                if new_quantity < current_quantity:
                    # Adding to short position
                    position['cost_basis'] = trade.price * abs(new_quantity)
                    position['average_price'] = trade.price
                else:
                    # Covering short position
                    realized_pnl = (position['average_price'] - trade.price) * min(abs(current_quantity), trade.quantity)
                    position['realized_pnl'] += realized_pnl
                    
                    if new_quantity == 0:
                        # Flat
                        position['cost_basis'] = 0
                        position['average_price'] = 0
                    elif new_quantity > 0:
                        # Reversed to long
                        position['average_price'] = trade.price
                        position['cost_basis'] = trade.price * new_quantity
            
            position['quantity'] = new_quantity
    
    def _update_equity(self, market_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Update equity based on current positions and market data.
        
        Args:
            market_data: Market data dictionary
        """
        # Start with cash
        equity = self.cash
        
        # Add value of all positions
        for symbol, position in self.positions.items():
            if position['quantity'] == 0:
                continue
                
            # Get current price
            if symbol in market_data:
                # Use mid price as current price
                if 'price' in market_data[symbol]:
                    current_price = market_data[symbol]['price']
                else:
                    bid = market_data[symbol].get('bid', 0)
                    ask = market_data[symbol].get('ask', 0)
                    if bid > 0 and ask > 0:
                        current_price = (bid + ask) / 2
                    else:
                        # Fall back to previous equity
                        continue
                        
                # Calculate position value
                position_value = position['quantity'] * current_price
                equity += position_value
        
        # Update equity
        self.equity = equity
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Get list of open positions.
        
        Returns:
            List of position dictionaries
        """
        # Filter to positions with non-zero quantity
        return [
            position for position in self.positions.values()
            if position['quantity'] != 0
        ]
    
    def get_active_orders(self) -> List[Dict[str, Any]]:
        """
        Get list of active orders.
        
        Returns:
            List of order dictionaries
        """
        # Filter to active orders
        return [
            order.to_dict() for order in self.orders.values()
            if order.is_active()
        ]
    
    def get_recent_trades(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of recent trades.
        
        Args:
            count: Number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        # Get most recent trades
        return [
            trade.to_dict() for trade in sorted(
                self.trades, key=lambda t: t.timestamp, reverse=True
            )[:count]
        ]
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get portfolio summary.
        
        Returns:
            Dictionary with portfolio summary
        """
        return {
            'cash': self.cash,
            'equity': self.equity,
            'initial_cash': self.initial_cash,
            'return': (self.equity - self.initial_cash) / self.initial_cash,
            'position_count': len(self.get_open_positions()),
            'total_trades': len(self.trades),
            'active_orders': len(self.get_active_orders())
        } 