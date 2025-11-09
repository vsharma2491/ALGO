import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import pandas as pd

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from event_driven_backtester import BacktraderEngine

class TestEventDrivenBacktester(unittest.TestCase):

    def setUp(self):
        """
        Set up a simple dataset and strategy for testing.
        """
        data = {
            'datetime': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']),
            'open': [100, 102, 101, 103, 105],
            'high': [101, 103, 102, 104, 106],
            'low': [99, 101, 100, 102, 104],
            'close': [100, 102, 101, 103, 105],
            'volume': [1000, 1200, 1100, 1300, 1400]
        }
        self.data = pd.DataFrame(data).set_index('datetime')

    @patch('event_driven_backtester.bt.Cerebro')
    def test_backtrader_engine_run(self, mock_cerebro):
        """
        Test that the BacktraderEngine class correctly initializes and runs
        a backtrader backtest.
        """
        mock_cerebro_instance = MagicMock()
        mock_cerebro.return_value = mock_cerebro_instance

        class DummyStrategy:
            pass

        engine = BacktraderEngine(DummyStrategy, self.data, 100000)
        engine.run()

        mock_cerebro_instance.addstrategy.assert_called_once_with(DummyStrategy)
        mock_cerebro_instance.adddata.assert_called_once()
        mock_cerebro_instance.broker.setcash.assert_called_once_with(100000)
        mock_cerebro_instance.run.assert_called_once()

if __name__ == '__main__':
    unittest.main()
