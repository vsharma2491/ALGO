import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import pandas as pd

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import main

class TestMain(unittest.TestCase):

    def setUp(self):
        """
        Set up a simple dataset for testing.
        """
        self.mock_data = pd.DataFrame({
            'datetime': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']),
            'close': [100, 102, 101, 103, 105]
        })

    @patch('main.argparse.ArgumentParser')
    def test_main_download_data(self, mock_argparse):
        """
        Test that the main function calls the download_nifty_data function
        when the --download-data argument is provided.
        """
        mock_args = MagicMock()
        mock_args.download_data = True
        mock_args.start_date = "2023-01-01"
        mock_args.end_date = "2023-12-31"
        mock_argparse.return_value.parse_args.return_value = mock_args

        with patch('main.download_nifty_data') as mock_download:
            main()
            mock_download.assert_called_once_with("2023-01-01", "2023-12-31")

    @patch('main.argparse.ArgumentParser')
    @patch('main.Backtester')
    def test_main_vectorized_backtester(self, mock_backtester, mock_argparse):
        """
        Test that the main function calls the vectorized backtester when the
        --backtester argument is set to 'vectorized'.
        """
        mock_args = MagicMock()
        mock_args.download_data = False
        mock_args.backtester = 'vectorized'
        mock_args.strategy = 'ma_crossover'
        mock_args.sample_data = True
        mock_argparse.return_value.parse_args.return_value = mock_args

        mock_backtester_instance = mock_backtester.return_value
        mock_equity_curve = pd.Series([100000, 100010, 100020], index=pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']))
        mock_backtester_instance.run.return_value = ({}, pd.DataFrame(), mock_equity_curve)

        with patch('main.pd.read_csv') as mock_read_csv:
            mock_read_csv.return_value = self.mock_data
            main()
            mock_backtester.assert_called()

    @patch('main.argparse.ArgumentParser')
    @patch('main.BacktraderEngine')
    def test_main_event_driven_backtester(self, mock_backtrader_engine, mock_argparse):
        """
        Test that the main function calls the event-driven backtester when the
        --backtester argument is set to 'event_driven'.
        """
        mock_args = MagicMock()
        mock_args.download_data = False
        mock_args.backtester = 'event_driven'
        mock_args.strategy = 'ema_cross_atr_stops'
        mock_args.sample_data = True
        mock_argparse.return_value.parse_args.return_value = mock_args

        with patch('main.pd.read_csv') as mock_read_csv:
            mock_read_csv.return_value = self.mock_data
            main()
            mock_backtrader_engine.assert_called()

if __name__ == '__main__':
    unittest.main()
