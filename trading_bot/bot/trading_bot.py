import asyncio
import logging
import pandas as pd
from datetime import datetime, time
from typing import Dict, Any

from .telegram_handler import TelegramHandler
from .position_manager import PositionManager
from .risk_manager import RiskManager
from . import indicators

logger = logging.getLogger(__name__)

class TradingBot:
    """The main class for the trading bot."""

    def __init__(self, config: Dict[str, Any], broker, telegram_handler: TelegramHandler, instrument_token: str):
        self.bot_config = config
        self.broker = broker
        self.telegram_handler = telegram_handler
        self.position_manager = PositionManager()
        self.risk_manager = RiskManager(config['trading']['max_concurrent_positions'])
        self.instrument_token = instrument_token

        self.is_running = False
        self.tick_prices = []
        self.historical_prices = pd.DataFrame(columns=['open', 'high', 'low', 'close'])

        self.trading_start_time = time(config['trading']['trading_start_hour'], config['trading']['trading_start_minute'])
        self.trading_end_time = time(config['trading']['trading_end_hour'], config['trading']['trading_end_minute'])

    def is_market_open(self) -> bool:
        """Checks if the market is currently open."""
        now = datetime.now().time()
        return self.trading_start_time <= now <= self.trading_end_time

    async def run(self):
        """Starts the main trading loop of the bot."""
        self.is_running = True
        await self.telegram_handler.send_message(f"{self.bot_config['name']} started.")
        logger.info(f"{self.bot_config['name']} started.")

        self.broker.connect_websocket(tick_callback=self.on_tick)
        self.broker.subscribe([self.bot_config['symbol']], exchange=self.bot_config['exchange'])

        while self.is_running:
            if self.is_market_open():
                await self.check_positions_for_sl_tp()
            else:
                await self.handle_market_close()
            await asyncio.sleep(self.bot_config['trading']['check_interval_seconds'])

    def stop(self):
        self.is_running = False
        logger.info(f"{self.bot_config['name']} stopping.")

    async def on_tick(self, tick_data):
        """Callback to handle incoming ticks and resample them into 1-minute bars."""
        if tick_data.get('tk') != self.instrument_token:
            return

        current_price = float(tick_data.get('lp', 0.0))
        if current_price == 0.0: return

        self.tick_prices.append({'price': current_price, 'time': datetime.now()})

        # Resample ticks into 1-minute bars
        if len(self.tick_prices) > 1 and (self.tick_prices[-1]['time'].minute != self.tick_prices[-2]['time'].minute):
            df = pd.DataFrame(self.tick_prices)
            df.set_index('time', inplace=True)

            # Create 1-minute candle
            resampled_df = df['price'].resample('1Min').ohlc()
            if not resampled_df.empty:
                new_bar = resampled_df.iloc[-1]
                self.historical_prices = pd.concat([self.historical_prices, pd.DataFrame([new_bar])], ignore_index=True)
                self.tick_prices = [] # Clear ticks for the next bar

                logger.debug(f"New 1-minute bar for {self.bot_config['symbol']}: {new_bar.to_dict()}")
                await self.on_bar(new_bar['close'])

    async def on_bar(self, current_price: float):
        """Executes the trading strategy on a new 1-minute bar."""
        if len(self.historical_prices) < self.bot_config['strategy']['long_ma_period']:
            return
        await self.execute_strategy(current_price)

    async def execute_strategy(self, current_price: float):
        """Executes the trading strategy based on the latest price data."""
        symbol = self.bot_config['symbol']
        position = self.position_manager.get_position(symbol)

        short_ma = indicators.calculate_ma(self.historical_prices['close'], self.bot_config['strategy']['short_ma_period']).iloc[-1]
        long_ma = indicators.calculate_ma(self.historical_prices['close'], self.bot_config['strategy']['long_ma_period']).iloc[-1]

        if position is None:
            if short_ma > long_ma and self.risk_manager.can_open_new_position(symbol, self.position_manager.get_open_position_count()):
                await self.open_position('BUY', current_price)
        else:
            if position.side == 'BUY' and short_ma < long_ma:
                await self.close_position(symbol, "MA Crossover Exit")

    async def open_position(self, side: str, price: float):
        """Opens a new trading position."""
        symbol = self.bot_config['symbol']
        position_size = self.bot_config['trading']['position_size_inr']
        quantity = position_size / price

        stop_loss = price * (1 - self.bot_config['trading']['stop_loss_pct'] / 100) if side == 'BUY' else price * (1 + self.bot_config['trading']['stop_loss_pct'] / 100)
        profit_target = price * (1 + self.bot_config['trading']['profit_target_pct'] / 100) if side == 'BUY' else price * (1 - self.bot_config['trading']['profit_target_pct'] / 100)

        order_id = await self.broker.place_order(
            symbol=symbol, quantity=int(quantity), price=price,
            transaction_type=side, order_type='MARKET', product='MIS',
            exchange=self.bot_config['exchange']
        )

        if order_id:
            self.position_manager.add_position(symbol, side, price, quantity, stop_loss, profit_target, datetime.now())
            await self.telegram_handler.send_message(f"Opened {side} position for {symbol} at {price:.2f}")

    async def check_positions_for_sl_tp(self):
        """Checks all open positions for stop-loss or profit-target triggers."""
        if not self.tick_prices: return
        current_price = self.tick_prices[-1]['price']

        for symbol, position in list(self.position_manager.get_all_positions().items()):
            position.update_pnl(current_price)

            reason = None
            if position.side == 'BUY':
                if current_price <= position.stop_loss_price: reason = "Stop-Loss"
                elif current_price >= position.profit_target_price: reason = "Profit-Target"
            else: # SELL
                if current_price >= position.stop_loss_price: reason = "Stop-Loss"
                elif current_price <= position.profit_target_price: reason = "Profit-Target"

            if reason:
                await self.close_position(symbol, reason)

    async def close_position(self, symbol: str, reason: str):
        """Closes an open position."""
        position = self.position_manager.get_position(symbol)
        if not position: return

        current_price = self.tick_prices[-1]['price'] if self.tick_prices else position.entry_price
        side = 'SELL' if position.side == 'BUY' else 'BUY'

        order_id = await self.broker.place_order(
            symbol=symbol, quantity=int(position.quantity), price=current_price,
            transaction_type=side, order_type='MARKET', product='MIS',
            exchange=self.bot_config['exchange']
        )

        if order_id:
            position.update_pnl(current_price)
            await self.telegram_handler.send_message(f"Closed {position.side} position for {symbol} at {current_price:.2f}. P&L: {position.pnl:.2f}. Reason: {reason}")
            await self.broker.log_trade(symbol, position.side, position.entry_price, current_price, position.entry_time, datetime.now(), position.pnl, reason)
            self.position_manager.remove_position(symbol)
            self.risk_manager.add_closed_position(symbol)

    async def handle_market_close(self):
        """Handles the market close procedure."""
        if self.position_manager.get_open_position_count() > 0:
            await self.telegram_handler.send_message("Market is closing. Closing all open positions.")
            for symbol in list(self.position_manager.get_all_positions().keys()):
                await self.close_position(symbol, "EOD")

        self.risk_manager.reset()
        self.tick_prices = []
        self.historical_prices = pd.DataFrame(columns=['open', 'high', 'low', 'close'])
        logger.info("Market closed. Ready for the next trading day.")