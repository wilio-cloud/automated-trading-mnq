import os
import sys
import asyncio
import datetime
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
import pytz

# Assegurar path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from bot.config import config
from bot.tradovate_client import tradovate_client
from bot.contract_resolver import resolve_active_contract
from bot.daily_briefing import generate_and_send_briefing
from bot.macro_calendar import get_day_trading_status
from dashboard.simulation_engine import STRATEGIES_METADATA, generate_projections
from dashboard.withdrawal_advisor import calculate_withdrawal_advice

logger = logging.getLogger("MacroScheduler")

macro_scheduler_state = {
    "last_sent_date": None,
    "last_sent_time": None,
    "is_running": False
}

async def macro_notification_worker():
    """
    Worker asíncron en segon pla que corre al servidor de Railway:
    1. A l'arrencada (dilluns a divendres), envia confirmació d'estat macro a Discord.
    2. Cada dia laborable a les 10:00 CEST (Europe/Madrid), envia el Briefing Matinal.
    """
    tz_madrid = pytz.timezone("Europe/Madrid")
    macro_scheduler_state["is_running"] = True
    logger.info("📅 Planificador Macro actiu per a notificacions a Discord (10:00 CEST).")
    
    # 1. Notificació d'arrencada de Railway (només dies laborables i si no s'ha enviat avui)
    if os.environ.get("TESTING") != "1" and not any("unittest" in arg or "pytest" in arg for arg in sys.argv):
        try:
            now_madrid = datetime.datetime.now(tz_madrid)
            if now_madrid.date().weekday() < 5 and config.discord_webhook_url:
                logger.info("🚀 Enviant estat macro inicial d'arrencada Railway a Discord...")
                sent = generate_and_send_briefing(now_madrid.date(), is_startup=True)
                if sent:
                    macro_scheduler_state["last_sent_date"] = now_madrid.date().isoformat()
                    macro_scheduler_state["last_sent_time"] = now_madrid.isoformat()
        except Exception as e:
            logger.error(f"Error enviant briefing d'arrencada: {e}")

    # 2. Bucle diari a les 10:00 CEST
    while True:
        try:
            now_madrid = datetime.datetime.now(tz_madrid)
            today_date = now_madrid.date()
            
            # Dilluns a divendres (0=dl, 4=dv)
            if today_date.weekday() < 5 and config.discord_webhook_url:
                already_sent_today = (macro_scheduler_state["last_sent_date"] == today_date.isoformat())
                # S'envia a les 10:00 CEST
                if now_madrid.hour == 10 and not already_sent_today:
                    logger.info(f"⏰ Són les {now_madrid.strftime('%H:%M:%S')} CEST. Enviant briefing matinal a Discord...")
                    sent = generate_and_send_briefing(today_date, is_startup=False)
                    if sent:
                        macro_scheduler_state["last_sent_date"] = today_date.isoformat()
                        macro_scheduler_state["last_sent_time"] = now_madrid.isoformat()

            # Comprovar cada 30 segons
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            logger.info("Planificador Macro aturat.")
            macro_scheduler_state["is_running"] = False
            break
        except Exception as e:
            logger.error(f"Error en el bucle del planificador macro: {e}")
            await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = asyncio.create_task(macro_notification_worker())
    yield
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Tradovate MNQ Zones Dashboard",
    description="Terminal Institucional de Projeccions i Seguiment en Temps Real",
    version="1.0.0",
    lifespan=lifespan
)

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"

