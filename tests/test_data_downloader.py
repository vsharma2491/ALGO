import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import pandas as pd

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules that are not part of the standard library or not installed.
sys.modules['logger'] = MagicMock()
sys.modules['NorenRestApiPy'] = MagicMock()
sys.modules['NorenRestApiPy.NorenApi'] = MagicMock()

from data_downloader import download_nifty_data

class TestDataDownloader(unittest.TestCase):

    @patch('data_downloader.FlattradeBroker')
    def test_download_nifty_data_fresh(self, mock_broker):
        """
        Test that the download_nifty_data function downloads data when no
        existing data is present.
        """
        mock_broker_instance = MagicMock()
        mock_broker.return_value = mock_broker_instance
        mock_broker_instance.get_historical_data.return_value = [{'time': '1672531200', 'into': '100', 'inth': '102', 'intl': '99', 'intc': '101', 'intv': '1000'}]

        with patch('os.path.exists', return_value=False):
            with patch('pandas.DataFrame.to_csv') as mock_to_csv:
                download_nifty_data("2023-01-01", "2023-01-02")
                mock_to_csv.assert_called_once()

    @patch('data_downloader.FlattradeBroker')
    @patch('os.path.exists', return_value=True)
    @patch('pandas.read_csv')
    def test_download_nifty_data_resume(self, mock_read_csv, mock_exists, mock_broker):
        """
        Test that the download_nifty_data function resumes downloading from the
        last available date.
        """
        mock_broker_instance = MagicMock()
        mock_broker.return_value = mock_broker_instance
        mock_broker_instance.get_historical_data.return_value = []

        mock_existing_data = pd.DataFrame({
            'datetime': pd.to_datetime(['2023-01-01']),
            'close': [100]
        })
        mock_read_csv.return_value = mock_existing_data

        download_nifty_data("2023-01-01", "2023-01-03")
        mock_broker_instance.get_historical_data.assert_called_once_with('NIFTY 50', 'NSE', '2023-01-02', '2023-01-03', interval='1')

if __name__ == '__main__':
    unittest.main()
