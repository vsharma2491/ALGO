import argparse
import logging
import yaml
import pandas as pd
from data_downloader import download_nifty_data
from backtest_engine import Backtester
from reporting import generate_report
from strategies.ma_crossover import MACrossover

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
        logging.info(f"Running backtest with {args.strategy} strategy...")

        if args.strategy == "ma_crossover":
            try:
                data = pd.read_csv('data/nifty_1min_data.csv')
                data['datetime'] = pd.to_datetime(data['datetime'])
                data.set_index('datetime', inplace=True)
            except FileNotFoundError:
                logging.error("Data file not found. Please run with --download-data first.")
                return

            strategy = MACrossover(data)
            backtester = Backtester(strategy, data, config['initial_capital'], config)
            results, trades, equity_curve = backtester.run()

            generate_report(results, trades, equity_curve)

            logging.info("Backtest complete.")

if __name__ == "__main__":
    main()
