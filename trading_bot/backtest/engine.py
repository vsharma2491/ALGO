import logging
import pandas as pd
from datetime import datetime, timedelta

from ..bot.trading_bot import TradingBot

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Handles the execution of a backtest for a given trading bot and strategy.
    """
    def __init__(self, bot_config: dict, live_broker, simulated_broker, start_date: str, end_date: str):
        """
        Initializes the BacktestEngine.

        Args:
            bot_config (dict): The configuration for the bot to be backtested.
            live_broker: The broker instance used to fetch historical data.
            simulated_broker: The broker instance used for simulated trading.
            start_date (str): The start date for the backtest (YYYY-MM-DD).
            end_date (str): The end date for the backtest (YYYY-MM-DD).
        """
        self.bot_config = bot_config
        self.live_broker = live_broker
        self.simulated_broker = simulated_broker
        self.start_date = start_date
        self.end_date = end_date

        class MockTelegramHandler:
            async def send_message(self, message: str):
                logger.info(f"[TELEGRAM_MOCK] {message}")

        self.telegram_handler = MockTelegramHandler()

        instrument_token = self.live_broker.get_token(bot_config['exchange'], bot_config['symbol'])
        if not instrument_token:
            raise ValueError(f"Could not get token for {bot_config['symbol']}")

        self.bot = TradingBot(
            config=self.bot_config,
            broker=self.simulated_broker,
            telegram_handler=self.telegram_handler,
            instrument_token=instrument_token
        )

    async def run(self):
        """Runs the backtest."""
        logger.info(f"Starting backtest for {self.bot_config['name']} from {self.start_date} to {self.end_date}...")

        # Fetch historical data in chunks
        all_data = []
        current_start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
        end_date_dt = datetime.strptime(self.end_date, '%Y-%m-%d')
        while current_start_date < end_date_dt:
            chunk_end_date = current_start_date + timedelta(days=90)
            if chunk_end_date > end_date_dt: chunk_end_date = end_date_dt

            logger.info(f"Fetching data from {current_start_date.strftime('%Y-%m-%d')} to {chunk_end_date.strftime('%Y-%m-%d')}")
            data_chunk = self.live_broker.get_historical_data(
                symbol=self.bot_config['symbol'], exchange=self.bot_config['exchange'],
                start_date=current_start_date.strftime('%Y-%m-%d'), end_date=chunk_end_date.strftime('%Y-%m-%d'),
                interval='1'
            )
            if data_chunk: all_data.extend(data_chunk)
            current_start_date = chunk_end_date + timedelta(days=1)

        if not all_data:
            logger.error("Failed to fetch any historical data. Aborting backtest.")
            return

        historical_data = pd.DataFrame(all_data).sort_values(by='time').reset_index(drop=True)
        if 'intc' not in historical_data.columns:
            logger.error("Historical data does not contain 'intc' (close price) column.")
            return

        # Simulate the event loop
        for index, row in historical_data.iterrows():
            tick_data = { 'tk': self.bot.instrument_token, 'lp': float(row['intc']) }
            await self.bot.on_tick(tick_data)

        logger.info("Backtest finished.")
        self.generate_report()

    def generate_report(self):
        """Generates a summary report of the backtest."""
        logger.info("Generating backtest report...")
        trades = self.simulated_broker.get_trade_history()
        if not trades:
            logger.info("No trades were executed during the backtest.")
            return

        total_pnl = sum(trade['pnl'] for trade in trades)
        wins = [trade for trade in trades if trade['pnl'] > 0]
        win_rate = (len(wins) / len(trades)) * 100 if trades else 0

        logger.info("--- Backtest Summary ---")
        logger.info(f"Total Trades: {len(trades)}")
        logger.info(f"Total P&L: {total_pnl:.2f}")
        logger.info(f"Win Rate: {win_rate:.2f}%")
        logger.info(f"Wins: {len(wins)}")
        logger.info(f"Losses: {len(trades) - len(wins)}")
        logger.info("------------------------")

        df = pd.DataFrame(trades)
        report_filename = f"backtest_report_{self.bot_config['name']}_{self.start_date}_to_{self.end_date}.csv"
        df.to_csv(report_filename, index=False)
        logger.info(f"Backtest report saved to {report_filename}")