import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class Position:
    """Represents a single open trading position."""

    def __init__(self, symbol: str, side: str, entry_price: float, quantity: float, stop_loss: float, profit_target: float, entry_time: datetime):
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.quantity = quantity
        self.stop_loss_price = stop_loss
        self.profit_target_price = profit_target
        self.entry_time = entry_time
        self.pnl = 0.0

    def update_pnl(self, current_price: float):
        """Updates the profit and loss for the position."""
        if self.side == 'BUY':
            self.pnl = (current_price - self.entry_price) * self.quantity
        else: # SELL
            self.pnl = (self.entry_price - current_price) * self.quantity

class PositionManager:
    """Manages all open trading positions."""

    def __init__(self):
        self.open_positions: Dict[str, Position] = {}
        logger.info("PositionManager initialized.")

    def add_position(self, symbol: str, side: str, entry_price: float, quantity: float, stop_loss: float, profit_target: float, entry_time: datetime):
        """Adds a new position to the manager."""
        if symbol in self.open_positions:
            logger.warning(f"Position for {symbol} already exists. Cannot add a new one.")
            return
        position = Position(symbol, side, entry_price, quantity, stop_loss, profit_target, entry_time)
        self.open_positions[symbol] = position
        logger.info(f"Added new {side} position for {symbol} at {entry_price}.")

    def remove_position(self, symbol: str):
        """Removes a position from the manager."""
        if symbol in self.open_positions:
            del self.open_positions[symbol]
            logger.info(f"Removed position for {symbol}.")
        else:
            logger.warning(f"No open position found for {symbol} to remove.")

    def get_position(self, symbol: str) -> Optional[Position]:
        """Retrieves a position by its symbol."""
        return self.open_positions.get(symbol)

    def get_all_positions(self) -> Dict[str, Position]:
        """Returns all open positions."""
        return self.open_positions

    def get_open_position_count(self) -> int:
        """Returns the number of open positions."""
        return len(self.open_positions)

    def update_all_positions(self, current_prices: Dict[str, float]):
        """Updates the P&L for all open positions."""
        for symbol, position in self.open_positions.items():
            if symbol in current_prices:
                position.update_pnl(current_prices[symbol])
            else:
                logger.warning(f"No current price available for {symbol} to update P&L.")