import pandas as pd
import pandas_ta as ta

def calculate_ma(prices: pd.Series, length: int) -> pd.Series:
    """
    Calculates the moving average (MA) for a given series of prices.

    Args:
        prices (pd.Series): A pandas Series of price data.
        length (int): The period for the moving average.

    Returns:
        pd.Series: A pandas Series containing the moving average values.
    """
    return ta.sma(prices, length=length)

def calculate_rsi(prices: pd.Series, length: int = 14) -> pd.Series:
    """
    Calculates the Relative Strength Index (RSI) for a given series of prices.

    Args:
        prices (pd.Series): A pandas Series of price data.
        length (int): The period for the RSI calculation.

    Returns:
        pd.Series: A pandas Series containing the RSI values.
    """
    return ta.rsi(prices, length=length)

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    Calculates the Moving Average Convergence Divergence (MACD) for a given series of prices.

    Args:
        prices (pd.Series): A pandas Series of price data.
        fast (int): The period for the fast EMA.
        slow (int): The period for the slow EMA.
        signal (int): The period for the signal line.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the MACD, histogram, and signal lines.
    """
    return ta.macd(prices, fast=fast, slow=slow, signal=signal)