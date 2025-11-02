# Nifty Options Backtesting System

This is a fully automated Nifty options backtesting system built in Python. It allows you to download historical data, test different trading strategies, and generate comprehensive performance reports.

## Features

-   **Automated Data Download:** Download historical 1-minute Nifty data from the Flattrade API.
-   **Modular Strategy Framework:** Easily create and test new trading strategies.
-   **Comprehensive Performance Metrics:** Get a detailed analysis of your strategy's performance.
-   **Detailed Reporting:** Generate reports in console, CSV, Excel, and HTML formats.
-   **Command-Line Interface:** Run the entire system from the command line.

## Project Structure

```
/
├── config/
│   ├── config.yaml
│   └── credentials.py.template
├── data/
│   └── nifty_1min_data.csv
├── results/
│   ├── backtest_results.xlsx
│   ├── backtest_results.html
│   ├── ...
├── strategies/
│   ├── base_strategy.py
│   ├── ma_crossover.py
│   └── strategy_template.py
├── tests/
│   └── ...
├── .gitignore
├── main.py
├── data_downloader.py
├── backtest_engine.py
├── reporting.py
└── requirements.txt
```

## Setup

### 1. Clone the Repository

```bash
git clone <repository_url>
cd <repository_name>
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate # On Windows, use `.venv\Scripts\activate`
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Credentials

Copy the `credentials.py.template` file to `credentials.py` and fill in your Flattrade API details.

```bash
cp config/credentials.py.template config/credentials.py
```

Now, edit `config/credentials.py` with your API key, secret, client ID, and redirect URI.

## Usage

### 1. Download Historical Data

Run the following command to download the latest historical data for Nifty:

```bash
python main.py --download-data
```

This will save the data to `data/nifty_1min_data.csv`. The script will automatically detect existing data and only download new dates.

### 2. Run a Backtest

To run a backtest with the default `ma_crossover` strategy, use the following command:

```bash
python main.py --strategy ma_crossover
```

You can also specify a custom date range for the backtest:

```bash
python main.py --strategy ma_crossover --start-date 2023-01-01 --end-date 2023-06-30
```

The backtest results will be printed to the console and saved in the `results/` directory.

### 3. Create a New Strategy

To create a new strategy, copy the `strategy_template.py` file and modify it with your own logic.

```bash
cp strategies/strategy_template.py strategies/my_strategy.py
```

Then, you can run a backtest with your new strategy:

```bash
python main.py --strategy my_strategy
```

## Troubleshooting

-   **Authentication Errors:** Double-check your API credentials in `config/credentials.py`.
-   **Data Download Issues:** Ensure you have a stable internet connection. If the issue persists, check the Flattrade API documentation for any changes.
-   **"File not found" errors:** Make sure you are running the `main.py` script from the root directory of the project.
