import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path to allow imports.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules that are not part of the standard library or not installed.
sys.modules['logger'] = MagicMock()
sys.modules['NorenRestApiPy'] = MagicMock()
sys.modules['NorenRestApiPy.NorenApi'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['flask'] = MagicMock()

from brokers.flattrade import FlattradeBroker

class TestFlattradeBroker(unittest.TestCase):
    """Tests the FlattradeBroker class."""

    def setUp(self):
        """Set up a broker instance for testing."""
        # Patch authenticate to prevent it from running during instantiation.
        with patch.object(FlattradeBroker, 'authenticate', return_value=None):
            self.broker = FlattradeBroker()
            # Mock the api object after instantiation
            self.broker.api = MagicMock()

    @patch('brokers.flattrade.FlattradeBroker._get_token')
    def test_get_quote_success(self, mock_get_token):
        """
        Tests that get_quote returns data when a valid token is found.
        """
        # Arrange
        mock_get_token.return_value = 'test_token'
        self.broker.api.get_quotes.return_value = {'stat': 'Ok', 'last_price': 100}

        # Act
        quote = self.broker.get_quote(symbol='RELIANCE', exchange='NSE')

        # Assert
        mock_get_token.assert_called_once_with('NSE', 'RELIANCE')
        self.broker.api.get_quotes.assert_called_once_with(exchange='NSE', token='test_token')
        self.assertEqual(quote, {'stat': 'Ok', 'last_price': 100})

    @patch('brokers.flattrade.FlattradeBroker._get_token')
    def test_get_quote_token_not_found(self, mock_get_token):
        """
        Tests that get_quote returns None when a token is not found.
        """
        # Arrange
        mock_get_token.return_value = None

        # Act
        quote = self.broker.get_quote(symbol='RELIANCE', exchange='NSE')

        # Assert
        mock_get_token.assert_called_once_with('NSE', 'RELIANCE')
        self.broker.api.get_quotes.assert_not_called()
        self.assertIsNone(quote)

    @patch('brokers.flattrade.FlattradeBroker._get_token')
    def test_get_historical_data_success(self, mock_get_token):
        """
        Tests that get_historical_data returns data for valid inputs.
        """
        # Arrange
        mock_get_token.return_value = 'test_token'
        self.broker.api.get_time_price_series.return_value = [{'time': '2023-01-01', 'price': 100}]

        # Act
        data = self.broker.get_historical_data(symbol='RELIANCE', exchange='NSE', start_date='2023-01-01', end_date='2023-01-02')

        # Assert
        mock_get_token.assert_called_once_with('NSE', 'RELIANCE')
        self.broker.api.get_time_price_series.assert_called_once()
        self.assertEqual(data, [{'time': '2023-01-01', 'price': 100}])

    @patch('brokers.flattrade.FlattradeBroker._get_token')
    def test_get_historical_data_token_not_found(self, mock_get_token):
        """
        Tests that get_historical_data returns None when a token is not found.
        """
        # Arrange
        mock_get_token.return_value = None

        # Act
        data = self.broker.get_historical_data(symbol='RELIANCE', exchange='NSE', start_date='2023-01-01', end_date='2023-01-02')

        # Assert
        mock_get_token.assert_called_once_with('NSE', 'RELIANCE')
        self.broker.api.get_time_price_series.assert_not_called()
        self.assertIsNone(data)

    def test_get_historical_data_invalid_date_format(self):
        """
        Tests that get_historical_data returns None for invalid date formats.
        """
        # Act
        data = self.broker.get_historical_data(symbol='RELIANCE', exchange='NSE', start_date='2023/01/01', end_date='2023/01/02')

        # Assert
        self.broker.api.get_time_price_series.assert_not_called()
        self.assertIsNone(data)

    def test_place_order_buy_success(self):
        """
        Tests that place_order returns an order ID for a successful BUY order.
        """
        # Arrange
        self.broker.api.place_order.return_value = {'stat': 'Ok', 'norenordno': '12345'}

        # Act
        order_id = self.broker.place_order(symbol='RELIANCE', quantity=10, price=100.0, transaction_type='BUY', order_type='LIMIT', product='MIS')

        # Assert
        self.broker.api.place_order.assert_called_once()
        self.assertEqual(order_id, '12345')

    def test_place_order_sell_success(self):
        """
        Tests that place_order returns an order ID for a successful SELL order.
        """
        # Arrange
        self.broker.api.place_order.return_value = {'stat': 'Ok', 'norenordno': '67890'}

        # Act
        order_id = self.broker.place_order(symbol='RELIANCE', quantity=10, price=100.0, transaction_type='SELL', order_type='LIMIT', product='MIS')

        # Assert
        self.broker.api.place_order.assert_called_once()
        self.assertEqual(order_id, '67890')

    def test_place_order_failure(self):
        """
        Tests that place_order returns None when the order placement fails.
        """
        # Arrange
        self.broker.api.place_order.return_value = {'stat': 'Not_Ok', 'emsg': 'Order failed'}

        # Act
        order_id = self.broker.place_order(symbol='RELIANCE', quantity=10, price=100.0, transaction_type='BUY', order_type='LIMIT', product='MIS')

        # Assert
        self.broker.api.place_order.assert_called_once()
        self.assertIsNone(order_id)

if __name__ == '__main__':
    unittest.main()
