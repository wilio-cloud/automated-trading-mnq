import datetime
import logging
import time
from typing import Optional, Dict, Any
import pytz

from bot.config import config
from bot.tradovate_client import tradovate_client
from bot.contract_resolver import resolve_active_contract
from bot.zone_calculator import zone_calculator
from bot.risk_manager import risk_manager
from bot.notifier import notifier
from bot.daily_briefing import generate_and_send_briefing
from bot.macro_calendar import get_macro_event_for_date

logger = logging.getLogger("Strategy")

class LondonZonesStrategy:
    def __init__(self):
        self.tz = pytz.timezone(config.timezone)
        self.tz_madrid = pytz.timezone("Europe/Madrid")
        self.current_trading_date: Optional[datetime.date] = None
        self.briefing_sent: bool = False
        self.orders_placed: bool = False
        self.amber_cleaned: bool = False
        self.eod_cleaned: bool = False
        
        # Estat diari
        self.active_symbol: Optional[str] = None
        self.london_high: Optional[float] = None
        self.london_low: Optional[float] = None
        self.short_order_id: Optional[int] = None
        self.long_order_id: Optional[int] = None

    def reset_for_new_day(self, today: datetime.date):
        """Reinicia l'estat per a una nova jornada operativa."""
        self.current_trading_date = today
        self.briefing_sent = False
        self.orders_placed = False
        self.amber_cleaned = False
        self.eod_cleaned = False
        self.active_symbol = None
        self.london_high = None
        self.london_low = None
        self.short_order_id = None
        self.long_order_id = None
        logger.info(f"🔄 Estat reiniciat per a la jornada: {today}")

    def on_london_close(self, now: datetime.datetime):
        """
        Es crida exactament a les 05:00 EDT (11:00 CEST) quan finalitza la sessió de Londres.
        Calcula els nivells institucionals i col·loca les dues ordres OSO a Tradovate.
        """
        if self.orders_placed:
            logger.info("Les ordres d'avui ja han estat col·locades prèviament.")
            return

        today = now.date()
        # Verificar que sigui dia laborable (dilluns=0 a divendres=4)
        if today.weekday() >= 5:
            logger.info(f"Cap de setmana detectat ({today}). Mercat CME tancat.")
            return

        # 1. Assegurar autenticació
        is_auth = tradovate_client.authenticate()
        if not is_auth and config.tradovate_env == "live":
            notifier.send("ERROR CRÍTIC TRADOVATE", "No s'ha pogut autenticar amb Tradovate!", color="danger")
            return

        # 2. Resoldre el contracte actiu (ex: MNQU6, MNQZ6)
        self.active_symbol = resolve_active_contract(tradovate_client, config.symbol_base)
        logger.info(f"Símbol operatiu seleccionat: {self.active_symbol}")

        # 3. Consultar saldo i calcular mida de posició
        cash_balance = tradovate_client.get_cash_balance()
        contracts = risk_manager.calculate_contracts(cash_balance)
        
        if not risk_manager.validate_margin(cash_balance, contracts):
            logger.error("Risc: Marge insuficient. Ordres no enviades.")
            return

        # 4. Calcular London High i London Low
        self.london_high, self.london_low = zone_calculator.calculate_london_range(
            date=today,
            tradovate_client=tradovate_client,
            symbol=self.active_symbol
        )

        if self.london_high is None or self.london_low is None:
            err = f"❌ Error: No s'han pogut determinar els nivells de Londres per al dia {today}."
            logger.error(err)
            notifier.send("ERROR DE ZONES", err, color="danger")
            return

        # 5. Càlcul de preus de l'estratègia (TP Dinàmic segons cota NQ, SL Invariant 60 pts)
        # Regla quantitativa validada: NQ < 21.000 pts -> TP 8 pts; NQ >= 21.000 pts -> TP 10 pts
        dynamic_tp = 8.0 if self.london_high < 21000.0 else config.tp_points
        dynamic_sl = config.sl_points

        # Zona Alta: Sell Limit @ High
        short_entry = self.london_high
        short_tp = round(short_entry - dynamic_tp, 2)
        short_sl = round(short_entry + dynamic_sl, 2)

        # Zona Baixa: Buy Limit @ Low
        long_entry = self.london_low
        long_tp = round(long_entry + dynamic_tp, 2)
        long_sl = round(long_entry - dynamic_sl, 2)

        # 6. Col·locació d'ordres OSO a Tradovate
        regime_str = "< 21.000 pts (TP 8 pts)" if self.london_high < 21000.0 else "≥ 21.000 pts (TP 10 pts)"
        notifier.send(
            "🇬🇧 ZONES DE LONDRES CALCULADES",
            f"**Data**: {today}\n"
            f"**Contracte**: `{self.active_symbol}`\n"
            f"**Règim NQ**: `{regime_str}`\n\n"
            f"🔴 **SHORT (London High)**: `{short_entry:.2f}`\n"
            f"   • Take Profit: `{short_tp:.2f}` (+{dynamic_tp:.1f} pts)\n"
            f"   • Stop Loss:   `{short_sl:.2f}` (-{dynamic_sl:.1f} pts)\n\n"
            f"🟢 **LONG (London Low)**: `{long_entry:.2f}`\n"
            f"   • Take Profit: `{long_tp:.2f}` (+{dynamic_tp:.1f} pts)\n"
            f"   • Stop Loss:   `{long_sl:.2f}` (-{dynamic_sl:.1f} pts)\n\n"
            f"🎯 _Ordres límit col·locades. Gestió activa de la sessió._",
            color="info"
        )

        # Enviar Short OSO
        short_res = tradovate_client.place_bracket_order(
            symbol=self.active_symbol,
            action="Sell",
            qty=contracts,
            entry_price=short_entry,
            tp_price=short_tp,
            sl_price=short_sl
        )
        if short_res:
            self.short_order_id = short_res.get("orderId")

        # Enviar Long OSO
        long_res = tradovate_client.place_bracket_order(
            symbol=self.active_symbol,
            action="Buy",
            qty=contracts,
            entry_price=long_entry,
            tp_price=long_tp,
            sl_price=long_sl
        )
        if long_res:
            self.long_order_id = long_res.get("orderId")

        self.orders_placed = True
        logger.info("✅ Ordres OSO col·locades correctament al mercat.")

    def on_eod_close(self, now: datetime.datetime):
        """
        Es crida a les 16:55 EDT (22:55 CEST) per netejar ordres pendents i tancar qualsevol posició.
        """
        if self.eod_cleaned:
            return

        logger.info("⏰ Executant protocol de tancament EOD CME (16:55 EDT)...")
        
        # 1. Cancel·lar totes les ordres pendents
        canceled = tradovate_client.cancel_all_pending_orders()
        
        # 2. Tancar/aplanar posicions obertes
        tradovate_client.close_all_positions(symbol=self.active_symbol)

        # 3. Consultar balanç final
        final_balance = tradovate_client.get_cash_balance()

        notifier.send(
            "🌙 TANCAMENT EOD CME (16:55 EDT)",
            f"**Jornada completada**: {now.date()}\n"
            f"• Ordres límit no tocades cancel·lades: {canceled}\n"
            f"• Posicions aplanades (Flatten) abans de l'overnight.",
            color="warning"
        )

        self.eod_cleaned = True

    def process_tick(self, now: Optional[datetime.datetime] = None):
        """
        Rutina periòdica d'avaluació segons l'hora actual (America/New_York).
        """
        if now is None:
            now = datetime.datetime.now(self.tz)

        today = now.date()

        # Nou dia?
        if self.current_trading_date != today:
            self.reset_for_new_day(today)

        hour = now.hour
        minute = now.minute

        # 0. Briefing Matinal a Discord a les 10:00 CEST (dilluns a divendres)
        now_madrid = now.astimezone(self.tz_madrid) if now else datetime.datetime.now(self.tz_madrid)
        if now_madrid.date().weekday() < 5:
            if now_madrid.hour == 10 and not self.briefing_sent:
                generate_and_send_briefing(now_madrid.date())
                self.briefing_sent = True

        macro = get_macro_event_for_date(today)
        is_fomc = macro and macro.get("type") == "FOMC"
        is_amber = macro and macro.get("severity") == "AMBER"

        # 1. Moment de col·locació d'ordres (a partir de les 05:00 EDT / 11:00 CEST)
        is_after_london = (hour > config.london_end_hour) or (hour == config.london_end_hour and minute >= config.london_end_minute)
        can_trade_now = not (is_fomc and now_madrid.hour >= 18) and (hour < config.eod_close_hour)

        if is_after_london and can_trade_now:
            if not self.orders_placed:
                self.on_london_close(now)

        # 2. Cancel·lació de protecció en dies AMBER (CPI / NFP) a les 14:20 CEST si no s'ha omplert l'ordre
        if is_amber and (now_madrid.hour > 14 or (now_madrid.hour == 14 and now_madrid.minute >= 20)):
            if self.orders_placed and not self.amber_cleaned:
                logger.info("⚠️ Notícia AMBER detectada: Cancel·lant ordres límit pendents abans de les 14:30...")
                tradovate_client.cancel_all_pending_orders()
                notifier.send(
                    "⚠️ CANCEL·LACIÓ PRE-NOTÍCIA (14:20 CEST)",
                    f"**Esdeveniment**: {macro.get('name')}\n"
                    f"• Ordres límit no tocades retirades abans de la publicació de dades (14:30).\n"
                    f"• Prevenció de fuetades de liquiditat i slippage violent.",
                    color="warning"
                )
                self.amber_cleaned = True

        # 3. Tancament anticipat per a dies de FOMC (18:00 CEST)
        if is_fomc and now_madrid.hour >= 18:
            if not self.eod_cleaned:
                logger.info("⏰ Tancament anticipat de seguretat FOMC a les 18:00 CEST...")
                self.on_eod_close(now)

        # 4. Tancament EOD estàndard CME (16:55 EDT)
        if hour == config.eod_close_hour and minute >= config.eod_close_minute:
            if not self.eod_cleaned:
                self.on_eod_close(now)

strategy = LondonZonesStrategy()
