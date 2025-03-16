"""
Order types and related classes for the trading engine.
"""

import uuid
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

class OrderSide(Enum):
    """Order side (buy or sell)."""
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    """Order type (market or limit)."""
    MARKET = "market"
    LIMIT = "limit"

class OrderStatus(Enum):
    """Order status."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass
class Order:
    """
    An order to buy or sell a financial instrument.
    """
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType
    price: Optional[float] = None
    timestamp: datetime = None
    id: str = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0
    filled_price: Optional[float] = None
    
    def __post_init__(self):
        """Initialize after creation."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        # Validate fields
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("Limit orders must have a price")
            
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
    
    def is_buy(self) -> bool:
        """Return True if this is a buy order."""
        return self.side == OrderSide.BUY
    
    def is_sell(self) -> bool:
        """Return True if this is a sell order."""
        return self.side == OrderSide.SELL
    
    def is_market(self) -> bool:
        """Return True if this is a market order."""
        return self.order_type == OrderType.MARKET
    
    def is_limit(self) -> bool:
        """Return True if this is a limit order."""
        return self.order_type == OrderType.LIMIT
    
    def is_active(self) -> bool:
        """Return True if this order is still active."""
        return (self.status == OrderStatus.PENDING or 
                self.status == OrderStatus.PARTIALLY_FILLED)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'order_type': self.order_type.value,
            'price': self.price,
            'timestamp': self.timestamp,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'filled_price': self.filled_price
        }

@dataclass
class Trade:
    """
    A trade resulting from an order execution.
    """
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime = None
    commission: float = 0.0
    
    def __post_init__(self):
        """Initialize after creation."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'price': self.price,
            'timestamp': self.timestamp,
            'commission': self.commission
        } 