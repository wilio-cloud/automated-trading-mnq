"""
Motor de Simulació i Projeccions Multitemporals
Genera corbes mensuals precises per a 1A, 5A i 10A sobre les 3 estratègies validades.
"""

from typing import Dict, Any, List

STRATEGIES_METADATA = {
    "london_only": {
        "id": "london_only",
        "name": "🇬🇧 Només Londres (Sweet Spot)",
        "badge": "Recomanada Institucional",
        "badge_color": "emerald",
        "win_rate": 94.27,
        "profit_factor": 2.74,
        "tp_points": 10.0,
        "sl_points": 60.0,
        "trades_per_year": 419,
        "monthly_trades": 35,
        "expectancy_pts": 5.989,
        "net_per_trade_1mnq": 10.48,
        "monthly_net_1mnq": 366.80,
        "max_dd_1mnq": 272.0,
        "max_dd_5mnq": 729.0,
        "description": "L'estratègia reina del backtest. Opera exclusivament els nivells de London High i London Low amb 1 sol trade per nivell."
    },
    "all_sessions": {
        "id": "all_sessions",
        "name": "🌐 Àsia + Londres (All Sessions)",
        "badge": "Major Volum",
        "badge_color": "blue",
        "win_rate": 89.20,
        "profit_factor": 1.95,
        "tp_points": 10.0,
        "sl_points": 60.0,
        "trades_per_year": 838,
        "monthly_trades": 70,
        "expectancy_pts": 2.44,
        "net_per_trade_1mnq": 3.38,
        "monthly_net_1mnq": 236.60,
        "max_dd_1mnq": 480.0,
        "max_dd_5mnq": 1350.0,
        "description": "Inclou tant els nivells d'Àsia (00:00 EDT) com els de Londres (05:00 EDT). Duplica el nombre d'operacions diàries."
    },
    "apex_compliant": {
        "id": "apex_compliant",
        "name": "🛡️ Apex Legacy Compliant (TP 12 / SL 50)",
        "badge": "Ràtio 4,17:1 Legal",
        "badge_color": "indigo",
        "win_rate": 89.50,
        "profit_factor": 2.12,
        "tp_points": 12.0,
        "sl_points": 50.0,
        "trades_per_year": 419,
        "monthly_trades": 35,
        "expectancy_pts": 5.49,
        "net_per_trade_1mnq": 9.48,
        "monthly_net_1mnq": 331.80,
        "max_dd_1mnq": 280.0,
        "max_dd_5mnq": 820.0,
        "description": "Configuració amb marge de seguretat per a comptes finançats que prohibeixen ràtios R:R superiors a 5:1 (Apex PA Legacy)."
    }
}

