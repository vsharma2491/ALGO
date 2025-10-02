import unittest
from unittest.mock import patch, call, MagicMock
import os
import sys

# Add project root to path to allow imports from the 'brokers' directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules that are not part of the standard library or not installed.
sys.modules['logger'] = MagicMock()
sys.modules['NorenRestApiPy'] = MagicMock()
sys.modules['NorenRestApiPy.NorenApi'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['flask'] = MagicMock()

from brokers.flattrade import FlattradeBroker

class TestFlattradeAuthentication(unittest.TestCase):
    """Tests the authentication logic of the FlattradeBroker."""

    @patch('brokers.flattrade.os.getenv')
    def test_get_credentials_uses_correct_env_vars(self, mock_getenv):
        """
        Verifies that the `_get_credentials` method reads the correct
        environment variables.
        """
        # Arrange: Patch authenticate to do nothing during instantiation.
        # This prevents the constructor from running the real authentication flow.
        with patch.object(FlattradeBroker, 'authenticate', return_value=None):
            broker = FlattradeBroker()

        # Arrange: Set up the mock for the actual test.
        # Provide dummy credentials to simulate that the env vars are set.
        def getenv_side_effect(key):
            return {
                "FLATTRADE_API_KEY": "test_api_key",
                "FLATTRADE_API_SECRET": "test_api_secret",
                "FLATTRADE_BROKER_ID": "test_broker_id"
            }.get(key)
        mock_getenv.side_effect = getenv_side_effect

        # Act: Call the method under test directly.
        credentials = broker._get_credentials()

        # Assert: Verify that os.getenv was called with the correct names.
        expected_calls = [
            call('FLATTRADE_API_KEY'),
            call('FLATTRADE_API_SECRET'),
            call('FLATTRADE_BROKER_ID')
        ]
        mock_getenv.assert_has_calls(expected_calls, any_order=True)

        # Assert: Verify that the credentials are correct
        self.assertIsNotNone(credentials)
        self.assertEqual(credentials['api_key'], 'test_api_key')
        self.assertEqual(credentials['api_secret'], 'test_api_secret')
        self.assertEqual(credentials['broker_id'], 'test_broker_id')


if __name__ == '__main__':
    unittest.main()