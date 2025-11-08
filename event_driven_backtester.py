import backtrader as bt
import pandas as pd

class BacktraderEngine:
    """
    An event-driven backtesting engine using the backtrader library.
    """
    def __init__(self, strategy_class, data, initial_capital=100000.0, **kwargs):
        self.strategy_class = strategy_class
        self.data = data
        self.initial_capital = initial_capital
        self.kwargs = kwargs
        self.cerebro = bt.Cerebro()

    def run(self):
        """
        Runs the backtest.
        """
        # Add the strategy
        self.cerebro.addstrategy(self.strategy_class, **self.kwargs)

        # Add the data feed
        data_feed = bt.feeds.PandasData(dataname=self.data)
        self.cerebro.adddata(data_feed)

        # Set our desired cash start
        self.cerebro.broker.setcash(self.initial_capital)

        # Set the commission
        self.cerebro.broker.setcommission(commission=0.001)

        # Print out the starting conditions
        print('Starting Portfolio Value: %.2f' % self.cerebro.broker.getvalue())

        # Run over everything
        self.cerebro.run()

        # Print out the final result
        print('Final Portfolio Value: %.2f' % self.cerebro.broker.getvalue())

        return self.cerebro
