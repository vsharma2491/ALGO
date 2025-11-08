import pandas as pd
from flattrade import Flattrade
import os

# ==============================================================================
# SECTION 1: CONFIGURATION
# ==============================================================================
# This section contains all the configurable parameters for fetching data.
# --- API Credentials ---
# Replace with your actual API key, secret, and user ID.
API_KEY = "b2c2ab98ac934e35bb4aeee2e7b91848"
API_SECRET = "YOUR_API_SECRET"  # <-- IMPORTANT: REPLACE WITH YOUR ACTUAL API SECRET
USER_ID = "stoxxoO"

# --- Data Fetching Parameters ---
# The symbol for the instrument you want to fetch data for.
# Example: "RELIANCE-EQ" for Reliance Industries on NSE.
SYMBOL = "NIFTY 50"  # Flattrade might use "NIFTY 50" for the index
EXCHANGE = "NSE" # Example: "NSE" for National Stock Exchange

# The time interval for the data.
# Options can include '1m', '5m', '10m', '15m', '30m', '60m', '1d'.
INTERVAL = "1m"

# The start and end dates for the historical data.
# Format: 'YYYY-MM-DD'
START_DATE = "2024-01-01"
END_DATE = "2024-01-31"

# The name of the output file where the data will be saved.
OUTPUT_FILENAME = "historical_data.csv"


# ==============================================================================
# SECTION 2: DATA FETCHING AND PROCESSING
# ==============================================================================

def fetch_historical_data():
    """
    Connects to the Flattrade API, fetches historical data, and saves it to a CSV file.
    """
    print("--- Starting Data Fetching Process ---")

    # --- Step 1: Connect to Flattrade API ---
    # It's good practice to check if the API secret has been updated.
    if API_SECRET == "YOUR_API_SECRET":
        print("Error: Please replace 'YOUR_API_SECRET' with your actual API secret in the script.")
        return

    try:
        # Create a Flattrade API client instance
        flattrade = Flattrade(api_key=API_KEY, api_secret=API_SECRET)
        print("Successfully created Flattrade API client.")
        
        # Note: The Flattrade Python client may require a login process.
        # This script assumes you have a valid session or the client handles it.
        # You might need to uncomment the following line if a login is required:
        # flattrade.login(API_KEY, USER_ID)
        # print("Login successful.")

    except Exception as e:
        print(f"Error connecting to Flattrade API: {e}")
        return

    # --- Step 2: Fetch Historical Data ---
    print(f"Fetching historical data for {SYMBOL} from {START_DATE} to {END_DATE} with interval {INTERVAL}...")
    try:
        # The exact method and parameters might vary based on the Flattrade client version.
        # This is a common format for such clients.
        # The Flattrade client might return a list of dictionaries or a pandas DataFrame.
        historical_data = flattrade.get_historical_data(
            exchange=EXCHANGE,
            token=SYMBOL, # The API might expect a token instead of a symbol string
            starttime=pd.to_datetime(START_DATE).timestamp(),
            endtime=pd.to_datetime(END_DATE).timestamp(),
            interval=INTERVAL
        )

        if not historical_data:
            print("Error: No data returned from the API. Please check your parameters (symbol, dates, etc.).")
            return

        print(f"Successfully fetched {len(historical_data)} data points.")

    except Exception as e:
        print(f"Error fetching historical data: {e}")
        print("This could be due to an invalid symbol, incorrect API credentials, or an issue with the API service.")
        return

    # --- Step 3: Process and Format Data ---
    try:
        # Convert the list of dictionaries to a pandas DataFrame
        df = pd.DataFrame(historical_data)
        print("Successfully converted data to DataFrame. Columns found:", df.columns.tolist())

        # The Flattrade API might use different column names.
        # We need to rename them to the format our backtester expects:
        # 'Date', 'Open', 'High', 'Low', 'Close', 'Volume'
        
        # Create a mapping of potential API column names to our standard names
        column_mapping = {
            'time': 'Date',
            'into': 'Open',
            'inth': 'High',
            'intl': 'Low',
            'intc': 'Close',
            'intv': 'Volume',
            # Add other potential variations if you discover them
            'd': 'Date',
            'o': 'Open',
            'h': 'High',
            'l': 'Low',
            'c': 'Close',
            'v': 'Volume'
        }
        
        # Rename columns based on the mapping
        df.rename(columns=column_mapping, inplace=True)
        
        # Ensure all required columns are present
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_columns):
            print("Error: The fetched data does not contain all the required columns after renaming.")
            print("Required columns:", required_columns)
            print("Columns found in DataFrame:", df.columns.tolist())
            return
            
        # Convert the 'Date' column to datetime objects
        # The format might be a timestamp or a string, so we handle it accordingly.
        df['Date'] = pd.to_datetime(df['Date'])

        print("Data successfully processed and formatted.")

    except Exception as e:
        print(f"Error processing data: {e}")
        return

    # --- Step 4: Save Data to CSV ---
    try:
        # Save the formatted DataFrame to a CSV file.
        # The index is not saved as the date is now a column.
        df.to_csv(OUTPUT_FILENAME, index=False)
        print(f"Successfully saved data to '{os.path.abspath(OUTPUT_FILENAME)}'")
        print("\nYou can now use this file with the backtester.")

    except Exception as e:
        print(f"Error saving data to CSV: {e}")
        return


# ==============================================================================
# SECTION 3: MAIN EXECUTION BLOCK
# ==============================================================================
if __name__ == "__main__":
    # This function will be called when you run the script from the command line.
    # Example: python fetch_data.py
    fetch_historical_data()