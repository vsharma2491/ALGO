# ==============================================================================
# SECTION 1: LOGIC PARAMETERS
# ==============================================================================
# This section contains all the configurable parameters for the backtesting setup.
# Modify these values to change the strategy's behavior, risk management, and
# optimization settings without altering the core logic in other sections.

# ------------------------------------------------------------------------------
# Strategy & Indicator Parameters
# ------------------------------------------------------------------------------
# These parameters define the core logic of the trading strategy.
STRATEGY_PARAMETERS = {
    # --- Crossover Logic Parameters ---
    # These define the periods for the moving averages used in the crossover strategy.
    # For a MACD-like strategy, these would be the fast, slow, and signal periods.
    'fast_period': 12,          # Period for the fast moving average.
    'slow_period': 26,          # Period for the slow moving average.
    'signal_period': 9,         # Period for the signal line (e.g., for MACD).
    'ma_type': 'EMA',           # Type of Moving Average to use: 'SMA' or 'EMA'.

    # --- Trend Filter ---
    # A long-term moving average can be used to filter trades.
    # e.g., only take long trades when the price is above this MA.
    'trend_filter_period': 200, # Period for the long-term trend-filtering MA.
    'trend_filter_enabled': True, # Set to False to disable the trend filter.
}

# ------------------------------------------------------------------------------
# Risk Management Parameters
# ------------------------------------------------------------------------------
# These parameters control the risk aspects of the strategy.
RISK_PARAMETERS = {
    # --- Stop Loss ---
    'enable_stop_loss': True,   # Set to True to use a fixed stop loss.
    'stop_loss_pct': 0.02,      # Stop loss percentage (e.g., 0.02 for 2%).

    # --- Take Profit ---
    'enable_take_profit': True, # Set to True to use a fixed take profit.
    'take_profit_pct': 0.04,    # Take profit percentage (e.g., 0.04 for 4%).

    # --- Trailing Stop ---
    'enable_trailing_stop': False, # Set to True to use a trailing stop loss.
    'trailing_stop_pct': 0.015,  # Trailing stop percentage (e.g., 0.015 for 1.5%).
}

# ------------------------------------------------------------------------------
# Trade Execution & Sizing Parameters
# ------------------------------------------------------------------------------
# These parameters define the context of the backtest, such as capital and costs.
TRADE_PARAMETERS = {
    'initial_capital': 100000.0,    # The starting capital for the backtest.
    'position_size_pct_capital': 0.10, # % of capital to allocate per trade.
    'commission_pct': 0.0001,       # Commission fee per trade (e.g., 0.01% = 0.0001).
    'slippage_pct': 0.0005,         # Estimated slippage per trade (e.g., 0.05% = 0.0005).
}

# ------------------------------------------------------------------------------
# Backtest & Optimization Parameters
# ------------------------------------------------------------------------------
# These parameters configure the backtesting engine and the optimization process.
BACKTEST_PARAMETERS = {
    'data_filepath': r"c:/Users/vivek/Desktop/algo/NIFTY DATA/NIFTY50-INDEX.csv",
    'start_date': '2024-01-01',     # The start date for the backtest.
    'end_date': '2024-12-31',       # The end date for the backtest.
    'use_multiprocessing': True,    # Set to True to speed up optimization.

    # --- Parameter Optimization Grid ---
    # Define the parameter combinations to test during optimization.
    # The backtester will run a separate test for each combination.
    # Format: 'parameter_name': [list_of_values_to_test]
    'optimization_grid': {
        'fast_period': [10, 12, 15],
        'slow_period': [25, 26, 30],
        'signal_period': [9], # Keep signal constant for this example
    },

    # --- Optimization Ranking Metric ---
    # The metric used to rank the results of the parameter optimization.
    # Options: 'Sharpe Ratio', 'Total Return', 'Max Drawdown', 'Profit Factor'
    'optimization_metric': 'Sharpe Ratio'
}

# This marks the end of Section 1.

