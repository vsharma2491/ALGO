import argparse
import logging
import yaml
import pandas as pd
import importlib
from dotenv import load_dotenv
from data_downloader import download_nifty_data
from backtest_engine import Backtester
from event_driven_backtester import BacktraderEngine
from reporting import generate_report

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Main function to run the backtesting system.
    """
    parser = argparse.ArgumentParser(description="A fully automated Nifty options backtesting system.")
    parser.add_argument("--download-data", action="store_true", help="Downloads fresh historical data.")
    parser.add_argument("--start-date", type=str, help="The start date for the backtest (YYYY-MM-DD).")
    parser.add_argument("--end-date", type=str, help="The end date for the backtest (YYYY-MM-DD).")
    parser.add_argument("--strategy", type=str, default="ma_crossover", help="The strategy file to test.")
    parser.add_argument("--sample-data", action="store_true", help="Run the backtest with sample data.")
    parser.add_argument("--backtester", type=str, default="vectorized", help="The backtesting engine to use (vectorized or event_driven).")
    parser.add_argument("--optimize", action="store_true", help="Run a parameter sweep for the strategy.")

    args = parser.parse_args()

    # Load config
    with open("config/config.yaml", 'r') as f:
        config = yaml.safe_load(f)

    start_date = args.start_date if args.start_date else config['start_date']
    end_date = args.end_date if args.end_date else config['end_date']

    if args.download_data:
        logging.info("Downloading historical data...")
        download_nifty_data(start_date, end_date)
        logging.info("Data download complete.")

    if not args.download_data:
        # Determine which data file to use
        if args.sample_data:
            data_file = 'data/sample_nifty_data.csv'
        else:
            data_file = 'data/nifty_1min_data.csv'

        logging.info(f"Running backtest with {args.strategy} strategy on {data_file}...")

        try:
            data = pd.read_csv(data_file)
            data['datetime'] = pd.to_datetime(data['datetime'])
            data.set_index('datetime', inplace=True)
        except FileNotFoundError:
            logging.error(f"Data file not found: {data_file}. Please run with --download-data or use --sample-data.")
            return

        try:
            strategy_module = importlib.import_module(f"strategies.{args.strategy}")
            if args.strategy == "ma_crossover":
                strategy_class = getattr(strategy_module, "MACrossover")
            elif args.strategy == "ema_cross_atr_stops":
                strategy_class = getattr(strategy_module, "EmaCrossAtrStops")
            else:
                strategy_class = getattr(strategy_module, args.strategy.capitalize().replace('_', ''))
        except (ImportError, AttributeError):
            logging.error(f"Could not find strategy '{args.strategy}'. Please make sure the file 'strategies/{args.strategy}.py' and class '{args.strategy.capitalize().replace('_', '')}' exist.")
            return

        if args.backtester == "vectorized":
            strategy = strategy_class(data)
            backtester = Backtester(strategy, data, config['initial_capital'], config)
            results, trades, equity_curve = backtester.run()
            generate_report(results, trades, equity_curve)

        elif args.backtester == "event_driven":
            backtester = BacktraderEngine(strategy_class, data, config['initial_capital'])
            cerebro = backtester.run()
            cerebro.plot()
        else:
            logging.error(f"Backtester '{args.backtester}' not supported.")
            return

        logging.info("Backtest complete.")

if __name__ == "__main__":
    main()
