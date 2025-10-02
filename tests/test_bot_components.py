import unittest
import pandas as pd
from datetime import datetime

from trading_bot.bot import indicators
from trading_bot.bot.risk_manager import RiskManager
from trading_bot.bot.position_manager import PositionManager, Position

class TestIndicators(unittest.TestCase):
    """Tests for the technical indicator calculations."""

    def setUp(self):
        """Set up a sample price series for testing."""
        self.prices = pd.Series([100, 102, 105, 103, 106, 108, 110, 109, 112, 115])

    def test_calculate_ma(self):
        """Test the moving average calculation."""
        ma = indicators.calculate_ma(self.prices, length=5)
        self.assertAlmostEqual(ma.iloc[-1], 110.80, places=2)

    def test_calculate_rsi(self):
        """Test the RSI calculation."""
        rsi = indicators.calculate_rsi(self.prices, length=5)
        self.assertAlmostEqual(rsi.iloc[-1], 90.05, places=2)

    def test_calculate_macd(self):
        """Test the MACD calculation."""
        macd_df = indicators.calculate_macd(self.prices, fast=3, slow=6, signal=2)
        self.assertAlmostEqual(macd_df['MACD_3_6_2'].iloc[-1], 2.51, places=2)

class TestRiskManager(unittest.TestCase):
    """Tests for the RiskManager."""

    def test_can_open_new_position_within_limits(self):
        """Test that a new position can be opened when within limits."""
        risk_manager = RiskManager(max_concurrent_positions=5)
        self.assertTrue(risk_manager.can_open_new_position("NIFTY 50", 4))

    def test_cannot_open_new_position_when_max_reached(self):
        """Test that a new position cannot be opened when the max limit is reached."""
        risk_manager = RiskManager(max_concurrent_positions=5)
        self.assertFalse(risk_manager.can_open_new_position("NIFTY 50", 5))

    def test_cannot_re_enter_position_on_same_day(self):
        """Test that a position cannot be re-entered on the same day."""
        risk_manager = RiskManager(max_concurrent_positions=5)
        risk_manager.add_closed_position("NIFTY 50")
        self.assertFalse(risk_manager.can_open_new_position("NIFTY 50", 2))

    def test_reset_clears_closed_positions(self):
        """Test that the reset method clears the set of closed positions."""
        risk_manager = RiskManager(max_concurrent_positions=5)
        risk_manager.add_closed_position("NIFTY 50")
        risk_manager.reset()
        self.assertTrue(risk_manager.can_open_new_position("NIFTY 50", 0))

class TestPositionManager(unittest.TestCase):
    """Tests for the PositionManager."""

    def setUp(self):
        self.pm = PositionManager()
        self.entry_time = datetime.now()

    def test_add_and_get_position(self):
        """Test adding and retrieving a position."""
        self.pm.add_position("NIFTY 50", "BUY", 15000, 1, 14850, 15300, self.entry_time)
        self.assertEqual(self.pm.get_open_position_count(), 1)
        position = self.pm.get_position("NIFTY 50")
        self.assertIsInstance(position, Position)

    def test_remove_position(self):
        """Test removing a position."""
        self.pm.add_position("NIFTY 50", "BUY", 15000, 1, 14850, 15300, self.entry_time)
        self.pm.remove_position("NIFTY 50")
        self.assertEqual(self.pm.get_open_position_count(), 0)

    def test_update_pnl(self):
        """Test P&L calculation for a position."""
        self.pm.add_position("NIFTY 50", "BUY", 15000, 2, 14850, 15300, self.entry_time)
        position = self.pm.get_position("NIFTY 50")
        position.update_pnl(15050)
        self.assertEqual(position.pnl, 100)