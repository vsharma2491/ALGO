from strategies.base_strategy import Strategy

class StrategyTemplate(Strategy):
    """
    A template for creating new trading strategies.
    """
    def init(self):
        """
        Initialize any indicators or variables here.
        """
        # Example: self.sma = moving_average(self.data, 20)
        pass

    def next(self, bar):
        """
        Implement your strategy logic here.

        Args:
            bar (pd.Series): The current bar of data.
        """
        # --- Time-based filters ---
        # Example: Avoid trading in the first and last 15 minutes of the day
        if bar.name.time() < pd.to_datetime('09:30').time() or bar.name.time() > pd.to_datetime('15:15').time():
            return

        # --- Entry logic ---
        # Example: Go long if the close is above the 20-period SMA
        # if bar['close'] > self.sma[-1] and not self.position:
        #     self.buy()

        # --- Exit logic ---
        # Example: Go short if the close is below the 20-period SMA
        # elif bar['close'] < self.sma[-1] and self.position:
        #     self.sell()

        # --- Risk management ---
        # Example: Stop loss and take profit
        # if self.position:
        #     if bar['close'] < self.entry_price * 0.99: # 1% stop loss
        #         self.sell()
        #     elif bar['close'] > self.entry_price * 1.02: # 2% take profit
        #         self.sell()

        pass
