from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

class BrokerBase(ABC):
    """Abstract base class for all broker implementations."""

    def __init__(self):
        self.authenticated = False
        self.access_token = None

    @abstractmethod
    async def place_order(self, symbol: str, quantity: int, price: float, transaction_type: str, order_type: str, product: str, exchange: str = 'NSE', tag: str = "strategy") -> Optional[str]:
        """Places a trading order."""
        pass

    @abstractmethod
    async def log_trade(self, symbol: str, side: str, entry_price: float, exit_price: float, entry_time: datetime, exit_time: datetime, pnl: float, reason: str):
        """Logs a completed trade."""
        pass