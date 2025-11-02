import unittest
import pandas as pd
from backtest_engine import Backtester
from strategies.ma_crossover import MACrossover

class TestBacktester(unittest.TestCase):
    """
    Unit tests for the Backtester class.
    """
    def setUp(self):
        """
        Set up a simple dataset and strategy for testing.
        """
        data = {
            'datetime': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']),
            'close': [100, 102, 101, 103, 105]
        }
        self.data = pd.DataFrame(data).set_index('datetime')

        class DummyStrategy:
            def __init__(self, data):
                self.signals = pd.DataFrame(index=data.index)
                self.signals['positions'] = [0, 1, 0, -1, 0]

        self.strategy = DummyStrategy(self.data)
        self.backtester = Backtester(self.strategy, self.data, 100000, {})

    def test_performance_calculation(self):
        """
        Test that the performance metrics are calculated correctly.
        """
        results, _, _ = self.backtester.run()

        self.assertIn("Total Return", results)
        self.assertIn("Sharpe Ratio", results)
        self.assertIn("Max Drawdown", results)

        self.assertEqual(results['Total Trades'], 2)

if __name__ == '__main__':
    unittest.main()
