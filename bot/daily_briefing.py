"""
Mòdul de Publicació del Briefing Matinal a Discord (10:00 CEST)
"""

import os
import sys
import datetime
import pytz
import logging

# Assegurar paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.config import config
from bot.notifier import notifier
from bot.contract_resolver import resolve_active_contract
from bot.macro_calendar import get_macro_event_for_date

logger = logging.getLogger("DailyBriefing")

def generate_and_send_briefing(target_date: datetime.date = None) -> bool:
    """
    Genera i envia el missatge del Briefing Matinal a Discord a les 10:00 CEST.
    """
    tz_madrid = pytz.timezone("Europe/Madrid")
    if target_date is None:
        target_date = datetime.datetime.now(tz_madrid).date()

    date_str = target_date.strftime("%d/%m/%Y")
    event = get_macro_event_for_date(target_date)
    active_contract = resolve_active_contract(symbol_base=config.symbol_base)

    if event:
        severity = event.get("severity", "AMBER")
        event_name = event.get("name", "Esdeveniment Macro")
        time_str = event.get("time_cest", "Hora no fixada")
        instructions = event.get("instructions", "")

        if severity == "RED" or event.get("type") == "FOMC":
            title = f"🟡 BRIEFING MATINAL LONDRES — {date_str}"
            status_text = f"🟡 **TANCAMENT ANTICIPAT A LES 18:00 CEST** ({event_name})"
            color_name = "warning"
            
            fed_detail = f"• **De 18:00 a 22:00 CEST**: Prohibit operar durant la decisió de tipus i la roda de premsa de la Fed." if "Rate Decision" in event_name else f"• **Instrucció**: {instructions}"
            time_label = "HORA DE LA DECISIÓ FED" if "Rate Decision" in event_name else "HORA DE L'ESDEVENIMENT"

            desc = (
                f"**🚦 ESTAT DEL DIA**: {status_text}\n"
                f"**🕒 {time_label}**: `{time_str}`\n"
                f"**📦 CONTRACTE ACTIU**: `{active_contract}`\n\n"
                f"**📋 INSTRUCCIONS DEL PROTOCOL**:\n"
                f"• **11:00 CEST**: Es calculen les zones i es col·loquen les ordres límit amb normalitat.\n"
                f"• **11:00 a 18:00 CEST**: Finestra operativa permesa (Londres i matí de Nova York).\n"
                f"• ⛔ **TANCAMENT OBLIGATORI A LES 18:00 CEST**: A les 18:00 CEST es cancel·len totes les ordres pendents i es tanca qualsevol posició oberta (protocol de seguretat).\n"
                f"{fed_detail}\n\n"
                f"🎯 _Pròxim avís: Publicació de zones i nivells exactes a les 11:00 CEST._"
            )
        elif severity == "AMBER":
            title = f"🟡 BRIEFING MATINAL LONDRES — {date_str}"
            status_text = f"🟡 **ALTA PRECAUCIÓ** ({event_name})"
            color_name = "warning"
            desc = (
                f"**🚦 ESTAT DEL DIA**: {status_text}\n"
                f"**🕒 HORA DE LA NOTÍCIA**: `{time_str}`\n"
                f"**📦 CONTRACTE ACTIU**: `{active_contract}`\n\n"
                f"**📋 INSTRUCCIONS DEL PROTOCOL**:\n"
                f"• **11:00 CEST**: Es calcularan les zones de London High i London Low.\n"
                f"• **11:00 a 14:20 CEST**: La sessió és 100% operable i vàlida.\n"
                f"• ⚠️ **REGLA D'OR**: {instructions}\n\n"
                f"🎯 _Pròxim avís: Publicació de zones i nivells exactes a les 11:00 CEST._"
            )
        else: # GRAY / HOLIDAY
            title = f"⚪ BRIEFING MATINAL LONDRES — {date_str}"
            status_text = f"⚪ **FESTIU CME** ({event_name})"
            color_name = "info"
            desc = (
                f"**🚦 ESTAT DEL DIA**: {status_text}\n"
                f"**🕒 HORARI**: `{time_str}`\n"
                f"**📦 CONTRACTE ACTIU**: `{active_contract}`\n\n"
                f"**📋 INSTRUCCIONS DEL PROTOCOL**:\n"
                f"• {instructions}\n"
                f"• Mercat sense liquiditat institucional. No es col·loquen ordres avui."
            )
    else:
        # Dia normal de Llum Verda (85% dels dies)
        title = f"🇬🇧 BRIEFING MATINAL LONDRES — {date_str}"
        color_name = "success"
        desc = (
            f"**🚦 ESTAT DEL DIA**: 🟢 **LLUM VERDA (Condicions Òptimes - 95% WR)**\n"
            f"**📅 CALENDARI**: Dia net sense notícies vermelles d'alt impacte.\n"
            f"**📦 CONTRACTE ACTIU**: `{active_contract}`\n\n"
            f"**📋 INSTRUCCIONS DEL PROTOCOL**:\n"
            f"• **11:00 CEST**: Càlcul de zones institucionals de Londres (High & Low).\n"
            f"• Ordres límit passives: Sell Limit a l'High i Buy Limit al Low.\n"
            f"• Objectiu: **Take Profit +10.0 punts** | **Stop Loss -60.0 punts**.\n"
            f"• **16:55 EDT (22:55 CEST)**: Tancament automàtic EOD CME Globex.\n\n"
            f"🎯 _Pròxim avís: Publicació de zones i nivells exactes a les 11:00 CEST._"
        )

    logger.info(f"Enviant Briefing Matinal per al dia {date_str} a Discord...")
    notifier.send(title, desc, color=color_name)
    return True

if __name__ == "__main__":
    print("Enviant Briefing de prova...")
    generate_and_send_briefing()
