import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import pandas as pd
from datetime import datetime, timedelta

from trading_bot.backtest.engine import BacktestEngine

class TestBacktestEngine(unittest.TestCase):
    """Tests for the BacktestEngine."""

    @patch('trading_bot.backtest.engine.TradingBot')
    def test_data_fetching_chunking(self, MockTradingBot):
        """
        Verify that the backtest engine correctly fetches historical data in chunks.
        """
        # --- Arrange ---
        mock_bot_instance = MockTradingBot.return_value
        mock_bot_instance.on_tick = AsyncMock()

        mock_live_broker = MagicMock()
        chunk1 = [{'time': '2023-01-01', 'intc': 100}]
        chunk2 = [{'time': '2023-04-01', 'intc': 102}]
        mock_live_broker.get_historical_data.side_effect = [chunk1, chunk2, None]
        mock_live_broker.get_token.return_value = 'DUMMY_TOKEN'

        mock_simulated_broker = MagicMock()
        mock_simulated_broker.get_trade_history.return_value = []

        bot_config = {
            'name': 'TestBot', 'symbol': 'TEST', 'exchange': 'NSE',
            'trading': { 'max_concurrent_positions': 10, 'trading_start_hour': 9, 'trading_start_minute': 15, 'trading_end_hour': 15, 'trading_end_minute': 30 },
            'strategy': { 'name': 'ma_crossover', 'short_ma_period': 10, 'long_ma_period': 20 }
        }

        start_date = '2023-01-01'
        end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=100)).strftime('%Y-%m-%d')

        # --- Act ---
        import asyncio
        engine = BacktestEngine(bot_config, mock_live_broker, mock_simulated_broker, start_date, end_date)
        asyncio.run(engine.run())

        # --- Assert ---
        self.assertGreaterEqual(mock_live_broker.get_historical_data.call_count, 2)
        first_call_args = mock_live_broker.get_historical_data.call_args_list[0].kwargs
        self.assertEqual(first_call_args['start_date'], '2023-01-01')
        self.assertEqual(first_call_args['end_date'], '2023-04-01')

        second_call_args = mock_live_broker.get_historical_data.call_args_list[1].kwargs
        self.assertEqual(second_call_args['start_date'], '2023-04-02')

if __name__ == '__main__':
    unittest.main()