def generate_projections(
    strategy_id: str = "london_only",
    horizon_years: int = 5,
    initial_balance: float = 1000.0
) -> Dict[str, Any]:
    """
    Genera la trajectòria mes a mes de cadascun dels 4 escenaris per a l'horitzó sol·licitat (1, 5 o 10 anys).
    """
    strat = STRATEGIES_METADATA.get(strategy_id, STRATEGIES_METADATA["london_only"])
    total_months = horizon_years * 12
    monthly_net_1mnq = strat["monthly_net_1mnq"]
    
    months_labels = [f"M{m}" if total_months > 24 else f"Mes {m}" for m in range(total_months + 1)]
    if horizon_years == 1:
        months_labels = ["Inici", "Gen", "Feb", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Des"]

    # 1. Escenari Renda / Sou Mensual (Recomanat)
    # Any 1 creix fins a 5 MNQ. A partir d'Any 2 retira una renda mensual fixa deixant coixí creixent
    income_balance = [initial_balance]
    income_withdrawn_accum = [0.0]
    income_total_value = [initial_balance]
    curr_income_cap = initial_balance
    curr_withdrawn = 0.0

    # 2. Escenari Re-inversió Total Compost (Fins a 50 MNQ / 5 NQ)
    comp_balance = [initial_balance]
    curr_comp_cap = initial_balance

    # 3. Escenari Desgast de Mercat (Win Rate cau ~3.5%)
    decay_balance = [initial_balance]
    curr_decay_cap = initial_balance
    decay_monthly_1mnq = monthly_net_1mnq * 0.55  # ~45% menys de rendiment per desgast

    # 4. Escenari Conservador Fixe (Màxim 3 MNQ per sempre)
    cons_balance = [initial_balance]
    curr_cons_cap = initial_balance

    for m in range(1, total_months + 1):
        year_num = ((m - 1) // 12) + 1

        # --- Model 1: Renda / Sou Mensual ---
        if year_num == 1:
            contracts = max(1, min(int(curr_income_cap // 1500), 5))
            month_gain = contracts * monthly_net_1mnq
            withdrawal = 0.0
        else:
            contracts = 5
            month_gain = contracts * monthly_net_1mnq
            # Retirar sou si el compte té coixí (> $10.000)
            if curr_income_cap > 10000.0:
                withdrawal = min(1500.0, month_gain * 0.70)
            else:
                withdrawal = 0.0

        curr_income_cap += (month_gain - withdrawal)
        curr_withdrawn += withdrawal
        income_balance.append(round(curr_income_cap, 2))
        income_withdrawn_accum.append(round(curr_withdrawn, 2))
        income_total_value.append(round(curr_income_cap + curr_withdrawn, 2))

        # --- Model 2: Re-inversió Total Compost ---
        # 1 MNQ per cada $1.500 de coixí, amb sostre a 50 MNQ (5 NQ)
        contracts_comp = max(1, min(int(curr_comp_cap // 1500), 50))
        gain_comp = contracts_comp * monthly_net_1mnq
        curr_comp_cap += gain_comp
        comp_balance.append(round(curr_comp_cap, 2))

        # --- Model 3: Desgast de Mercat ---
        contracts_decay = max(1, min(int(curr_decay_cap // 1500), 5))
        gain_decay = contracts_decay * decay_monthly_1mnq
        curr_decay_cap += gain_decay
        decay_balance.append(round(curr_decay_cap, 2))

        # --- Model 4: Conservador Fixe (Max 3 MNQ) ---
        contracts_cons = max(1, min(int(curr_cons_cap // 1500), 3))
        gain_cons = contracts_cons * monthly_net_1mnq
        curr_cons_cap += gain_cons
        cons_balance.append(round(curr_cons_cap, 2))

    return {
        "strategy": strat,
        "horizon_years": horizon_years,
        "total_months": total_months,
        "labels": months_labels,
        "scenarios": {
            "income": {
                "id": "income",
                "name": "💵 Model Sou / Renda (5 MNQ Fixe + Retirades)",
                "color": "#10b981",  # Esmeralda
                "balance": income_balance,
                "withdrawn_accum": income_withdrawn_accum,
                "total_value": income_total_value,
                "final_balance": income_balance[-1],
                "final_withdrawn": income_withdrawn_accum[-1],
                "final_total_value": income_total_value[-1],
                "description": "Any 1 acumulació fins a 5 MNQ. Després es retiren ~1.500$/mes cap al banc i el capital continua acumulant coixí."
            },
            "compounded": {
                "id": "compounded",
                "name": "🚀 Re-inversió Total Compost (Sostre 5 NQ)",
                "color": "#3b82f6",  # Blau elèctric
                "balance": comp_balance,
                "final_balance": comp_balance[-1],
                "description": "Re-inversió del 100% afegint contractes fins a 50 MNQ (5 NQ) sense cap retirada."
            },
            "realistic_decay": {
                "id": "realistic_decay",
                "name": "⚠️ Desgast de Mercat (WR 90% + Slippage)",
                "color": "#f59e0b",  # Ambre / Taronja
                "balance": decay_balance,
                "final_balance": decay_balance[-1],
                "description": "Suposa que en el futur el mercat es torna més caòtic i el Win Rate cau un 4% amb slippage afegit."
            },
            "conservative": {
                "id": "conservative",
                "name": "🛡️ Conservador Fixe (Màxim 3 MNQ per sempre)",
                "color": "#8b5cf6",  # Violeta
                "balance": cons_balance,
                "final_balance": cons_balance[-1],
                "description": "Sostre rígid a 3 MNQ. Risc mínim, zero estrès emocional i drawdown màxim inferior a 850$."
            }
        }
    }
