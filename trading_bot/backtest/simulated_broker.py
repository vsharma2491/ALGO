import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..brokers.base import BrokerBase

logger = logging.getLogger(__name__)

class SimulatedBroker(BrokerBase):
    """
    A simulated broker for backtesting purposes. It mimics the interface
    of the live broker but does not execute real trades.
    """
    def __init__(self):
        super().__init__()
        self.trade_history: List[Dict[str, Any]] = []
        self.order_id_counter = 1
        self.authenticated = True # Always authenticated in simulation
        logger.info("SimulatedBroker initialized.")

    async def place_order(self, symbol: str, quantity: int, price: float, transaction_type: str, order_type: str, product: str, exchange: str = 'NSE', tag: str = "strategy") -> Optional[str]:
        """
        Simulates placing an order. In a backtest, orders are assumed to be
        filled immediately at the given price.
        """
        logger.info(f"[SIMULATED] Placing {transaction_type} order for {quantity} {symbol} at {price:.2f}")
        order_id = str(self.order_id_counter)
        self.order_id_counter += 1
        return order_id

    async def log_trade(self, symbol: str, side: str, entry_price: float, exit_price: float, entry_time: datetime, exit_time: datetime, pnl: float, reason: str):
        """
        Logs a completed trade to the internal history. This method is called
        by the TradingBot after a position is closed.
        """
        trade = {
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "entry_time": entry_time.strftime('%Y-%m-%d %H:%M:%S'),
            "exit_time": exit_time.strftime('%Y-%m-%d %H:%M:%S'),
            "pnl": pnl,
            "exit_reason": reason
        }
        self.trade_history.append(trade)
        logger.info(f"[SIMULATED] Logged trade: {trade}")

    def get_trade_history(self) -> List[Dict[str, Any]]:
        """
        Returns the history of all trades executed during the simulation.
        """
        return self.trade_history