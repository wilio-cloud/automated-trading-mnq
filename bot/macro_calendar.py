"""
Base de Dades del Calendari Macroeconòmic Institucional (2026 - 2027)
Filtre de Risc per a CME Globex MNQ
"""

import datetime
from typing import Optional, Dict, Any

MACRO_EVENTS = {
    # --- 2026 ---
    "2026-09-16": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CEST", "instructions": "Decisió de tipus de la Fed. Tancament obligatori abans de les 18:00 CEST."},
    "2026-09-18": {"type": "OPEX", "severity": "AMBER", "name": "Quadruple Witching OpEx (Venciment Trimestral)", "time_cest": "Tot el dia", "instructions": "Alta volatilitat d'expiració de contractes. Londres operable amb normalitat de 11:00 a 16:00 CEST."},
    "2026-09-30": {"type": "REBALANCING", "severity": "AMBER", "name": "Final de Trimestre Q3 Rebalancing", "time_cest": "16:00 - 22:00 CEST", "instructions": "Fluxos de reequilibri institucional de carteres al final de la sessió americana. Londres al matí és 100% net."},
    "2026-10-02": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Sessió de Londres normal al matí (11:00 a 14:20 CEST). Si no s'ha tocat a les 14:20 CEST, cancel·lar l'ordre límit pendent."},
    "2026-10-14": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Zona de Londres vàlida de 11:00 a 14:20 CEST. Cancel·lar immediatament si no s'ha tocat a les 14:20 CEST."},
    "2026-11-04": {"type": "FOMC", "severity": "AMBER", "name": "FOMC Meeting (Dia 1)", "time_cest": "Tot el dia", "instructions": "Rang estret previ a la decisió de tipus. Operable a Londres amb normalitat."},
    "2026-11-05": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CET", "instructions": "Decisió de tipus d'interès. Londres operable. Apagar el bot i tancar posicions abans de les 18:00 CET."},
    "2026-11-06": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si encara no s'ha executat."},
    "2026-11-12": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Zona operable fins a les 14:20 CET. Cancel·lar pendents abans de les 14:30 CET."},
    "2026-11-26": {"type": "HOLIDAY", "severity": "GRAY", "name": "Thanksgiving Day", "time_cest": "Tot el dia", "instructions": "CME Globex tancat. Festa operativa."},
    "2026-11-27": {"type": "HOLIDAY", "severity": "GRAY", "name": "Black Friday (Early Close)", "time_cest": "19:00 CET", "instructions": "Tancament anticipat de mercat. Volum baix, no operar."},
    "2026-12-04": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2026-12-10": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2026-12-16": {"type": "FOMC", "severity": "RED", "name": "FOMC + Projeccions SEP (Powell)", "time_cest": "20:00 CET", "instructions": "Reunió trimestral clau de la Fed amb gràfic de punts (dot plot). Apagar el bot completament avui."},
    "2026-12-24": {"type": "HOLIDAY", "severity": "GRAY", "name": "Christmas Eve", "time_cest": "19:15 CET", "instructions": "Tancament anticipat. Sense volum institucional. No operar."},
    "2026-12-25": {"type": "HOLIDAY", "severity": "GRAY", "name": "Nadal", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2026-12-31": {"type": "HOLIDAY", "severity": "GRAY", "name": "Cap d'Any (Early Close)", "time_cest": "Tot el dia", "instructions": "Volum festiu reduït. Mercat sense liquiditat institucional."},

    # --- 2027 ---
    "2027-01-01": {"type": "HOLIDAY", "severity": "GRAY", "name": "Any Nou", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2027-01-08": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-01-13": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-01-18": {"type": "HOLIDAY", "severity": "GRAY", "name": "Martin Luther King Jr. Day", "time_cest": "19:00 CET", "instructions": "Tancament anticipat CME. No operar."},
    "2027-01-27": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CET", "instructions": "Apagar el bot abans de les 18:00 CET."},
    "2027-02-05": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-02-11": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-02-15": {"type": "HOLIDAY", "severity": "GRAY", "name": "Presidents' Day", "time_cest": "19:00 CET", "instructions": "Tancament anticipat CME. No operar."},
    "2027-03-05": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-03-11": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-03-17": {"type": "FOMC", "severity": "RED", "name": "FOMC + SEP (Projeccions)", "time_cest": "19:00 CET", "instructions": "Reunió trimestral clau. Apagar el bot tot el dia."},
    "2027-03-26": {"type": "HOLIDAY", "severity": "GRAY", "name": "Good Friday", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2027-04-02": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-04-14": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-05-05": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CEST", "instructions": "Apagar el bot abans de les 18:00 CEST."},
    "2027-05-07": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-05-12": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-05-31": {"type": "HOLIDAY", "severity": "GRAY", "name": "Memorial Day", "time_cest": "19:00 CEST", "instructions": "Tancament anticipat CME. No operar."},
    "2027-06-04": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-06-10": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-06-16": {"type": "FOMC", "severity": "RED", "name": "FOMC + SEP (Powell)", "time_cest": "20:00 CEST", "instructions": "Reunió trimestral clau. Apagar el bot tot el dia."},
    "2027-07-02": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-07-05": {"type": "HOLIDAY", "severity": "GRAY", "name": "Independence Day (Obs)", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2027-07-14": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-07-28": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CEST", "instructions": "Apagar el bot abans de les 18:00 CEST."},
    "2027-08-06": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-08-11": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-08-27": {"type": "FOMC", "severity": "RED", "name": "Jackson Hole Economic Symposium", "time_cest": "16:00 CEST", "instructions": "Discurs de Powell sobre política monetària a llarg termini. Apagar el bot."},
    "2027-09-03": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-09-06": {"type": "HOLIDAY", "severity": "GRAY", "name": "Labor Day", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2027-09-14": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-09-22": {"type": "FOMC", "severity": "RED", "name": "FOMC + SEP (Powell)", "time_cest": "20:00 CEST", "instructions": "Reunió trimestral clau. Apagar el bot."},
    "2027-10-01": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-10-13": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-11-03": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "19:00 CET", "instructions": "Apagar el bot abans de les 17:00 CET."},
    "2027-11-05": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-11-10": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-11-25": {"type": "HOLIDAY", "severity": "GRAY", "name": "Thanksgiving Day", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2027-11-26": {"type": "HOLIDAY", "severity": "GRAY", "name": "Black Friday", "time_cest": "19:00 CET", "instructions": "Tancament anticipat. No operar."},
    "2027-12-03": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-12-10": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-12-15": {"type": "FOMC", "severity": "RED", "name": "FOMC + SEP (Powell)", "time_cest": "20:00 CET", "instructions": "Reunió trimestral clau. Apagar el bot."},
    "2027-12-24": {"type": "HOLIDAY", "severity": "GRAY", "name": "Christmas Eve", "time_cest": "19:15 CET", "instructions": "Tancament anticipat. No operar."},
    "2027-12-25": {"type": "HOLIDAY", "severity": "GRAY", "name": "Nadal", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."}
}

def is_monthly_opex(dt: datetime.date) -> bool:
    """El tercer divendres de cada mes sempre cau entre el dia 15 i el dia 21."""
    return dt.weekday() == 4 and 15 <= dt.day <= 21

def is_quarter_end(dt: datetime.date) -> bool:
    """Últims dies de Març, Juny, Setembre i Desembre (dies 29 a 31)."""
    return dt.month in (3, 6, 9, 12) and dt.day >= 29

def is_jackson_hole(dt: datetime.date) -> bool:
    """Simposi de la Fed a Jackson Hole (dies 22 a 28 d'agost)."""
    return dt.month == 8 and 22 <= dt.day <= 28

def is_post_holiday_low_liquidity(dt: datetime.date) -> bool:
    """Jornades immediatament posteriors a grans festius amb volum reduït."""
    return (dt.month == 1 and dt.day in (2, 3)) or (dt.month == 7 and dt.day in (5, 6, 7))

def get_macro_event_for_date(target_date: Optional[datetime.date] = None) -> Optional[Dict[str, Any]]:
    """
    Retorna la informació de l'esdeveniment macro si la data indicada està al calendari
    o coincideix amb un filtre estructural (OpEx, Quarter-End, Jackson Hole).
    """
    if target_date is None:
        target_date = datetime.date.today()
        
    date_key = target_date.strftime("%Y-%m-%d")
    if date_key in MACRO_EVENTS:
        return MACRO_EVENTS[date_key]

    # Filtres estructurals automàtics (invariants anuals)
    if is_monthly_opex(target_date):
        return {
            "type": "OPEX",
            "severity": "AMBER",
            "name": "Venciment Mensual d'Opcions (OpEx - 3r Divendres)",
            "time_cest": "Tot el dia",
            "instructions": "Expiració mensual de contractes de derivats CME. Filtre anti-ruïna activat."
        }

    if is_quarter_end(target_date):
        return {
            "type": "REBALANCING",
            "severity": "AMBER",
            "name": "Final de Trimestre (Quarter-End Rebalancing)",
            "time_cest": "Tot el dia",
            "instructions": "Reequilibri massiu de carteres per fons de pensions i institucionals."
        }

    if is_jackson_hole(target_date):
        return {
            "type": "FOMC",
            "severity": "RED",
            "name": "Simposi Econòmic Jackson Hole",
            "time_cest": "Tot el dia",
            "instructions": "Intervenció de política monetària dels bancs centrals."
        }

    if is_post_holiday_low_liquidity(target_date):
        return {
            "type": "HOLIDAY",
            "severity": "GRAY",
            "name": "Sessió Post-Festiva (Baixa Liquiditat)",
            "time_cest": "Tot el dia",
            "instructions": "Volum institucional deprimit post-festiu."
        }

    return None

def get_day_trading_status(target_date: Optional[datetime.date] = None) -> Dict[str, Any]:
    """
    Classifica de manera inequívoca si la jornada és:
    - 'OPERABLE': Llum Verda (Condicions òptimes, 86.3% WR auditat a 1 segon).
    - 'NOT_OPERABLE': Llum Vermella o Groga filtrada (Preservació de capital estricta).
    """
    if target_date is None:
        target_date = datetime.date.today()

    date_str = target_date.strftime("%d/%m/%Y")
    is_weekend = target_date.weekday() >= 5  # 5=Dissabte, 6=Diumenge

    # 1. Cap de Setmana
    if is_weekend:
        day_name = "Dissabte" if target_date.weekday() == 5 else "Diumenge"
        return {
            "date": target_date,
            "date_str": date_str,
            "status": "NOT_OPERABLE",
            "can_trade": False,
            "severity": "GRAY",
            "color_name": "danger",
            "badge": "🔴 NO OPERAR (CAP DE SETMANA)",
            "title": f"MERCAT TANCAT — {day_name} {date_str}",
            "headline": f"Mercat CME Globex tancat ({day_name}).",
            "instructions": "Cap de setmana. El mercat romandrà tancat fins diumenge a la nit.",
            "time_window": "Mercat tancat",
            "event": None,
            "is_weekend": True,
            "is_holiday": False
        }

    event = get_macro_event_for_date(target_date)

    # 2. Esdeveniment de Risc al Calendari (Festiu, FOMC, CPI, NFP, OpEx, Quarter-End)
    if event:
        severity = event.get("severity", "AMBER")
        event_name = event.get("name", "Esdeveniment Macro")
        time_str = event.get("time_cest", "Hora no fixada")
        instructions = event.get("instructions", "")

        return {
            "date": target_date,
            "date_str": date_str,
            "status": "NOT_OPERABLE",
            "can_trade": False,
            "severity": severity,
            "color_name": "danger",
            "badge": f"🔴 NO OPERAR ({event.get('type', 'FILTRE')})",
            "title": f"FILTRE DE SEGURETAT — {date_str}",
            "headline": f"{event_name} ({time_str})",
            "instructions": f"Filtre de preservació de capital activat per {event_name}. Avui no s'opera.",
            "time_window": "Sense operativa (Filtre activat)",
            "event": event,
            "is_weekend": False,
            "is_holiday": severity == "GRAY"
        }

    # 3. Dia 100% Netejat i Valitat (Llum Verda)
    return {
        "date": target_date,
        "date_str": target_date.strftime("%d/%m/%Y"),
        "status": "OPERABLE",
        "can_trade": True,
        "severity": "GREEN",
        "color_name": "success",
        "badge": "🟢 OPERAR (LLUM VERDA)",
        "title": f"ZONES LONDRES · {date_str}",
        "headline": "Sessió neta de notícies d'impacte institucional.",
        "instructions": "Condicions òptimes de Londres (11:00 a 15:20 CEST). Executar ordres límit a High/Low.",
        "time_window": "11:00 a 15:20 CEST",
        "event": None,
        "is_weekend": False,
        "is_holiday": False
    }

