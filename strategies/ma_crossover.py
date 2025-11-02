import pandas as pd
from strategies.base_strategy import Strategy

class MACrossover(Strategy):
    """
    A simple moving average crossover strategy.
    """
    def __init__(self, data, short_window=50, long_window=200):
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
        signals['signal'][self.short_window:] = np.where(signals['short_mavg'][self.short_window:]
                                                    > signals['long_mavg'][self.short_window:], 1.0, 0.0)

        # Generate trading orders
        signals['positions'] = signals['signal'].diff()

        return signals

    def next(self, bar):
        """
        This method is not used in this vectorized backtest example.
        The signals are pre-computed in the `_generate_signals` method.
        """
        pass
