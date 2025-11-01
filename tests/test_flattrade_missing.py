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

class TestFlattradeBrokerMissing(unittest.TestCase):
    """Tests the FlattradeBroker class."""

    def setUp(self):
        """Set up a broker instance for testing."""
        # Patch authenticate to prevent it from running during instantiation.
        with patch.object(FlattradeBroker, 'authenticate', return_value=None):
            self.broker = FlattradeBroker()
            # Mock the api object after instantiation
            self.broker.api = MagicMock()

    def test_get_token_not_found(self):
        """
        Tests that _get_token returns None when the token is not found.
        """
        # Arrange
        self.broker.api.searchscrip.return_value = {'stat': 'Ok', 'values': []}

        # Act
        token = self.broker._get_token(exchange='NSE', symbol='RELIANCE')

        # Assert
        self.broker.api.searchscrip.assert_called_once_with(exchange='NSE', searchtext='RELIANCE-EQ')
        self.assertIsNone(token)

    def test_get_positions(self):
        """
        Tests that get_positions calls the api correctly.
        """
        # Arrange
        self.broker.api.get_positions.return_value = [{'symbol': 'RELIANCE', 'quantity': 10}]

        # Act
        positions = self.broker.get_positions()

        # Assert
        self.broker.api.get_positions.assert_called_once()
        self.assertEqual(positions, [{'symbol': 'RELIANCE', 'quantity': 10}])

    def test_get_orders(self):
        """
        Tests that get_orders calls the api correctly.
        """
        # Arrange
        self.broker.api.get_order_book.return_value = [{'order_id': '12345'}]

        # Act
        orders = self.broker.get_orders()

        # Assert
        self.broker.api.get_order_book.assert_called_once()
        self.assertEqual(orders, [{'order_id': '12345'}])

    def test_connect_websocket(self):
        """
        Tests that connect_websocket calls the api correctly.
        """
        # Act
        self.broker.connect_websocket()

        # Assert
        self.broker.api.start_websocket.assert_called_once()

    @patch('brokers.flattrade.FlattradeBroker._get_token')
    def test_subscribe(self, mock_get_token):
        """
        Tests that subscribe calls the api correctly.
        """
        # Arrange
        mock_get_token.return_value = 'test_token'

        # Act
        self.broker.subscribe(symbols=['RELIANCE'], exchange='NSE')

        # Assert
        mock_get_token.assert_called_once_with('NSE', 'RELIANCE')
        self.broker.api.subscribe.assert_called_once_with(['NSE|test_token'])

    @patch('brokers.flattrade.FlattradeBroker._get_token')
    def test_unsubscribe(self, mock_get_token):
        """
        Tests that unsubscribe calls the api correctly.
        """
        # Arrange
        mock_get_token.return_value = 'test_token'

        # Act
        self.broker.unsubscribe(symbols=['RELIANCE'], exchange='NSE')

        # Assert
        mock_get_token.assert_called_once_with('NSE', 'RELIANCE')
        self.broker.api.unsubscribe.assert_called_once_with(['NSE|test_token'])

    @patch('brokers.flattrade.logger')
    def test_on_ticks(self, mock_logger):
        """
        Tests the on_ticks callback.
        """
        # Act
        self.broker.on_ticks('some_ticks')

        # Assert
        mock_logger.info.assert_called_once_with("Ticks: some_ticks")

    @patch('brokers.flattrade.logger')
    def test_on_connect(self, mock_logger):
        """
        Tests the on_connect callback.
        """
        # Act
        self.broker.on_connect()

        # Assert
        mock_logger.info.assert_called_once_with("WebSocket connected.")

    @patch('brokers.flattrade.logger')
    def test_on_close(self, mock_logger):
        """
        Tests the on_close callback.
        """
        # Act
        self.broker.on_close()

        # Assert
        mock_logger.info.assert_called_once_with("WebSocket closed.")

    @patch('brokers.flattrade.logger')
    def test_on_error(self, mock_logger):
        """
        Tests the on_error callback.
        """
        # Act
        self.broker.on_error('some_error')

        # Assert
        mock_logger.error.assert_called_once_with("WebSocket error: some_error")

    @patch('brokers.flattrade.logger')
    def test_on_order_update(self, mock_logger):
        """
        Tests the on_order_update callback.
        """
        # Act
        self.broker.on_order_update('some_order_data')

        # Assert
        mock_logger.info.assert_called_once_with("Order Update: some_order_data")

if __name__ == '__main__':
    unittest.main()
