import logging
from typing import Set

logger = logging.getLogger(__name__)

class RiskManager:
    """Manages trading risk by enforcing predefined rules."""

    def __init__(self, max_concurrent_positions: int):
        """
        Initializes the RiskManager.

        Args:
            max_concurrent_positions (int): The maximum number of positions that can be open at the same time.
        """
        self.max_concurrent_positions = max_concurrent_positions
        self.closed_today: Set[str] = set()
        logger.info(f"RiskManager initialized with max concurrent positions: {max_concurrent_positions}.")

    def can_open_new_position(self, symbol: str, current_position_count: int) -> bool:
        """
        Checks if a new position can be opened based on the risk rules.

        Args:
            symbol (str): The symbol for the potential new position.
            current_position_count (int): The current number of open positions.

        Returns:
            bool: True if a new position can be opened, False otherwise.
        """
        if current_position_count >= self.max_concurrent_positions:
            logger.debug(f"Cannot open new position: max concurrent positions ({self.max_concurrent_positions}) reached.")
            return False

        if symbol in self.closed_today:
            logger.debug(f"Cannot open new position for {symbol}: already traded today.")
            return False

        return True

    def add_closed_position(self, symbol: str):
        """
        Adds a symbol to the set of positions that have been closed today.

        Args:
            symbol (str): The symbol of the closed position.
        """
        self.closed_today.add(symbol)
        logger.info(f"Added {symbol} to today's closed positions. No re-entry allowed.")

    def reset(self):
        """Resets the risk manager's state for a new trading day."""
        self.closed_today.clear()
        logger.info("RiskManager state has been reset for the new trading day.")