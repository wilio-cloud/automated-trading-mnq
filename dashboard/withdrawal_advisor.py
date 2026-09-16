"""
Mòdul de Recomanació Intel·ligent de Retirades Mensuals de Capital
"""

from typing import Dict, Any

def calculate_withdrawal_advice(current_balance: float, initial_deposit: float = 1000.0) -> Dict[str, Any]:
    """
    Calcula la recomanació mensual de retirada en funció del saldo real del compte a Tradovate
    i dels marges de drawdown de l'estratègia.
    """
    current_balance = max(0.0, float(current_balance))
    net_profit = current_balance - initial_deposit
    
    # Fase 1: Acumulació Inicial (< $2.200)
    if current_balance < 2200.0:
        recommended_monthly = 0.0
        phase = "Fase 1: Acumulació de Coixí Inicial"
        phase_color = "amber"
        message = (
            "Estem en la fase d'acumulació crítica. Es recomana no retirar diners encara "
            f"per assolir amb seguretat els 2.200$ i poder escalar a 2 MNQ sense risc."
        )
        buffer_status = "Construint matalàs"
        safe_contracts = 1
        pct_recommended = 0.0

    # Fase 2: Escalat Intermedi ($2.200 a $5.000)
    elif current_balance < 5000.0:
        # Recomanar retirar un 25% del benefici per sobre de 2.200$, aprox 200$-400$/mes
        surplus = current_balance - 2200.0
        recommended_monthly = round(min(400.0, surplus * 0.20), 2)
        phase = "Fase 2: Consolidació i Escalat (2 a 3 MNQ)"
        phase_color = "blue"
        message = (
            f"El compte ja té un matalàs sòlid. Pots retirar aproximadament ${recommended_monthly:,.2f} USD "
            "aquest mes com a recompensa, mantenint intacte el coixí per operar 2-3 MNQ."
        )
        buffer_status = "Matalàs en expansió"
        safe_contracts = 2 if current_balance < 3500 else 3
        pct_recommended = 20.0

    # Fase 3: Renda Plena i Escalat Institucional ($5.000 a $15.000)
    elif current_balance < 15000.0:
        # Recomanar 50% dels guanys mensuals típics (~$1.200 - $1.800/mes)
        recommended_monthly = 1500.0
        phase = "Fase 3: Renda Plena Institucional (4 a 5 MNQ)"
        phase_color = "emerald"
        message = (
            f"Compte fortament consolidat. Es recomana retirar **$1.500,00 USD** aquest mes "
            "directament cap al teu banc. El compte continuarà creixent amb el 50% restant del benefici."
        )
        buffer_status = "Matalàs institucional excel·lent"
        safe_contracts = 5
        pct_recommended = 50.0

    # Fase 4: Mode Búnquer de Renda (> $15.000)
    else:
        # Recomanar 70% dels guanys mensuals típics (~$2.000 - $2.500/mes)
        recommended_monthly = 2200.0
        phase = "Fase 4: Búnquer de Renda i Independència (> $15.000)"
        phase_color = "purple"
        message = (
            f"Matalàs indestructible (> $15.000). Es recomana extreure **$2.200,00 USD al mes** com a sou fix. "
            "El saldo al broker supera amb escreix 20 vegades el drawdown màxim històric."
        )
        buffer_status = "Búnquer de seguretat màxima"
        safe_contracts = 5
        pct_recommended = 70.0

    # Mètriques de seguretat
    margin_distance = current_balance - (safe_contracts * 100.0)  # Distància al marge mínim Tradovate
    drawdown_cushion_x = round(current_balance / 729.0, 1)  # Quants Max DD històrics aguanta el compte

    return {
        "current_balance": current_balance,
        "initial_deposit": initial_deposit,
        "net_profit": net_profit,
        "phase": phase,
        "phase_color": phase_color,
        "recommended_monthly_withdrawal": recommended_monthly,
        "percentage_of_gains": pct_recommended,
        "message": message,
        "safe_contracts": safe_contracts,
        "buffer_status": buffer_status,
        "margin_distance": max(0.0, margin_distance),
        "drawdown_cushion_multiples": drawdown_cushion_x,
        "historical_max_dd": 729.0
    }
