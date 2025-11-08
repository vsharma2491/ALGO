import pandas as pd
import numpy as np

# Parameters (as per your Pine Script)
ema9_length = 9
ema21_length = 21
atr_length = 14
atr_multiplier_sl = 2.0
atr_multiplier_tp = 3.0
atr_multiplier_tsl = 1.5

# Calculate EMAs
df['ema9'] = df['close'].ewm(span=ema9_length, adjust=False).mean()
df['ema21'] = df['close'].ewm(span=ema21_length, adjust=False).mean()

# Calculate ATR
high_low = df['high'] - df['low']
high_close = np.abs(df['high'] - df['close'].shift())
low_close = np.abs(df['low'] - df['close'].shift())
tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
df['atr'] = tr.rolling(window=atr_length).mean()

# Initialize tracking variables
position = 0  # 1 for long, -1 for short, 0 for no position
entry_price = 0
long_sl = 0
long_tp = 0
short_sl = 0
short_tp = 0
highest_price_since_long = 0
lowest_price_since_short = 0
long_trailing_sl = 0
short_trailing_sl = 0

# Lists to store signals and orders
signals = []
orders = []

for i in range(len(df)):
    row = df.iloc[i]
    
    # Entry signals
    if row['ema9'] > row['ema21'] and position <= 0:
        # Enter long
        position = 1
        entry_price = row['close']
        long_sl = entry_price - row['atr'] * atr_multiplier_sl
        long_tp = entry_price + row['atr'] * atr_multiplier_tp
        highest_price_since_long = row['high']
        long_trailing_sl = long_sl
        signals.append('Long Entry')
        orders.append(('buy', row['timestamp']))

    elif row['ema9'] < row['ema21'] and position >= 0:
        # Enter short
        position = -1
        entry_price = row['close']
        short_sl = entry_price + row['atr'] * atr_multiplier_sl
        short_tp = entry_price - row['atr'] * atr_multiplier_tp
        lowest_price_since_short = row['low']
        short_trailing_sl = short_sl
        signals.append('Short Entry')
        orders.append(('sell', row['timestamp']))

    # For existing long position
    if position == 1:
        highest_price_since_long = max(highest_price_since_long, row['high'])
        potential_trailing_sl = highest_price_since_long - row['atr'] * atr_multiplier_tsl
        long_trailing_sl = max(long_trailing_sl, potential_trailing_sl)
        # Exit conditions
        if row['close'] <= long_trailing_sl or row['close'] >= long_tp:
            signals.append('Long Exit')
            orders.append(('sell', row['timestamp']))
            position = 0

    # For existing short position
    if position == -1:
        lowest_price_since_short = min(lowest_price_since_short, row['low'])
        potential_trailing_sl = lowest_price_since_short + row['atr'] * atr_multiplier_tsl
        short_trailing_sl = min(short_trailing_sl, potential_trailing_sl)
        # Exit conditions
        if row['close'] >= short_trailing_sl or row['close'] <= short_tp:
            signals.append('Short Exit')
            orders.append(('buy', row['timestamp']))
            position = 0

# This is a simplified illustration.  
# You can expand this based on your backtesting framework, include order sizes, and execute actual trades.
