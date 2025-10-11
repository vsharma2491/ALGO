import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules that are not part of the standard library or not installed
sys.modules['logger'] = MagicMock()
sys.modules['NorenRestApiPy'] = MagicMock()
sys.modules['NorenRestApiPy.NorenApi'] = MagicMock()

from brokers.flattrade import FlattradeBroker

class TestFlattradeBroker(unittest.TestCase):
    """Test suite for the FlattradeBroker class."""

    @patch('brokers.flattrade.os.getenv')
    def setUp(self, mock_getenv):
        """Set up the test environment before each test."""
        # Mock environment variables to prevent actual credential loading
        mock_getenv.side_effect = self.getenv_side_effect

        # Patch the authenticate method to prevent it from running during instantiation
        with patch.object(FlattradeBroker, 'authenticate', return_value=None):
            self.broker = FlattradeBroker()
            self.broker.api = MagicMock()  # Mock the NorenApi object
            self.broker.authenticated = True  # Assume authenticated state

    def getenv_side_effect(self, key):
        """Simulate the behavior of os.getenv for credentials."""
        return {
            "FLATTRADE_API_KEY": "test_api_key",
            "FLATTRADE_API_SECRET": "test_api_secret",
            "FLATTRADE_BROKER_ID": "test_broker_id"
        }.get(key)

    def test_initialization(self):
        """Test that the broker is initialized correctly."""
        self.assertIsInstance(self.broker, FlattradeBroker)
        self.assertTrue(self.broker.authenticated)

    def test_get_quote_success(self):
        """Test successful retrieval of a quote."""
        # Arrange
        self.broker._get_token = MagicMock(return_value="12345")
        self.broker.api.get_quotes.return_value = {"stat": "Ok", "last_price": 100.0}

        # Act
        quote = self.broker.get_quote("RELIANCE")

        # Assert
        self.assertIsNotNone(quote)
        self.assertEqual(quote['last_price'], 100.0)
        self.broker._get_token.assert_called_once_with("NSE", "RELIANCE")
        self.broker.api.get_quotes.assert_called_once_with(exchange="NSE", token="12345")

    def test_place_order_success(self):
        """Test successful order placement."""
        # Arrange
        self.broker.api.place_order.return_value = {"stat": "Ok", "norenordno": "2206200000001"}

        # Act
        order_id = self.broker.place_order(
            symbol="INFY",
            quantity=10,
            price=1500.0,
            transaction_type="BUY",
            order_type="LIMIT",
            product="MIS"
        )

        # Assert
        self.assertEqual(order_id, "2206200000001")
        self.broker.api.place_order.assert_called_once()

    def test_place_order_failure(self):
        """Test failed order placement."""
        # Arrange
        self.broker.api.place_order.return_value = {"stat": "Not_Ok", "emsg": "Invalid parameters"}

        # Act
        order_id = self.broker.place_order(
            symbol="TCS",
            quantity=5,
            price=3200.0,
            transaction_type="SELL",
            order_type="MARKET",
            product="CNC"
        )

        # Assert
        self.assertIsNone(order_id)

    def test_get_positions_success(self):
        """Test successful retrieval of positions."""
        # Arrange
        self.broker.api.get_positions.return_value = [{"symbol": "HDFCBANK", "quantity": 100}]

        # Act
        positions = self.broker.get_positions()

        # Assert
        self.assertIsNotNone(positions)
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['symbol'], "HDFCBANK")

    def test_get_orders_success(self):
        """Test successful retrieval of the order book."""
        # Arrange
        self.broker.api.get_order_book.return_value = [{"order_id": "12345", "status": "COMPLETE"}]

        # Act
        orders = self.broker.get_orders()

        # Assert
        self.assertIsNotNone(orders)
        self.assertEqual(orders[0]['status'], "COMPLETE")

    def test_place_sl_order(self):
        """Test correct parameter handling for SL orders."""
        # Arrange
        self.broker.api.place_order.return_value = {"stat": "Ok", "norenordno": "2206200000002"}

        # Act
        self.broker.place_order(
            symbol="RELIANCE",
            quantity=1,
            price=2500.0,
            transaction_type="BUY",
            order_type="SL",
            product="MIS"
        )

        # Assert
        self.broker.api.place_order.assert_called_with(
            buy_or_sell='B',
            product_type='M',
            exchange='NSE',
            tradingsymbol='RELIANCE',
            quantity=1,
            discloseqty=0,
            price_type='SL-MKT',
            price=0.0,
            trigger_price=2500.0,
            retention='DAY',
            remarks='strategy'
        )

    def test_websocket_connection(self):
        """Test that the WebSocket connection is initialized correctly."""
        # Act
        self.broker.connect_websocket()

        # Assert
        self.broker.api.start_websocket.assert_called_once()

    def test_subscribe_unsubscribe(self):
        """Test subscribing and unsubscribing from symbols."""
        # Arrange
        self.broker._get_token = MagicMock(side_effect=["token1", "token2", "token1", "token2"])
        symbols = ["SBIN", "TATASTEEL"]
        instrument_list = ["NSE|token1", "NSE|token2"]

        # Act: Subscribe
        self.broker.subscribe(symbols)

        # Assert: Subscribe
        self.broker.api.subscribe.assert_called_with(instrument_list)
        self.broker._get_token.assert_has_calls([call("NSE", "SBIN"), call("NSE", "TATASTEEL")])

        # Act: Unsubscribe
        self.broker.unsubscribe(symbols)

        # Assert: Unsubscribe
        self.broker.api.unsubscribe.assert_called_with(instrument_list)

if __name__ == '__main__':
    unittest.main()