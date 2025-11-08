import os
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Optional

from brokers.flattrade import FlattradeBroker

def download_nifty_data(start_date: str, end_date: str) -> None:
    """
    Downloads 1-minute historical data for Nifty and saves it to a CSV file.

    This function connects to the Flattrade API, downloads historical data for the
    Nifty 50 index, and stores it in a CSV file. It includes an auto-update
    feature that checks for existing data and only downloads new dates.

    Args:
        start_date (str): The start date for the data download in "YYYY-MM-DD" format.
        end_date (str): The end date for the data download in "YYYY-MM-DD" format.
    """
    broker = FlattradeBroker()
    if not broker.authenticated:
        print("Authentication failed. Please check your credentials.")
        return


    symbol = "NIFTY 50" 

    symbol = "NIFTY 50"
ef30c4da16fe3884e4c2b68e5cde3930584545b3
    exchange = "NSE"
    file_path = f"data/nifty_1min_data.csv"

    if os.path.exists(file_path):
        try:
            existing_df = pd.read_csv(file_path)
            existing_df['datetime'] = pd.to_datetime(existing_df['datetime'])
            latest_date = existing_df['datetime'].max().strftime('%Y-%m-%d')
HEAD
            
=======

>>>>>>> ef30c4da16fe3884e4c2b68e5cde3930584545b3
            if latest_date > start_date:
                start_date = (pd.to_datetime(latest_date) + timedelta(days=1)).strftime('%Y-%m-%d')
                print(f"Resuming download from {start_date}")
        except (FileNotFoundError, pd.errors.EmptyDataError):
            print(f"Could not read existing data from {file_path}. Starting fresh download.")

    print(f"Downloading data from {start_date} to {end_date}...")
 HEAD
    
=======

ef30c4da16fe3884e4c2b68e5cde3930584545b3
    # In a real implementation, you would add retry logic and handle API rate limits here.
    try:
        data = broker.get_historical_data(symbol, exchange, start_date, end_date, interval='1')
    except Exception as e:
        print(f"An error occurred during data download: {e}")
        return

    if data:
        df = pd.DataFrame(data)
        df.rename(columns={'time': 'datetime', 'into': 'open', 'inth': 'high', 'intl': 'low', 'intc': 'close', 'intv': 'volume'}, inplace=True)
HEAD
        
=======

 ef30c4da16fe3884e4c2b68e5cde3930584545b3
        # Data validation
        df.dropna(inplace=True)
        df.drop_duplicates(inplace=True)
        df['datetime'] = pd.to_datetime(df['datetime'], unit='s')
HEAD
        
=======

 ef30c4da16fe3884e4c2b68e5cde3930584545b3
        # Save data
        if os.path.exists(file_path):
            df.to_csv(file_path, mode='a', header=False, index=False)
        else:
            df.to_csv(file_path, index=False)
HEAD
        
=======

f30c4da16fe3884e4c2b68e5cde3930584545b3
        print(f"Data downloaded and saved to {file_path}")
    else:
        print("Failed to download data.")

if __name__ == "__main__":
    download_nifty_data("2023-01-01", "2023-12-31")