# ==============================================================================
# SECTION 2: STRATEGY CLASS
# ==============================================================================
# This section defines the strategy logic. It is designed to be modular.
# To create a new strategy, you can create a new class that follows the same
# structure as CrossoverStrategy and then instantiate it in the backtesting engine.

import pandas as pd
import numpy as np

class CrossoverStrategy:
    """
    A strategy class that implements a moving average crossover system.
    It generates trading signals based on the crossover of two moving averages
    and can optionally use a third, longer-term MA as a trend filter.
    """
    def __init__(self, params):
        """
        Initializes the strategy with a given set of parameters.
        
        Args:
            params (dict): A dictionary containing all necessary strategy parameters,
                           such as 'fast_period', 'slow_period', 'ma_type', etc.
        """
        self.params = params

    def _calculate_ma(self, series, period, ma_type):
        """Calculates a moving average of a given type."""
        if ma_type.upper() == 'SMA':
            return series.rolling(window=period).mean()
        elif ma_type.upper() == 'EMA':
            return series.ewm(span=period, adjust=False).mean()
        else:
            raise ValueError("ma_type must be either 'SMA' or 'EMA'")

    def generate_signals(self, data):
        """
        Calculates indicators and generates trading signals.
        
        Args:
            data (pd.DataFrame): The input OHLCV data, must contain 'Close' prices.
            
        Returns:
            pd.DataFrame: The input DataFrame with added columns for indicators and signals.
        """
        try:
            df = data.copy()
            
            # --- Calculate Indicators ---
            # Fast and slow moving averages for the crossover signal
            df['ma_fast'] = self._calculate_ma(df['Close'], self.params['fast_period'], self.params['ma_type'])
            df['ma_slow'] = self._calculate_ma(df['Close'], self.params['slow_period'], self.params['ma_type'])
            
            # Optional trend-filtering moving average
            if self.params.get('trend_filter_enabled', False):
                df['ma_trend'] = self._calculate_ma(df['Close'], self.params['trend_filter_period'], self.params['ma_type'])
            
            # --- Generate Crossover Conditions ---
            # A crossover occurs when the relationship between fast and slow MAs changes
            ma_fast_above_slow = df['ma_fast'] > df['ma_slow']
            df['crossover_up'] = (ma_fast_above_slow) & (~ma_fast_above_slow.shift(1).fillna(False))
            df['crossover_down'] = (~ma_fast_above_slow) & (ma_fast_above_slow.shift(1).fillna(False))
            
            # --- Apply Trend Filter ---
            # If the trend filter is enabled, we define bullish and bearish conditions
            if self.params.get('trend_filter_enabled', False):
                bullish_trend = df['Close'] > df['ma_trend']
                bearish_trend = df['Close'] < df['ma_trend']
            else:
                # If disabled, the conditions are always true (no filtering)
                bullish_trend = True
                bearish_trend = True

            # --- Define Final Entry and Exit Signals ---
            # An entry signal is a crossover that aligns with the trend filter
            df['long_entry_signal'] = df['crossover_up'] & bullish_trend
            df['short_entry_signal'] = df['crossover_down'] & bearish_trend
            
            # An exit signal is the opposite crossover
            df['long_exit_signal'] = df['crossover_down']
            df['short_exit_signal'] = df['crossover_up']
            
            return df

        except Exception as e:
            print(f"Error generating signals: {e}")
            return pd.DataFrame() # Return an empty DataFrame on error

# This marks the end of Section 2.

# ==============================================================================
# SECTION 3: COMPLETE BACKTESTING ENGINE
# ==============================================================================
# This section contains the core backtesting engine. It handles data loading,
# trade simulation, and performance calculation. It uses multiprocessing to
# run tests for different parameter combinations in parallel.

import os
import itertools
from multiprocessing import Pool

