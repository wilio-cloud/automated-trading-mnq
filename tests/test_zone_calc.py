import unittest
import datetime
import os
import sys
import pytz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.zone_calculator import zone_calculator

class TestZoneCalculator(unittest.TestCase):
    def test_live_cme_feed(self):
        tz = pytz.timezone("America/New_York")
        yesterday = (datetime.datetime.now(tz) - datetime.timedelta(days=1)).date()
        
        # Test calculació de Londres
        high, low = zone_calculator.calculate_london_range(yesterday)
        self.assertIsNotNone(high)
        self.assertIsNotNone(low)
        self.assertGreater(high, low)
        
        # Comprovar tick size (multiple de 0.25)
        self.assertEqual(round((high * 4) % 1, 4), 0)
        self.assertEqual(round((low * 4) % 1, 4), 0)

if __name__ == "__main__":
    unittest.main()
