import datetime
import logging
from typing import Optional

logger = logging.getLogger("ContractResolver")

# Mesos de venciment de contractes de futurs CME per a Equity Indices
# H = Març, M = Juny, U = Setembre, Z = Desembre
EXPIRATION_MONTH_CODES = {
    3: "H",
    6: "M",
    9: "U",
    12: "Z"
}

def get_current_front_month_code(now: Optional[datetime.datetime] = None) -> str:
    """
    Retorna el codi del contracte actiu de futurs (ex: MNQU6 per a Setembre 2026).
    El roll institucional d'Equity Index CME es produeix habitualment
    el segon dijous del mes de venciment (una setmana abans del 3r divendres).
    """
    if now is None:
        now = datetime.datetime.now()

    year = now.year
    month = now.month
    day = now.day

    # Identificar el trimestre
    # Març (3), Juny (6), Setembre (9), Desembre (12)
    quarters = [3, 6, 9, 12]
    
    # Trobar el proper mes de venciment
    target_month = None
    target_year = year

    for qm in quarters:
        if month < qm:
            target_month = qm
            break
        elif month == qm:
            # Si estem en el mes de venciment, comprovem si ja hem passat la data de roll (~dia 10-14)
            # El roll del CME sol ser el segon dijous del mes
            if day < 12:
                target_month = qm
            else:
                # Ja hem fet el roll al següent trimestre
                pass
            break

    if target_month is None:
        # Passat el roll de desembre, mirem març de l'any vinent
        if month == 12 and day >= 12:
            target_month = 3
            target_year = year + 1
        else:
            # Buscar el proper després de month
            for qm in quarters:
                if qm > month:
                    target_month = qm
                    break
            if target_month is None:
                target_month = 3
                target_year = year + 1

    month_code = EXPIRATION_MONTH_CODES[target_month]
    year_digit = str(target_year)[-1]  # Ex: 6 per a 2026
    
    return f"MNQ{month_code}{year_digit}"

def resolve_active_contract(client=None, symbol_base: str = "MNQ") -> str:
    """
    Intenta resoldre el contracte actiu directament consultant Tradovate API.
    Si falla o no hi ha client disponible, utilitza el càlcul algorítmic.
    """
    if client:
        try:
            suggested = client.suggest_contract(symbol_base)
            if suggested:
                logger.info(f"Contracte actiu resolt per Tradovate API: {suggested}")
                return suggested
        except Exception as e:
            logger.warning(f"No s'ha pogut resoldre per API Tradovate ({e}), usant resolució de calendari.")

    fallback_symbol = get_current_front_month_code()
    logger.info(f"Contracte actiu per calendari: {fallback_symbol}")
    return fallback_symbol

if __name__ == "__main__":
    print(f"Active MNQ Contract: {get_current_front_month_code()}")