class BacktestEngine:
    """
    The core backtesting engine. It orchestrates the entire backtesting process,
    from data loading and preparation to running the simulation and gathering results.
    """
    def __init__(self, params_config):
        """
        Initializes the backtesting engine with all parameter configurations.
        
        Args:
            params_config (dict): A dictionary containing all parameter sections
                                  (strategy, risk, trade, and backtest).
        """
        self.params_config = params_config
        self.data = self._load_and_prepare_data()

    def _load_and_prepare_data(self):
        """
        Loads and prepares the data from the specified file path.
        - Loads CSV
        - Parses dates and sets index
        - Filters by date range
        - Renames columns to a standard format (TitleCase)
        """
        try:
            path = self.params_config['backtest']['data_filepath']
            if not os.path.exists(path):
                print(f"Error: Data file not found at {path}")
                return pd.DataFrame()

            df = pd.read_csv(path)
            # Standardize column names to avoid case sensitivity issues
            df.columns = [col.title() for col in df.columns]
            
            # Ensure 'Date' column is parsed correctly
            if 'Date' not in df.columns:
                raise ValueError("Dataframe must contain a 'Date' column.")
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True) # Sort by date to ensure index is monotonic
            
            # Filter data based on the specified date range
            start_date = self.params_config['backtest']['start_date']
            end_date = self.params_config['backtest']['end_date']
            df = df[start_date:end_date]
            
            if df.empty:
                print("Error: No data available for the specified date range.")
            
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()
            
    def _run_backtest_for_params(self, params_tuple):
        """
        This is the core simulation function that runs for a single set of parameters.
        It is designed to be called by the multiprocessing Pool.
        """
        # 1. Unpack parameters
        strategy_params, risk_params, trade_params = params_tuple
        
        # 2. Instantiate the strategy and generate signals
        strategy = CrossoverStrategy(strategy_params)
        signals_df = strategy.generate_signals(self.data)
        if signals_df.empty:
            return (strategy_params, []) # Return empty results if signal generation fails
            
        # 3. Initialize backtest state variables
        equity = trade_params['initial_capital']
        position = 0  # 0: flat, 1: long, -1: short
        entry_price = 0.0
        entry_time = None
        trade_log = []
        
        # 4. Loop through each bar of data
        for i in range(len(signals_df)):
            row = signals_df.iloc[i]
            
            # --- Handle Exits First ---
            if position != 0:
                exit_reason = None
                # Check for stop loss, take profit, or signal-based exit
                if position == 1: # Long position
                    if risk_params['enable_stop_loss'] and row['Low'] <= entry_price * (1 - risk_params['stop_loss_pct']):
                        exit_price = row['Low'] # Exit at the low of the bar
                        exit_reason = 'Stop Loss'
                    elif risk_params['enable_take_profit'] and row['High'] >= entry_price * (1 + risk_params['take_profit_pct']):
                        exit_price = row['High'] # Exit at the high of the bar
                        exit_reason = 'Take Profit'
                    elif row['long_exit_signal']:
                        exit_price = row['Close']
                        exit_reason = 'Exit Signal'
                
                elif position == -1: # Short position
                    if risk_params['enable_stop_loss'] and row['High'] >= entry_price * (1 + risk_params['stop_loss_pct']):
                        exit_price = row['High'] # Exit at the high of the bar
                        exit_reason = 'Stop Loss'
                    elif risk_params['enable_take_profit'] and row['Low'] <= entry_price * (1 - risk_params['take_profit_pct']):
                        exit_price = row['Low'] # Exit at the low of the bar
                        exit_reason = 'Take Profit'
                    elif row['short_exit_signal']:
                        exit_price = row['Close']
                        exit_reason = 'Exit Signal'

                if exit_reason:
                    pnl = (exit_price - entry_price) / entry_price if position == 1 else (entry_price - exit_price) / entry_price
                    trade_log.append({
                        'Entry Time': entry_time, 'Exit Time': row.name,
                        'Position': 'Long' if position == 1 else 'Short',
                        'Entry Price': entry_price, 'Exit Price': exit_price,
                        'PnL': pnl, 'Exit Reason': exit_reason
                    })
                    position = 0
                    entry_time = None

            # --- Handle Entries ---
            if position == 0:
                if row['long_entry_signal']:
                    position = 1
                    entry_price = row['Close']
                    entry_time = row.name
                elif row['short_entry_signal']:
                    position = -1
                    entry_price = row['Close']
                    entry_time = row.name
                    
        return (strategy_params, trade_log)

    def run(self):
        """
        The main public method to start the backtesting process.
        It generates parameter combinations and uses multiprocessing to run the simulations.
        """
        if self.data.empty:
            print("Cannot run backtest; data is empty.")
            return []

        # Generate all combinations of parameters from the optimization grid
        param_grid = self.params_config['backtest']['optimization_grid']
        keys, values = zip(*param_grid.items())
        param_combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        # Combine with static parameters
        full_param_sets = []
        for combo in param_combinations:
            strat_params = self.params_config['strategy'].copy()
            strat_params.update(combo)
            full_param_sets.append((strat_params, self.params_config['risk'], self.params_config['trade']))
            
        # Run the backtests
        if self.params_config['backtest']['use_multiprocessing']:
            print(f"Running {len(full_param_sets)} optimizations using multiprocessing...")
            with Pool() as pool:
                results = pool.map(self._run_backtest_for_params, full_param_sets)
        else:
            print(f"Running {len(full_param_sets)} optimizations sequentially...")
            results = [self._run_backtest_for_params(p) for p in full_param_sets]
            
        return results

