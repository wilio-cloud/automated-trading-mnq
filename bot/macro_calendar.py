"""
Base de Dades del Calendari Macroeconòmic Institucional (2026 - 2027)
Filtre de Risc per a CME Globex MNQ
"""

import datetime
from typing import Optional, Dict, Any

MACRO_EVENTS = {
    # --- 2026 ---
    "2026-09-16": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CEST", "instructions": "Decisió de tipus de la Fed. Apagar el bot abans de les 18:00 CEST."},
    "2026-10-02": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Sessió de Londres normal al matí. Si no s'ha tocat a les 14:20 CEST, cancel·lar l'ordre límit pendent."},
    "2026-10-14": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Zona de Londres vàlida de 11:00 a 14:20 CEST. Cancel·lar immediatament si no s'ha tocat a les 14:20 CEST."},
    "2026-11-04": {"type": "FOMC", "severity": "RED", "name": "FOMC Meeting (Dia 1)", "time_cest": "Tot el dia", "instructions": "Rang estret previ a la decisió de tipus. Operar amb màxima prudència."},
    "2026-11-05": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CET", "instructions": "Decisió de tipus d'interès. Apagar el bot abans de les 18:00 CET."},
    "2026-11-06": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si encara no s'ha executat."},
    "2026-11-12": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Zona operable fins a les 14:20 CET. Cancel·lar pendents abans de les 14:30 CET."},
    "2026-11-26": {"type": "HOLIDAY", "severity": "GRAY", "name": "Thanksgiving Day", "time_cest": "Tot el dia", "instructions": "CME Globex tancat. Festa operativa."},
    "2026-11-27": {"type": "HOLIDAY", "severity": "GRAY", "name": "Black Friday (Early Close)", "time_cest": "19:00 CET", "instructions": "Tancament anticipat de mercat. Volum baix, no operar."},
    "2026-12-04": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2026-12-10": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2026-12-16": {"type": "FOMC", "severity": "RED", "name": "FOMC + Projeccions SEP (Powell)", "time_cest": "20:00 CET", "instructions": "Reunió trimestral clau de la Fed. Apagar el bot completament."},
    "2026-12-24": {"type": "HOLIDAY", "severity": "GRAY", "name": "Christmas Eve", "time_cest": "19:15 CET", "instructions": "Tancament anticipat. Sense volum institucional."},
    "2026-12-25": {"type": "HOLIDAY", "severity": "GRAY", "name": "Nadal", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},

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
    "2027-03-17": {"type": "FOMC", "severity": "RED", "name": "FOMC + SEP (Projeccions)", "time_cest": "19:00 CET", "instructions": "Apagar el bot tot el dia."},
    "2027-03-26": {"type": "HOLIDAY", "severity": "GRAY", "name": "Good Friday", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2027-04-02": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-04-14": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-05-05": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CEST", "instructions": "Apagar el bot abans de les 18:00 CEST."},
    "2027-05-07": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-05-12": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-05-31": {"type": "HOLIDAY", "severity": "GRAY", "name": "Memorial Day", "time_cest": "19:00 CEST", "instructions": "Tancament anticipat CME. No operar."},
    "2027-06-04": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-06-10": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-06-16": {"type": "FOMC", "severity": "RED", "name": "FOMC + SEP (Powell)", "time_cest": "20:00 CEST", "instructions": "Reunió trimestral clau. Apagar el bot."},
    "2027-07-02": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-07-05": {"type": "HOLIDAY", "severity": "GRAY", "name": "Independence Day (Obs)", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2027-07-14": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-07-28": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CEST", "instructions": "Apagar el bot abans de les 18:00 CEST."},
    "2027-08-06": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-08-11": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-08-27": {"type": "FOMC", "severity": "AMBER", "name": "Jackson Hole Symposium", "time_cest": "16:00 CEST", "instructions": "Discurs de Powell. Alta volatilitat."},
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

def get_macro_event_for_date(target_date: Optional[datetime.date] = None) -> Optional[Dict[str, Any]]:
    """
    Retorna la informació de l'esdeveniment macro si la data indicada està al calendari.
    """
    if target_date is None:
        target_date = datetime.date.today()
        
    date_key = target_date.strftime("%Y-%m-%d")
    return MACRO_EVENTS.get(date_key, None)
