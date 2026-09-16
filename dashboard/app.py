import os
import sys
from pathlib import Path
from typing import Optional

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
from dashboard.simulation_engine import STRATEGIES_METADATA, generate_projections
from dashboard.withdrawal_advisor import calculate_withdrawal_advice

app = FastAPI(
    title="Tradovate MNQ Zones Dashboard",
    description="Terminal Institucional de Projeccions i Seguiment en Temps Real",
    version="1.0.0"
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
            print(f"Error connectant amb Tradovate: {e}")

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
        # Consultar saldo real o simulat
        status = get_live_status()
        balance = status["cash_balance"]
    return calculate_withdrawal_advice(current_balance=balance, initial_deposit=1000.0)

# Servir fitxers estàtics
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    return FileResponse(str(STATIC_DIR / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dashboard.app:app", host="0.0.0.0", port=8000, reload=True)
