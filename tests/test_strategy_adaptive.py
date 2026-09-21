import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from unittest.mock import MagicMock, patch
import datetime
import pytz

from bot.strategy import LondonZonesStrategy
from bot.config import config

class TestAdaptiveStrategy(unittest.TestCase):
    def setUp(self):
        self.strat = LondonZonesStrategy()

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.risk_manager")
    @patch("bot.strategy.zone_calculator")
    @patch("bot.strategy.notifier")
    def test_dynamic_tp_under_21000(self, mock_notifier, mock_zone_calc, mock_risk_mgr, mock_client):
        mock_client.authenticate.return_value = True
        mock_client.has_orders_or_fills_today.return_value = False
        mock_client.get_current_market_price.return_value = 18450.0
        mock_client.get_cash_balance.return_value = 50000.0
        mock_risk_mgr.calculate_contracts.return_value = 5
        mock_risk_mgr.validate_margin.return_value = True
        
        # NQ a 18.000 pts (< 21.000) -> Ha d'aplicar TP 8 pts
        mock_zone_calc.calculate_london_range.return_value = (18500.0, 18400.0)
        
        now = datetime.datetime(2026, 9, 15, 5, 5, tzinfo=self.strat.tz)
        self.strat.on_london_close(now)
        
        # Comprovar crida de short bracket: entry=18500, tp=18492 (-8 pts), sl=18500 + config.sl_points
        mock_client.place_bracket_order.assert_any_call(
            symbol=self.strat.active_symbol,
            action="Sell",
            qty=5,
            entry_price=18500.0,
            tp_price=18492.0,
            sl_price=18500.0 + config.sl_points
        )

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.risk_manager")
    @patch("bot.strategy.zone_calculator")
    @patch("bot.strategy.notifier")
    def test_dynamic_tp_above_21000(self, mock_notifier, mock_zone_calc, mock_risk_mgr, mock_client):
        mock_client.authenticate.return_value = True
        mock_client.has_orders_or_fills_today.return_value = False
        mock_client.get_current_market_price.return_value = 29050.0
        mock_client.get_cash_balance.return_value = 50000.0
        mock_risk_mgr.calculate_contracts.return_value = 5
        mock_risk_mgr.validate_margin.return_value = True
        
        # NQ a 29.000 pts (>= 21.000) -> Ha d'aplicar TP dinàmic (config.tp_points)
        mock_zone_calc.calculate_london_range.return_value = (29100.0, 29000.0)
        
        now = datetime.datetime(2026, 9, 15, 5, 5, tzinfo=self.strat.tz)
        self.strat.on_london_close(now)
        
        mock_client.place_bracket_order.assert_any_call(
            symbol=self.strat.active_symbol,
            action="Sell",
            qty=5,
            entry_price=29100.0,
            tp_price=round(29100.0 - config.tp_points, 2),
            sl_price=29100.0 + config.sl_points
        )

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.risk_manager")
    @patch("bot.strategy.zone_calculator")
    @patch("bot.strategy.notifier")
    def test_sanity_guard_prevents_marketable_orders(self, mock_notifier, mock_zone_calc, mock_risk_mgr, mock_client):
        mock_client.authenticate.return_value = True
        mock_client.has_orders_or_fills_today.return_value = False
        # Preu actual a 29500 -> Per sobre del Sell Limit a 29100
        mock_client.get_current_market_price.return_value = 29500.0
        mock_client.get_cash_balance.return_value = 50000.0
        mock_risk_mgr.calculate_contracts.return_value = 1
        mock_risk_mgr.validate_margin.return_value = True
        mock_zone_calc.calculate_london_range.return_value = (29100.0, 29000.0)

        now = datetime.datetime(2026, 9, 15, 5, 5, tzinfo=self.strat.tz)
        self.strat.on_london_close(now)

        # Comprovar que NO s'ha enviat cap ordre de Sell Limit perquè el preu està per sobre
        sell_calls = [c for c in mock_client.place_bracket_order.call_args_list if c.kwargs.get("action") == "Sell"]
        self.assertEqual(len(sell_calls), 0)

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.risk_manager")
    @patch("bot.strategy.zone_calculator")
    @patch("bot.strategy.notifier")
    def test_existing_broker_orders_blocks_duplicate(self, mock_notifier, mock_zone_calc, mock_risk_mgr, mock_client):
        mock_client.authenticate.return_value = True
        # Ja hi ha ordres/fills avui a Tradovate
        mock_client.has_orders_or_fills_today.return_value = True

        now = datetime.datetime(2026, 9, 15, 5, 5, tzinfo=self.strat.tz)
        self.strat.on_london_close(now)

        mock_client.place_bracket_order.assert_not_called()
        self.assertTrue(self.strat.orders_placed)

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.notifier")
    def test_amber_cancellation_at_1420(self, mock_notifier, mock_client):
        # 2026-10-02 és NFP (AMBER)
        mock_client.authenticate.return_value = True
        mock_client.has_orders_or_fills_today.return_value = False
        self.strat.reset_for_new_day(datetime.date(2026, 10, 2))
        self.strat.orders_placed = True
        self.strat.amber_cleaned = False
        
        # 14:25 CEST (8:25 EDT) -> Abans de 14:30 NFP -> Ha de cancel·lar ordres pendents
        now_edt = datetime.datetime(2026, 10, 2, 8, 25, tzinfo=self.strat.tz)
        self.strat.process_tick(now_edt)
        
        mock_client.cancel_all_pending_orders.assert_called_once()
        self.assertTrue(self.strat.amber_cleaned)

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.notifier")
    def test_weekend_no_notifications_or_orders(self, mock_notifier, mock_client):
        # 2026-09-19 és dissabte (weekday = 5)
        saturday = datetime.date(2026, 9, 19)
        self.strat.reset_for_new_day(saturday)
        
        self.assertTrue(self.strat.orders_placed)
        self.assertTrue(self.strat.eod_cleaned)
        
        # Test 1: Tick a les 11:00 CEST (5:00 EDT) en dissabte
        saturday_11am = datetime.datetime(2026, 9, 19, 5, 0, tzinfo=self.strat.tz)
        self.strat.process_tick(saturday_11am)
        mock_client.place_bracket_order.assert_not_called()
        mock_notifier.send.assert_not_called()
        
        # Test 2: Tick a les 22:55 CEST (16:55 EDT) en dissabte
        saturday_eod = datetime.datetime(2026, 9, 19, 16, 55, tzinfo=self.strat.tz)
        self.strat.process_tick(saturday_eod)
        self.strat.on_eod_close(saturday_eod)
        mock_client.close_all_positions.assert_not_called()
        mock_notifier.send.assert_not_called()

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.notifier")
    def test_london_cutoff_at_1520(self, mock_notifier, mock_client):
        # 15:20 CEST = 09:20 EDT
        mock_client.authenticate.return_value = True
        mock_client.has_orders_or_fills_today.return_value = False
        mock_client.get_open_positions.return_value = []
        mock_client.cancel_all_pending_orders.return_value = 2

        t_date = datetime.date(2026, 9, 22)  # Dimarts net
        self.strat.reset_for_new_day(t_date)
        self.strat.orders_placed = True
        self.strat.cutoff_cleaned = False

        # Tick a les 09:20 EDT (15:20 CEST)
        now_edt = datetime.datetime(2026, 9, 22, 9, 20, tzinfo=self.strat.tz)
        self.strat.process_tick(now_edt)

        mock_client.cancel_all_pending_orders.assert_called_once()
        self.assertTrue(self.strat.cutoff_cleaned)

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.notifier")
    def test_macro_opex_blocks_orders(self, mock_notifier, mock_client):
        # 2026-10-16 és 3r divendres d'octubre (OpEx mensual)
        opex_date = datetime.date(2026, 10, 16)
        self.strat.reset_for_new_day(opex_date)

        now_11am = datetime.datetime(2026, 10, 16, 5, 0, tzinfo=self.strat.tz)
        self.strat.on_london_close(now_11am)

        mock_client.place_bracket_order.assert_not_called()
        self.assertTrue(self.strat.orders_placed)

    def test_benchmark_parameters(self):
        # TP 14 pts (+28$) i SL 60 pts (-120$) del model institucional
        self.assertEqual(config.tp_points, 14.0)
        self.assertEqual(config.sl_points, 60.0)
        self.assertEqual(config.london_cutoff_hour, 9)
        self.assertEqual(config.london_cutoff_minute, 20)

if __name__ == "__main__":
    unittest.main()
