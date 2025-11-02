class Strategy:
    """
    A base class for all trading strategies.
    """
    def init(self):
        """
        This method is called once at the beginning of the backtest.
        Use it to initialize any indicators or variables.
        """
        pass

    def next(self, bar):
        """
        This method is called for each bar of data in the backtest.

        Args:
            bar (pd.Series): The current bar of data.
        """
        raise NotImplementedError("The 'next' method must be implemented by the subclass.")
