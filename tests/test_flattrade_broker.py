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

    def test_get_token_success(self):
        """
        Tests that _get_token returns the correct token on success.
        """
        # Arrange
        self.broker.api.searchscrip.return_value = {
            'stat': 'Ok',
            'values': [{'tsym': 'RELIANCE-EQ', 'token': '456'}]
        }

        # Act
        token = self.broker._get_token(symbol='RELIANCE', exchange='NSE')

        # Assert
        self.assertEqual(token, '456')

    def test_get_token_api_returns_none(self):
        """
        Tests that _get_token returns None when the api call returns None.
        """
        # Arrange
        self.broker.api.searchscrip.return_value = None

        # Act
        token = self.broker._get_token(symbol='RELIANCE', exchange='NSE')

        # Assert
        self.assertIsNone(token)

    def test_get_token_api_returns_not_ok(self):
        """
        Tests that _get_token returns None when the api call returns a 'Not_Ok' status.
        """
        # Arrange
        self.broker.api.searchscrip.return_value = {'stat': 'Not_Ok', 'emsg': 'Some error'}

        # Act
        token = self.broker._get_token(symbol='RELIANCE', exchange='NSE')

        # Assert
        self.assertIsNone(token)

    def test_get_token_api_returns_no_values(self):
        """
        Tests that _get_token returns None when the api call returns no 'values'.
        """
        # Arrange
        self.broker.api.searchscrip.return_value = {'stat': 'Ok', 'values': []}

        # Act
        token = self.broker._get_token(symbol='RELIANCE', exchange='NSE')

        # Assert
        self.assertIsNone(token)

    def test_get_token_no_matching_symbol(self):
        """
        Tests that _get_token returns None when no symbol in the response matches.
        """
        # Arrange
        self.broker.api.searchscrip.return_value = {
            'stat': 'Ok',
            'values': [{'tsym': 'INFY-EQ', 'token': '123'}]
        }

        # Act
        token = self.broker._get_token(symbol='RELIANCE', exchange='NSE')

        # Assert
        self.assertIsNone(token)

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
    def test_get_quote_api_not_ok(self, mock_get_token):
        """
        Tests that get_quote returns None when the API returns a 'Not_Ok' status.
        """
        # Arrange
        mock_get_token.return_value = 'test_token'
        self.broker.api.get_quotes.return_value = {'stat': 'Not_Ok', 'emsg': 'Some error'}

        # Act
        quote = self.broker.get_quote(symbol='RELIANCE', exchange='NSE')

        # Assert
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

    @patch('brokers.flattrade.FlattradeBroker._get_token')
    def test_get_historical_data_api_not_ok(self, mock_get_token):
        """
        Tests that get_historical_data returns None when the API returns a 'Not_Ok' status.
        """
        # Arrange
        mock_get_token.return_value = 'test_token'
        self.broker.api.get_time_price_series.return_value = {'stat': 'Not_Ok', 'emsg': 'Some error'}

        # Act
        data = self.broker.get_historical_data(symbol='RELIANCE', exchange='NSE', start_date='2023-01-01', end_date='2023-01-02')

        # Assert
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

    def test_place_order_correct_market_order_params(self):
        """
        Tests that place_order uses the correct parameters for a MARKET order.
        """
        # Act
        self.broker.place_order(symbol='RELIANCE', quantity=10, price=0.0,
                                transaction_type='BUY', order_type='MARKET', product='CNC')

        # Assert
        self.broker.api.place_order.assert_called_with(
            buy_or_sell='B', product_type='C', exchange='NSE',
            tradingsymbol='RELIANCE', quantity=10, discloseqty=0,
            price_type='MKT', price=0.0, trigger_price=0.0,
            retention='DAY', remarks='strategy'
        )

    def test_place_order_correct_sl_order_params(self):
        """
        Tests that place_order uses the correct parameters for a SL order.
        """
        # Act
        self.broker.place_order(symbol='RELIANCE', quantity=10, price=95.0,
                                transaction_type='SELL', order_type='SL', product='MIS')

        # Assert
        self.broker.api.place_order.assert_called_with(
            buy_or_sell='S', product_type='M', exchange='NSE',
            tradingsymbol='RELIANCE', quantity=10, discloseqty=0,
            price_type='SL-MKT', price=0.0, trigger_price=95.0,
            retention='DAY', remarks='strategy'
        )

    def test_place_order_api_returns_none(self):
        """
        Tests that place_order returns None when the API call returns None.
        """
        # Arrange
        self.broker.api.place_order.return_value = None

        # Act
        order_id = self.broker.place_order(symbol='RELIANCE', quantity=10, price=100.0,
                                           transaction_type='BUY', order_type='LIMIT', product='MIS')

        # Assert
        self.assertIsNone(order_id)

    def test_place_order_api_no_orderno(self):
        """
        Tests that place_order returns None when the API response is missing the order number.
        """
        # Arrange
        self.broker.api.place_order.return_value = {'stat': 'Ok'}

        # Act
        order_id = self.broker.place_order(symbol='RELIANCE', quantity=10, price=100.0,
                                           transaction_type='BUY', order_type='LIMIT', product='MIS')

        # Assert
        self.assertIsNone(order_id)

    def test_get_positions_success(self):
        """
        Tests that get_positions returns data on a successful API call.
        """
        # Arrange
        self.broker.api.get_positions.return_value = {'stat': 'Ok', 'positions': ['test_position']}

        # Act
        positions = self.broker.get_positions()

        # Assert
        self.broker.api.get_positions.assert_called_once()
        self.assertEqual(positions, ['test_position'])

    def test_get_positions_failure(self):
        """
        Tests that get_positions returns None when the API call fails.
        """
        # Arrange
        self.broker.api.get_positions.return_value = {'stat': 'Not_Ok', 'emsg': 'Some error'}

        # Act
        positions = self.broker.get_positions()

        # Assert
        self.broker.api.get_positions.assert_called_once()
        self.assertIsNone(positions)

    def test_get_orders_success(self):
        """
        Tests that get_orders returns data on a successful API call.
        """
        # Arrange
        self.broker.api.get_order_book.return_value = {'stat': 'Ok', 'orders': ['test_order']}

        # Act
        orders = self.broker.get_orders()

        # Assert
        self.broker.api.get_order_book.assert_called_once()
        self.assertEqual(orders, ['test_order'])

    def test_get_orders_failure(self):
        """
        Tests that get_orders returns None when the API call fails.
        """
        # Arrange
        self.broker.api.get_order_book.return_value = {'stat': 'Not_Ok', 'emsg': 'Some error'}

        # Act
        orders = self.broker.get_orders()

        # Assert
        self.broker.api.get_order_book.assert_called_once()
        self.assertIsNone(orders)

if __name__ == '__main__':
    unittest.main()