@app.get("/health")
def health_check():
    tz_madrid = pytz.timezone("Europe/Madrid")
    now_madrid = datetime.datetime.now(tz_madrid)
    day_info = get_day_trading_status(now_madrid.date())
    return {
        "status": "online",
        "service": "MNQ Institutional London Zones Dashboard",
        "strategy": "London Zones Only",
        "macro_status": day_info["status"],
        "macro_badge": day_info["badge"],
        "discord_notifier": "configured" if config.discord_webhook_url else "disabled",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@app.get("/api/london-zones")
def get_london_zones():
    import json
    json_path = STATIC_DIR / "london_zones_data.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 1. API: Estat del Broker en Temps Real
@app.get("/api/status")
def get_live_status():
    """
    Retorna l'estat actual de la connexió a Tradovate, saldo i contracte actiu.
    """
    active_contract = resolve_active_contract(tradovate_client, config.symbol_base)
    
    is_connected = False
    current_balance = 1000.0  # Fallback simulat
    account_spec = config.account_spec or "DEMO-1000"
    
    if config.user and config.password:
        try:
            if tradovate_client.authenticate():
                is_connected = True
                current_balance = tradovate_client.get_cash_balance()
                account_spec = tradovate_client.account_spec or account_spec
        except Exception as e:
            pass

    return {
        "connected": is_connected,
        "environment": config.tradovate_env.upper(),
        "account_spec": account_spec,
        "active_contract": active_contract,
        "cash_balance": current_balance,
        "initial_deposit": 1000.0,
        "symbol_base": config.symbol_base,
        "tp_points": config.tp_points,
        "sl_points": config.sl_points
    }

# 2. API: Llista d'Estratègies
@app.get("/api/strategies")
def get_strategies():
    return STRATEGIES_METADATA

# 3. API: Projeccions Multitemporals
@app.get("/api/projections")
def get_projections(
    strategy: str = Query("london_only", description="ID de l'estratègia"),
    horizon: int = Query(5, description="Horitzó en anys (1, 5, 10)"),
    balance: float = Query(1000.0, description="Capital inicial")
):
    if horizon not in (1, 5, 10):
        horizon = 5
    return generate_projections(strategy_id=strategy, horizon_years=horizon, initial_balance=balance)

# 4. API: Consell de Retirades Mensuals
@app.get("/api/withdrawal-advice")
def get_withdrawal_advice(balance: Optional[float] = Query(None)):
    if balance is None:
        status = get_live_status()
        balance = status["cash_balance"]
    return calculate_withdrawal_advice(current_balance=balance, initial_deposit=1000.0)

# 5. API: Estat del Planificador Macro i Notificacions Discord
@app.get("/api/macro/status")
def get_macro_status():
    tz_madrid = pytz.timezone("Europe/Madrid")
    now_madrid = datetime.datetime.now(tz_madrid)
    day_info = get_day_trading_status(now_madrid.date())
    return {
        "current_time_madrid": now_madrid.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "trading_status": day_info["status"],
        "can_trade": day_info["can_trade"],
        "badge": day_info["badge"],
        "headline": day_info["headline"],
        "instructions": day_info["instructions"],
        "last_sent_date": macro_scheduler_state["last_sent_date"],
        "last_sent_time": macro_scheduler_state["last_sent_time"],
        "scheduler_running": macro_scheduler_state["is_running"],
        "discord_configured": bool(config.discord_webhook_url)
    }

@app.get("/api/macro/send-now")
@app.post("/api/macro/send-now")
def trigger_macro_briefing(force: bool = False):
    tz_madrid = pytz.timezone("Europe/Madrid")
    now_madrid = datetime.datetime.now(tz_madrid)
    sent = generate_and_send_briefing(now_madrid.date(), is_startup=False)
    if sent:
        macro_scheduler_state["last_sent_date"] = now_madrid.date().isoformat()
        macro_scheduler_state["last_sent_time"] = now_madrid.isoformat()
    return {
        "sent": sent,
        "date": str(now_madrid.date()),
        "time": now_madrid.strftime("%H:%M:%S CEST"),
        "status": "delivered" if sent else "not_sent"
    }

# Servir fitxers estàtics
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    return FileResponse(str(STATIC_DIR / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dashboard.app:app", host="0.0.0.0", port=8000, reload=True)
