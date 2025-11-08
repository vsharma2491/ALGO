import backtrader as bt

class EmaCrossAtrStops(bt.Strategy):
    """
    9/21 EMA Cross Strategy with ATR Stops, implemented in backtrader.
    """
    params = (
        ('ema9_length', 9),
        ('ema21_length', 21),
        ('atr_length', 14),
        ('atr_multiplier_sl', 2.0),
        ('atr_multiplier_tp', 3.0),
        ('atr_multiplier_tsl', 1.5),
    )

    def __init__(self):
        self.ema9 = bt.indicators.EMA(self.data.close, period=self.p.ema9_length)
        self.ema21 = bt.indicators.EMA(self.data.close, period=self.p.ema21_length)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_length)

        # To track orders
        self.entry_order = None
        self.stop_loss_order = None
        self.take_profit_order = None
        
        # To track trailing stop prices
        self.highest_price_since_long_entry = 0
        self.lowest_price_since_short_entry = float('inf')

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
            elif order.issell():
                self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        if not order.alive():
            if order == self.entry_order:
                self.entry_order = None


    def notify_trade(self, trade):
        if trade.isopen:
            self.log(f"POSITION OPENED, Size: {trade.size}, Price: {trade.price:.2f}")
            if trade.long:
                self.highest_price_since_long_entry = self.data.high[0]
                # Place stop loss and take profit
                sl_price = trade.price - (self.atr[0] * self.p.atr_multiplier_sl)
                tp_price = trade.price + (self.atr[0] * self.p.atr_multiplier_tp)
                self.stop_loss_order = self.sell(exectype=bt.Order.Stop, price=sl_price)
                self.take_profit_order = self.sell(exectype=bt.Order.Limit, price=tp_price)
            elif trade.short:
                self.lowest_price_since_short_entry = self.data.low[0]
                # Place stop loss and take profit
                sl_price = trade.price + (self.atr[0] * self.p.atr_multiplier_sl)
                tp_price = trade.price - (self.atr[0] * self.p.atr_multiplier_tp)
                self.stop_loss_order = self.buy(exectype=bt.Order.Stop, price=sl_price)
                self.take_profit_order = self.buy(exectype=bt.Order.Limit, price=tp_price)
            return

        if trade.isclosed:
            self.log(f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}")
            # A trade is closed, cancel any pending related orders
            if self.stop_loss_order and self.stop_loss_order.alive():
                self.cancel(self.stop_loss_order)
            if self.take_profit_order and self.take_profit_order.alive():
                self.cancel(self.take_profit_order)

    def next(self):
        if self.entry_order:
            return

        # Explicitly define crossover conditions
        buy_signal = self.ema9[0] > self.ema21[0] and self.ema9[-1] <= self.ema21[-1]
        sell_signal = self.ema9[0] < self.ema21[0] and self.ema9[-1] >= self.ema21[-1]

        if not self.position:
            if buy_signal:
                self.log(f"BUY CREATE, {self.data.close[0]:.2f}")
                self.entry_order = self.buy()
            elif sell_signal:
                self.log(f"SELL CREATE, {self.data.close[0]:.2f}")
                self.entry_order = self.sell()
        else:
            if self.position.size > 0: # Long position
                self.highest_price_since_long_entry = max(self.highest_price_since_long_entry, self.data.high[0])
                tsl_price = self.highest_price_since_long_entry - (self.atr[0] * self.p.atr_multiplier_tsl)
                
                if self.stop_loss_order and tsl_price > self.stop_loss_order.price:
                    self.cancel(self.stop_loss_order)
                    self.stop_loss_order = self.sell(exectype=bt.Order.Stop, price=tsl_price)
                    self.log(f"Long Trailing Stop moved to {tsl_price:.2f}")
            
            elif self.position.size < 0: # Short position
                self.lowest_price_since_short_entry = min(self.lowest_price_since_short_entry, self.data.low[0])
                tsl_price = self.lowest_price_since_short_entry + (self.atr[0] * self.p.atr_multiplier_tsl)

                if self.stop_loss_order and tsl_price < self.stop_loss_order.price:
                    self.cancel(self.stop_loss_order)
                    self.stop_loss_order = self.buy(exectype=bt.Order.Stop, price=tsl_price)
                    self.log(f"Short Trailing Stop moved to {tsl_price:.2f}")
