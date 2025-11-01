import pandas as pd
import numpy as np

# Load CSV data
df = pd.read_csv(r'c:/Users/vivek/Desktop/algo/NIFTY DATA/NIFTY50-INDEX.csv')

# Convert 'Date' column to datetime and set as index
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

# Filter data for trading hours 09:17 to 15:15
df = df.between_time('09:17', '15:15')

# Drop 'index' column if it exists
if 'index' in df.columns:
    df.drop(columns=['index'], inplace=True)

# Calculate SMAs: 20 and 50 periods
df['SMA_20'] = df['Close'].rolling(window=20).mean()
df['SMA_50'] = df['Close'].rolling(window=50).mean()

# Generate trading signals
df['signal'] = 0
df.loc[df['SMA_20'] > df['SMA_50'], 'signal'] = 1
df.loc[df['SMA_20'] < df['SMA_50'], 'signal'] = -1

# Calculate returns and strategy returns
df['returns'] = df['Close'].pct_change()
df['strategy_returns'] = df['signal'].shift(1) * df['returns']

# Calculate cumulative returns for buy-hold and strategy
df['cumulative_returns'] = (1 + df['returns']).cumprod()
df['cumulative_strategy_returns'] = (1 + df['strategy_returns']).cumprod()

# Performance metrics
total_return = df['cumulative_strategy_returns'].iloc[-1] - 1
sharpe_ratio = df['strategy_returns'].mean() / df['strategy_returns'].std() * np.sqrt(252 * 6.5 * 60)  # approx for 1-min data over trading days

print("\nBacktest Results:")
print(f"Total Return: {total_return*100:.2f}%")
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")

# Show last few data points
print("\nLast few strategy data points:")
print(df[['Close', 'signal', 'cumulative_strategy_returns']].tail())
df.to_csv('Nifty50_20_50_SMA_backtest_full_results.csv')
print("All backtest results saved to Nifty50_20_50_SMA_backtest_full_results.csv")

