import pandas as pd
import numpy as np
from strategies.base_strategy import Strategy

class MaCrossover(Strategy):
    """
    A simple moving average crossover strategy.
    """
    def __init__(self, data, short_window=2, long_window=4):
        self.data = data
        self.short_window = short_window
        self.long_window = long_window
        self.position = 0
        self.signals = self._generate_signals()

    def _generate_signals(self):
        """Generates the trading signals."""
        signals = pd.DataFrame(index=self.data.index)
        signals['signal'] = 0.0

        # Create short and long simple moving averages
        signals['short_mavg'] = self.data['close'].rolling(window=self.short_window, min_periods=1, center=False).mean()
        signals['long_mavg'] = self.data['close'].rolling(window=self.long_window, min_periods=1, center=False).mean()

        # Create signals
        signal_values = np.where(signals['short_mavg'][self.short_window:] > signals['long_mavg'][self.short_window:], 1.0, 0.0)
        signals['signal'] = 0.0
        signals.iloc[self.short_window:, signals.columns.get_loc('signal')] = signal_values

        # Generate trading orders
        signals['positions'] = signals['signal'].diff()

        return signals

    def next(self, bar):
        """
        This method is not used in this vectorized backtest example.
        The signals are pre-computed in the `_generate_signals` method.
        """
        pass