# This marks the end of Section 3.

# ==============================================================================
# SECTION 4: RESULTS FORMATTING & PRINTING
# ==============================================================================
# This section is responsible for taking the raw results from the backtest,
# calculating a comprehensive set of performance metrics, and printing them
# in a clean, professional, and readable format.

from tabulate import tabulate

class ResultsFormatter:
    """
    Handles the calculation of metrics and the display of backtesting results.
    """
    def __init__(self, results, initial_capital, ranking_metric):
        self.results = results
        self.initial_capital = initial_capital
        self.ranking_metric = ranking_metric
        self.processed_results = self._process_results()

    def _calculate_metrics(self, trade_log_df):
        """Calculates a dictionary of performance metrics from a trade log."""
        if trade_log_df.empty:
            return {}

        # --- Performance Summary Metrics ---
        total_trades = len(trade_log_df)
        wins = trade_log_df[trade_log_df['PnL'] > 0]
        losses = trade_log_df[trade_log_df['PnL'] <= 0]
        win_rate = len(wins) / total_trades if total_trades > 0 else 0
        
        # --- Strategy Metrics ---
        pnl_returns = trade_log_df['PnL']
        sharpe_ratio = (pnl_returns.mean() / pnl_returns.std()) * np.sqrt(252) if pnl_returns.std() != 0 else 0
        total_return = pnl_returns.sum()
        
        # --- Drawdown ---
        cumulative_pnl = (pnl_returns * self.initial_capital).cumsum()
        equity_curve = self.initial_capital + cumulative_pnl
        peak = equity_curve.expanding(min_periods=1).max()
        drawdown = (equity_curve - peak) / peak
        max_drawdown = drawdown.min()

        return {
            'Total Trades': total_trades,
            'Win Rate': win_rate,
            'Total Return': total_return,
            'Sharpe Ratio': sharpe_ratio,
            'Max Drawdown': max_drawdown,
            'Profit Factor': abs(wins['PnL'].sum() / losses['PnL'].sum()) if losses['PnL'].sum() != 0 else np.inf,
        }

    def _process_results(self):
        """Processes raw results from the engine into a list of metric dicts."""
        processed = []
        for params, trade_log in self.results:
            if not trade_log:
                metrics = {'Total Trades': 0}
            else:
                trade_log_df = pd.DataFrame(trade_log)
                metrics = self._calculate_metrics(trade_log_df)
            
            processed.append({'params': params, 'metrics': metrics, 'trade_log': trade_log})
        return processed

    def print_all(self):
        """Prints all result tables: summary, detailed logs, and optimization."""
        if not self.processed_results:
            print("No results to display.")
            return
            
        # --- Print Optimization Results First ---
        self.print_optimization_results()

        # --- Print Detailed Report for the Best Parameters ---
        best_result = self.get_best_result()
        print("\n" + "="*80)
        print("DETAILED REPORT FOR BEST PARAMETERS")
        print(f"Parameters: {best_result['params']}")
        print("="*80)
        
        self.print_trade_by_trade_table(best_result['trade_log'])
        self.print_performance_summary(best_result['metrics'])

    def print_optimization_results(self):
        """Prints a table summarizing the performance of each parameter set."""
        headers = ["Parameters", "Total Trades", "Win Rate", "Total Return", "Sharpe Ratio", "Max Drawdown"]
        rows = []
        for res in self.processed_results:
            p = res['params']
            m = res['metrics']
            rows.append([
                f"fast={p['fast_period']}, slow={p['slow_period']}",
                m.get('Total Trades', 0),
                f"{m.get('Win Rate', 0):.2%}",
                f"{m.get('Total Return', 0):.2%}",
                f"{m.get('Sharpe Ratio', 0):.2f}",
                f"{m.get('Max Drawdown', 0):.2%}"
            ])
        
        print("\n" + "="*80)
        print("PARAMETER OPTIMIZATION RESULTS")
        print("="*80)
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        
    def print_trade_by_trade_table(self, trade_log):
        """Prints the detailed trade-by-trade log."""
        if not trade_log:
            print("\nNo trades were executed.")
            return
        
        df = pd.DataFrame(trade_log)
        df['PnL %'] = df['PnL'].apply(lambda x: f"{x:.2%}")
        df['Duration'] = (df['Exit Time'] - df['Entry Time'])
        df.index.name = "Trade No."
        
        print("\n--- Trade-by-Trade Detailed Table ---")
        print(tabulate(df[['Entry Time', 'Exit Time', 'Position', 'Entry Price', 'Exit Price', 'PnL %', 'Duration']],
                       headers='keys', tablefmt='psql', showindex=True))

    def print_performance_summary(self, metrics):
        """Prints the summary and strategy metrics tables."""
        if not metrics or metrics['Total Trades'] == 0:
            return

        summary_data = [
            ("Total Trades", metrics.get('Total Trades')),
            ("Win Rate", f"{metrics.get('Win Rate', 0):.2%}"),
            ("Profit Factor", f"{metrics.get('Profit Factor', 0):.2f}"),
            ("Total Return", f"{metrics.get('Total Return', 0):.2%}"),
        ]
        
        metrics_data = [
            ("Sharpe Ratio", f"{metrics.get('Sharpe Ratio', 0):.2f}"),
            ("Max Drawdown", f"{metrics.get('Max Drawdown', 0):.2%}"),
        ]
        
        print("\n--- Performance Summary ---")
        print(tabulate(summary_data, tablefmt="grid"))
        
        print("\n--- Strategy Metrics ---")
        print(tabulate(metrics_data, tablefmt="grid"))

    def get_best_result(self):
        """Returns the result set with the best performance based on the ranking metric."""
        return max(self.processed_results, key=lambda x: x['metrics'].get(self.ranking_metric, -np.inf))

# ==============================================================================
# MAIN EXECUTION BLOCK
# ==============================================================================
if __name__ == "__main__":
    # 1. Combine all parameter dictionaries into one config object
    config = {
        'strategy': STRATEGY_PARAMETERS,
        'risk': RISK_PARAMETERS,
        'trade': TRADE_PARAMETERS,
        'backtest': BACKTEST_PARAMETERS
    }

    # 2. Instantiate and run the backtesting engine
    engine = BacktestEngine(config)
    raw_results = engine.run()

    # 3. Format and print the results
    if raw_results:
        formatter = ResultsFormatter(
            results=raw_results,
            initial_capital=config['trade']['initial_capital'],
            ranking_metric=config['backtest']['optimization_metric']
        )
        formatter.print_all()
    else:
        print("Backtest finished with no results to display.")