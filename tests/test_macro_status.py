import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.macro_calendar import get_day_trading_status

def test_weekend_status():
    saturday = datetime.date(2026, 9, 19)
    sunday = datetime.date(2026, 9, 20)
    
    sat_res = get_day_trading_status(saturday)
    assert sat_res["status"] == "NOT_OPERABLE"
    assert sat_res["is_weekend"] is True
    assert "CAP DE SETMANA" in sat_res["badge"]

    sun_res = get_day_trading_status(sunday)
    assert sun_res["status"] == "NOT_OPERABLE"
    assert sun_res["is_weekend"] is True

def test_holiday_status():
    christmas = datetime.date(2026, 12, 25)
    res = get_day_trading_status(christmas)
    assert res["status"] == "NOT_OPERABLE"
    assert res["can_trade"] is False
    assert res["is_holiday"] is True
    assert "NO OPERAR" in res["badge"]

def test_fomc_status():
    fomc_sep = datetime.date(2026, 12, 16)
    res = get_day_trading_status(fomc_sep)
    assert res["status"] == "NOT_OPERABLE"
    assert res["can_trade"] is False
    assert "NO OPERAR" in res["badge"]

def test_amber_nfp_status():
    nfp = datetime.date(2026, 10, 2)
    res = get_day_trading_status(nfp)
    assert res["status"] == "NOT_OPERABLE"
    assert res["can_trade"] is False
    assert "NO OPERAR" in res["badge"]

def test_quarter_end_sep30_status():
    d30 = datetime.date(2026, 9, 30)
    res = get_day_trading_status(d30)
    assert res["status"] == "NOT_OPERABLE"
    assert res["can_trade"] is False
    assert "REBALANCING" in res["badge"]

def test_clean_green_day():
    clean_day = datetime.date(2026, 9, 17)
    res = get_day_trading_status(clean_day)
    assert res["status"] == "OPERABLE"
    assert res["can_trade"] is True
    assert res["severity"] == "GREEN"
    assert "OPERAR" in res["badge"]

def test_today_sep29_operable():
    today = datetime.date(2026, 9, 29)
    res = get_day_trading_status(today)
    assert res["status"] == "OPERABLE"
    assert res["can_trade"] is True
    assert res["severity"] == "GREEN"
    assert "OPERAR" in res["badge"]
    assert "ZONES LONDRES" in res["title"]

if __name__ == "__main__":
    test_weekend_status()
    test_holiday_status()
    test_fomc_status()
    test_amber_nfp_status()
    test_quarter_end_sep30_status()
    test_clean_green_day()
    test_today_sep29_operable()
    print("✅ Tots els tests de test_macro_status han passat correctament!")
