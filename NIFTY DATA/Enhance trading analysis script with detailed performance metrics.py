import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data (CSV assumed with datetime index)
# --- IMPORTANT: Please update this path to your actual file location ---
file_path = r'c:/Users/vivek/Desktop/algo/NIFTY DATA/NIFTY50-INDEX.csv'
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"Error: The file was not found at {file_path}")
    print("Please update the 'file_path' variable in the script with the correct location of your CSV file.")
    exit()

df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

# Filter market hours
df = df.between_time('09:17', '15:15')

# Drop 'index' column if it exists
if 'index' in df.columns:
    df.drop(columns=['index'], inplace=True)

# Calculate SMAs and drop NaNs created by rolling mean
df['SMA_20'] = df['Close'].rolling(20).mean()
df['SMA_50'] = df['Close'].rolling(50).mean()
df.dropna(inplace=True)

# Generate trading signals (1=buy, -1=sell)
df['signal'] = 0
df.loc[df['SMA_20'] > df['SMA_50'], 'signal'] = 1
df.loc[df['SMA_20'] < df['SMA_50'], 'signal'] = -1

# --- Trade-by-Trade Analysis ---
df['position_change'] = df['signal'].diff()
trades = []
in_trade = False
entry_date = None
entry_price = 0
trade_type = 0

for index, row in df.iterrows():
    if not in_trade and row['signal'] != 0:
        in_trade = True
        entry_date = index
        entry_price = row['Close']
        trade_type = row['signal']
    elif in_trade and (row['position_change'] != 0 or index == df.index[-1]):
        exit_date = index
        exit_price = row['Close']
        
        if trade_type == 1:
            pnl = (exit_price - entry_price) / entry_price
        elif trade_type == -1:
            pnl = (entry_price - exit_price) / entry_price
        else:
            pnl = 0
            
        duration = exit_date - entry_date
        
        trades.append({
            'Entry_Date': entry_date,
            'Exit_Date': exit_date,
            'Entry_Price': entry_price,
            'Exit_Price': exit_price,
            'Trade_Type': 'Long' if trade_type == 1 else 'Short',
            'PnL': pnl,
            'Duration': duration
        })
        
        if row['signal'] != 0:
            entry_date = index
            entry_price = row['Close']
            trade_type = row['signal']
        else:
            in_trade = False

trades_df = pd.DataFrame(trades)

# --- Enhanced Performance Metrics ---
print("----- Comprehensive Performance Analysis -----")
if not trades_df.empty:
    total_trades = len(trades_df)
    winning_trades = trades_df[trades_df['PnL'] > 0]
    losing_trades = trades_df[trades_df['PnL'] <= 0]
    num_winning_trades = len(winning_trades)
    num_losing_trades = len(losing_trades)
    win_rate = (num_winning_trades / total_trades) * 100 if total_trades > 0 else 0
    
    total_profit = winning_trades['PnL'].sum()
    total_loss = losing_trades['PnL'].sum()
    
    average_profit = winning_trades['PnL'].mean()
    average_loss = losing_trades['PnL'].mean()
    
    risk_reward_ratio = abs(average_profit / average_loss) if average_loss != 0 else np.nan
    
    df['returns'] = df['Close'].pct_change()
    df['strategy_returns'] = df['signal'].shift(1) * df['returns']
    daily_returns = df['strategy_returns'].resample('D').sum()
    
    if len(daily_returns) > 1 and daily_returns.std() != 0:
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
    else:
        sharpe_ratio = 0

    print(f"Total Trades: {total_trades}")
    print(f"Winning Trades: {num_winning_trades}")
    print(f"Losing Trades: {num_losing_trades}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Total Profit (Sum of winning trades PnL): {total_profit:.4f}")
    print(f"Total Loss (Sum of losing trades PnL): {total_loss:.4f}")
    print(f"Average Profit per Winning Trade: {average_profit:.4f}")
    print(f"Average Loss per Losing Trade: {average_loss:.4f}")
    print(f"Risk/Reward Ratio: {risk_reward_ratio:.2f}")
    print(f"Annualized Sharpe Ratio: {sharpe_ratio:.2f}\n")
else:
    print("No trades were executed, so no performance metrics to calculate.\n")

# --- Print Trade-by-Trade Results ---
print("----- Full Trade-by-Trade Log -----")
pd.set_option('display.max_rows',100000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 1000)

if not trades_df.empty:
    print(trades_df)
    trades_df.to_csv('Nifty50_SMA_Crossover_Trade_Log.csv', index=False)
    print("\nTrade-by-trade log saved to Nifty50_SMA_Crossover_Trade_Log.csv")
else:
    print("No trades were executed based on the strategy.")

# --- Day-wise PnL Summary ---
df['pnl'] = df['strategy_returns'].cumsum()
df['cumulative_max'] = df['pnl'].cummax()
df['drawdown'] = df['pnl'] - df['cumulative_max']
max_drawdown = df['drawdown'].min()

daywise_results = pd.DataFrame({
    'Daily PnL': daily_returns,
    'Cumulative PnL': daily_returns.cumsum(),
})

print("\n----- Full Day-wise PnL -----")
print(daywise_results)
daywise_results.to_csv('Nifty50_SMA_Crossover_Daywise_Results.csv')
print("\nDaywise results saved to Nifty50_SMA_Crossover_Daywise_Results.csv")
print(f"\nMax Drawdown: {max_drawdown:.4f}")

# --- Generate and Save PnL Curve Plot ---
if not daywise_results.empty:
    plt.figure(figsize=(12, 6))
    plt.plot(daywise_results['Cumulative PnL'], label='Cumulative PnL')
    plt.title('SMA Crossover Strategy - Cumulative PnL Curve')
    plt.xlabel('Date')
    plt.ylabel('Cumulative PnL')
    plt.grid(True)
    plt.legend()
    plt.savefig('pnl_curve.png')
    print("\nPnL curve plot saved to pnl_curve.png")
else:
    print("\nNo data to plot.")