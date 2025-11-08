import unittest
import pandas as pd
import backtrader as bt
from event_driven_backtester import BacktraderEngine
from strategies.ema_cross_atr_stops import EmaCrossAtrStops

class TestStrategies(unittest.TestCase):
    def test_ema_cross_atr_stops_enters_and_exits(self):
        # Create a deterministic dataset with a clear EMA crossover
        closes = [100] * 20 + list(range(101, 122)) + [120, 119, 118]
        datetimes = pd.to_datetime(pd.date_range(start='2023-01-01', periods=len(closes)))
        data = {
            'datetime': datetimes,
            'open': closes,
            'high': [p + 2 for p in closes],
            'low': [p - 2 for p in closes],
            'close': closes,
            'volume': [1000] * len(closes)
        }
        df = pd.DataFrame(data)
        df.set_index('datetime', inplace=True)

        class TestStrategy(EmaCrossAtrStops):
            def __init__(self):
                super().__init__()
                self.trade_count = 0
            
            def notify_trade(self, trade):
                super().notify_trade(trade)
                if trade.isclosed:
                    self.trade_count += 1
        
        # Run the backtest
        backtester = BacktraderEngine(TestStrategy, df, ema9_length=5, ema21_length=10) # Use shorter periods for faster signals
        cerebro = backtester.run()

        # Get the strategy instance from cerebro
        strategy_instance = cerebro.runstrats[0][0]

        # Assert that at least one trade was opened and closed
        self.assertGreater(strategy_instance.trade_count, 0, "No trades were closed during the backtest.")
        
        # Optional: Assert final portfolio value is different from initial capital
        self.assertNotEqual(cerebro.broker.getvalue(), 100000.0, "Portfolio value did not change, indicating no trades were likely executed.")


if __name__ == '__main__':
    unittest.main()
