import pandas as pd
import numpy as np
import multiprocessing
from datetime import datetime
import mplfinance as mpf
import matplotlib
import matplotlib.pyplot as plt
from tabulate import tabulate
import sys
import locale
import os

def prepare_data(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist.")
            return None
        df = pd.read_csv(file_path, parse_dates=['date'])
        df.rename(columns={
            'date': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low',
            'close': 'Close', 'volume': 'Volume'}, inplace=True, errors='ignore')
        df.sort_values('Date', inplace=True)
        df.reset_index(drop=True, inplace=True)
        start_date = pd.Timestamp('2024-01-01')
        end_date = pd.Timestamp('2024-12-31 23:59:59')
        df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        if df.empty:
            print(f"Error: DataFrame empty after filtering for January 2024.")
            return None
        df['Typical'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = df['Typical'].expanding().mean()
        return df
    except Exception as e:
        print(f"Error in prepare_data: {e}")
        return None

def calculate_indicators(df, macd_fast=12, macd_slow=26, macd_sig=9):
    try:
        def ema(series, period):
            return series.ewm(span=period, adjust=False).mean()
        df['EMA_fast'] = ema(df['Close'], macd_fast)
        df['EMA_slow'] = ema(df['Close'], macd_slow)
        df['MACD'] = df['EMA_fast'] - df['EMA_slow']
        df['MACD_sig'] = ema(df['MACD'], macd_sig)
        df['EMA200'] = ema(df['Close'], 200)
        df['macd_cross_up'] = (df['MACD'] > df['MACD_sig']) & (df['MACD'].shift(1) <= df['MACD_sig'].shift(1))
        df['macd_cross_down'] = (df['MACD'] < df['MACD_sig']) & (df['MACD'].shift(1) >= df['MACD_sig'].shift(1))
        return df
    except Exception as e:
        print(f"Error in calculate_indicators: {e}")
        return None

def generate_signals(df):
    try:
        df['bullish'] = df['Close'] > df['EMA200']
        df['bearish'] = df['Close'] < df['EMA200']
        df['longCond'] = df['macd_cross_up'] & df['bullish']
        df['shortCond'] = df['macd_cross_down'] & df['bearish']
        return df
    except Exception as e:
        print(f"Error in generate_signals: {e}")
        return None

def backtest_strategy(params):
    macd_fast, macd_slow, macd_signal = params
    file_path = r"c:/Users/vivek/Desktop/algo/NIFTY DATA/NIFTY50-INDEX.csv"
    df = prepare_data(file_path)
    if df is None or df.empty:
        return params, 0, 0, 0, []
    try:
        df = calculate_indicators(df, macd_fast, macd_slow, macd_signal)
        df = generate_signals(df)
        min_hold = 1
        cooldown = 1
        max_trades_day = 15
        commission = 0.0001
        slippage = 0.05
        stop_loss = 0.02
        profit_target = 0.04
        capital = 100000
        lot_size = 1
        max_daily_loss = 0.02

        position = 0
        entry_price = None
        entry_index = None
        last_exit_index = -cooldown
        trades_taken = {}
        trade_log = []
        equity = capital
        daily_pnl = {}
        quantity = 0

        for i in range(1, len(df)):
            row = df.iloc[i]
            day = row['Date'].date()
            if day not in trades_taken:
                trades_taken[day] = 0
                daily_pnl[day] = 0
            if not (pd.to_datetime('09:15:00').time() <= row['Date'].time() <= pd.to_datetime('15:30:00').time()):
                continue
            if position == 0 and (i - last_exit_index) >= cooldown and trades_taken[day] < max_trades_day:
                if daily_pnl[day] <= -max_daily_loss * capital:
                    continue
                price = row['Close']
                max_lots = int(capital // (price * lot_size))
                quantity = max_lots * lot_size
                if quantity < lot_size:
                    continue
                if row['longCond']:
                    position = 1
                    entry_price = row['Close']
                    entry_index = i
                    trade_log.append({'Entry Time': row['Date'], 'Exit Time': None,
                                     'Position': 'Long', 'Entry Price': entry_price,
                                     'Exit Price': None, 'PnL': None,
                                     'Absolute PnL (₹)': None, 'Quantity': quantity, 'Reason': 'Long Entry'})
                elif row['shortCond']:
                    position = -1
                    entry_price = row['Close']
                    entry_index = i
                    trade_log.append({'Entry Time': row['Date'], 'Exit Time': None,
                                     'Position': 'Short', 'Entry Price': entry_price,
                                     'Exit Price': None, 'PnL': None,
                                     'Absolute PnL (₹)': None, 'Quantity': quantity, 'Reason': 'Short Entry'})
                continue

            # Trade exit/stop logic
            if position != 0 and entry_price is not None:
                # Calculate open trade PnL
                direction = 1 if position == 1 else -1
                trade_pnl = direction * (row['Close'] - entry_price)

                # Check stop loss / profit target / EOD
                trigger_exit = False
                if direction == 1:  # Long
                    if (row['Low'] <= entry_price * (1 - stop_loss)) or (row['High'] >= entry_price * (1 + profit_target)):
                        trigger_exit = True
                else:  # Short
                    if (row['High'] >= entry_price * (1 + stop_loss)) or (row['Low'] <= entry_price * (1 - profit_target)):
                        trigger_exit = True
                if row['Date'].time() == pd.to_datetime('15:29:00').time():
                    trigger_exit = True

                if trigger_exit:
                    exit_price = row['Close'] - slippage * direction
                    abs_pnl = (exit_price - entry_price) * quantity * direction - commission * entry_price * quantity
                    trade_log[-1].update({'Exit Time': row['Date'],
                                         'Exit Price': exit_price,
                                         'PnL': abs_pnl / capital * 100,
                                         'Absolute PnL (₹)': abs_pnl,
                                         'bars_in_trade': i - entry_index})
                    equity += abs_pnl
                    daily_pnl[day] += abs_pnl
                    trades_taken[day] += 1
                    position = 0
                    entry_price = None
                    entry_index = None
                    last_exit_index = i

        # Aggregate results
        pnl_arr = [t['PnL'] for t in trade_log if t['PnL'] is not None]
        total_return = (equity / capital - 1) if equity != capital else 0
        win_rate = np.mean(np.array(pnl_arr) > 0) if pnl_arr else 0
        sharpe = (np.mean(pnl_arr) / np.std(pnl_arr) * np.sqrt(252 * 390)) if len(pnl_arr) > 1 and np.std(pnl_arr) != 0 else 0
        return params, total_return, win_rate, sharpe, trade_log

    except Exception as e:
        print(f"Error in backtest_strategy for params {params}: {e}")
        return params, 0, 0, 0, []

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    locale.setlocale(locale.LC_ALL, '')
    matplotlib.use('TkAgg')

    print("Running parameter sweep with multiprocessing...")
    param_grid = [(fast, slow, sig) for fast in [12] for slow in [26] for sig in [9]]
    with multiprocessing.Pool() as pool:
        results = pool.map(backtest_strategy, param_grid)

    print("\nMACD Parameter Test Results:\n")
    valid_results = [r for r in results if isinstance(r, tuple) and len(r) == 5 and isinstance(r[4], list)]
    print(f"Valid results: {len(valid_results)} of {len(results)}")
    for params, total_return, win_rate, sharpe, _ in valid_results:
        print(f"Fast={params[0]} Slow={params[1]} Sig={params[2]} | Return={total_return*100:.2f}% | WinRate={win_rate*100:.2f}% | Sharpe={sharpe:.2f}")

    sweep_results = [
        [f"{params[0]}/{params[1]}/{params[2]}", f"{total_return*100:.2f}%", f"{win_rate*100:.2f}%", f"{sharpe:.2f}"]
        for params, total_return, win_rate, sharpe, _ in valid_results
    ]

    if sweep_results:
        print("\nMACD Parameter Sweep Results:\n")
        print(tabulate(
            sweep_results,
            headers=["Fast/Slow/Sig", "Return", "WinRate", "Sharpe"],
            tablefmt="psql"
        ))

        # Run detailed backtest for default MACD(12, 26, 9)
        default_params = (12, 26, 9)
        print(f"\nShowing detailed results for default MACD(12, 26, 9):\n")
        default_result = next((r for r in valid_results if r[0] == default_params), None)
        if default_result:
            params, total_return, win_rate, sharpe, trade_log = default_result
        else:
            params, total_return, win_rate, sharpe, trade_log = backtest_strategy(default_params)

        trades_df = pd.DataFrame(trade_log)
        if not trades_df.empty:
            trades_df['Entry Time'] = pd.to_datetime(trades_df['Entry Time'])
            trades_df['Exit Time'] = pd.to_datetime(trades_df['Exit Time'])
            trades_df['bars_in_trade'] = (trades_df['Exit Time'] - trades_df['Entry Time']).dt.total_seconds() / 60.0

            total_trades = len(trades_df)
            winning_trades = trades_df[trades_df['PnL'] > 0]
            losing_trades = trades_df[trades_df['PnL'] <= 0]
            num_win = len(winning_trades)
            num_loss = len(losing_trades)
            percent_profitable = 100 * num_win / total_trades if total_trades > 0 else 0
            avg_pnl = trades_df['PnL'].mean() if not trades_df.empty else 0
            avg_win = winning_trades['PnL'].mean() if not winning_trades.empty else 0
            avg_loss = losing_trades['PnL'].mean() if not losing_trades.empty else 0
            ratio_win_loss = abs(avg_win / avg_loss) if avg_loss != 0 else np.nan
            largest_win = winning_trades['PnL'].max() if not winning_trades.empty else 0
            largest_loss = losing_trades['PnL'].min() if not losing_trades.empty else 0
            sharpe = (trades_df['PnL'].mean() / trades_df['PnL'].std() * np.sqrt(252 * 390)) if trades_df['PnL'].std() != 0 else 0
            cumulative_pnl = trades_df['PnL'].sum() if not trades_df.empty else 0
            absolute_pnl = trades_df['Absolute PnL (₹)'].sum() if not trades_df.empty else 0

            equity = [100000] + [100000 + trades_df['Absolute PnL (₹)'].cumsum()[:i+1].iloc[-1] for i in range(len(trades_df))]
            peak = np.maximum.accumulate(equity)
            drawdown = (np.array(equity) - peak) / peak
            max_dd = drawdown.min() * 100 if len(drawdown) else 0
            runup = (np.array(equity) - np.minimum.accumulate(equity)) / np.minimum.accumulate(equity)
            max_runup = runup.max() * 100 if len(runup) else 0

            avg_bars = trades_df['bars_in_trade'].mean() if not trades_df.empty else 0
            avg_bars_win = winning_trades['bars_in_trade'].mean() if not winning_trades.empty else 0
            avg_bars_loss = losing_trades['bars_in_trade'].mean() if not losing_trades.empty else 0
            consecutive_losses = max(
                (trades_df['PnL'] <= 0).astype(int).groupby((trades_df['PnL'] > 0).cumsum()).sum())
            profit_factor = abs(winning_trades['PnL'].sum() / losing_trades['PnL'].sum()) if not losing_trades.empty and losing_trades['PnL'].sum() != 0 else np.nan

            print(tabulate(trades_df[['Entry Time', 'Exit Time', 'Position', 'Entry Price', 'Exit Price', 'PnL', 'Absolute PnL (₹)', 'Quantity', 'bars_in_trade']],
                           headers='keys', tablefmt='psql', showindex=False))

            summary = [
                ["Total Trades", total_trades],
                ["Winning Trades", num_win],
                ["Losing Trades", num_loss],
                ["Percent Profitable", f"{percent_profitable:.2f}%"],
                ["Avg PnL/trade", f"{avg_pnl:.4f}"],
                ["Avg Winning Trade", f"{avg_win:.4f}"],
                ["Avg Losing Trade", f"{avg_loss:.4f}"],
                ["Ratio Avg Win/Loss", f"{ratio_win_loss:.2f}"],
                ["Largest Winning Trade", f"{largest_win:.4f}"],
                ["Largest Losing Trade", f"{largest_loss:.4f}"],
                ["Cumulative PnL (%)", f"{cumulative_pnl:.4f}"],
                ["Absolute PnL (₹)", f"{absolute_pnl:.2f}"],
                ["Sharpe Ratio", f"{sharpe:.3f}"],
                ["Max Drawdown (%)", f"{max_dd:.2f}%"],
                ["Max Runup (%)", f"{max_runup:.2f}%"],
                ["Avg # Bars in Trade", f"{avg_bars:.0f}"],
                ["Avg # Bars (Winning)", f"{avg_bars_win:.0f}"],
                ["Avg # Bars (Losing)", f"{avg_bars_loss:.0f}"],
                ["Max Consecutive Losses", consecutive_losses],
                ["Profit Factor", f"{profit_factor:.2f}"],
                ["Total Quantity", trades_df['Quantity'].sum()]
            ]
            print(tabulate(summary, headers=["Metric", "Value"], tablefmt="psql"))

            plt.figure(figsize=(10, 4))
            plt.plot(equity, label='Equity Curve', color='blue')
            plt.title(f"Equity Curve (MACD 12/26/9)")
            plt.xlabel('Trade Number')
            plt.ylabel('Equity (₹)')
            plt.grid(True)
            plt.legend()
            plt.tight_layout()               
            output_dir = os.path.dirname('pnl_curve.png')
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            plt.savefig('pnl_curve.png')

            plt.figure(figsize=(10, 4))
            plt.bar(range(len(drawdown)), drawdown * 100, color='red', label='Drawdown')
            plt.xlabel('Trade Number')
            plt.ylabel('Drawdown (%)')
            plt.title(f'Drawdown (MACD 12/26/9)')
            plt.legend()
            plt.tight_layout()
            plt.savefig('drawdown_curve.png')

            trades_df.to_csv("trade_log.csv", index=False)
            trades_df.to_html("trade_log.html", index=False)
            print("\nTrade log saved: trade_log.csv, trade_log.html")
            print("Plots saved: pnl_curve.png, drawdown_curve.png")
            plt.show()
            plt.close('all')
        else:
            print("Error: No trades generated for MACD(12, 26, 9).")
    else:
        print("Error: No valid results. Check data or backtest function.")
        exit(1)
