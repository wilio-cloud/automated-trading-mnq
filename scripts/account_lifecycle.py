#!/usr/bin/env python3
"""
Simulació del Cicle de Vida d'un Compte Fondejat de 50K
- Què passa si fem 'Burn & Replace' (anar a saco amb 1 NQ i anar pagant resets)
- Què passa si fem 'Safe Compound' (3 MNQ amb 100% de supervivència)
- Què passa si fem 'Escalat de Coixí' (Buffer scaling: 2 MNQ fins a +$2k de profit, després 4-5 MNQ)
"""

import pandas as pd
import numpy as np

# Load trades from simulation
from funded_simulation import simulate_trades

df = simulate_trades(10, 60, london_only=False)

def simulate_funded_lifecycle(df_trades, sizing_type, eval_cost=40.0, pa_fee=140.0, payout_target=2500.0):
    """
    Simula el cicle de vida:
    - Comença en fase Avaluació (Objectiu +$3,000, Límit DD: $2,000)
    - En aprovar, passa a Compte Fondejat (PA)
    - Cada cop que arriba a payout_target, es retira capital (payout)
    - Si toca -$2,000 de trailing DD, el compte es peta i es reinicia una nova avaluació!
    """
    EVAL_TARGET = 3000.0
    DD_LIMIT = 2000.0
    
    total_evals_bought = 0
    total_pas_paid = 0
    total_payouts_taken = 0.0
    total_accounts_blown = 0
    
    # State
    mode = 'EVAL' # 'EVAL' or 'FUNDED'
    total_evals_bought += 1
    balance = 0.0
    high_water_mark = 0.0
    
    payout_history = []
    
    for idx, row in df_trades.iterrows():
        pts = row['pnl_pts']
        
        # Determine contract size
        if sizing_type == '1_NQ':
            pt_val = 20.0
        elif sizing_type == '3_MNQ':
            pt_val = 6.0
        elif sizing_type == '4_MNQ':
            pt_val = 8.0
        elif sizing_type == 'BUFFER_SCALING':
            # Si estem en EVAL o si tenim poc coixí (<$2,000): 2 MNQ
            # Quan tenim coixí de seguretat (balance > $2,500): 4 MNQ
            if mode == 'EVAL':
                pt_val = 6.0 # 3 MNQ per passar
            else:
                pt_val = 8.0 if balance >= 2500.0 else 4.0
                
        pnl = pts * pt_val
        balance += pnl
        
        if balance > high_water_mark:
            high_water_mark = balance
            
        current_dd = high_water_mark - balance
        
        # Check Fail
        if current_dd >= DD_LIMIT:
            total_accounts_blown += 1
            # Reset
            mode = 'EVAL'
            total_evals_bought += 1
            balance = 0.0
            high_water_mark = 0.0
            continue
            
        # Check Pass Eval
        if mode == 'EVAL' and balance >= EVAL_TARGET:
            mode = 'FUNDED'
            total_pas_paid += 1
            balance = 0.0
            high_water_mark = 0.0
            continue
            
        # Check Payout in Funded mode
        if mode == 'FUNDED' and balance >= payout_target:
            total_payouts_taken += payout_target
            balance -= payout_target # withdraw
            high_water_mark = balance # reset HWM to remaining balance
            
    total_costs = (total_evals_bought * eval_cost) + (total_pas_paid * pa_fee)
    net_profit_in_pocket = total_payouts_taken - total_costs
    
    return {
        'sizing': sizing_type,
        'evals_comprats': total_evals_bought,
        'pas_activats': total_pas_paid,
        'comptes_petats': total_accounts_blown,
        'total_payouts_usd': total_payouts_taken,
        'costos_evals_i_pa': total_costs,
        'benefici_net_butxaca': net_profit_in_pocket
    }

print("="*90)
print("🏦 SIMULACIÓ D'1 ANY COMPLET: ESTRATÈGIA DE COMPTES FONDEJATS (50K - $2.000 DD)")
print("   Cost avaluació: $40 | Taxa activació PA: $140 | Payout per tram: $2.500")
print("="*90)

for s in ['1_NQ', '4_MNQ', '3_MNQ', 'BUFFER_SCALING']:
    res = simulate_funded_lifecycle(df, s)
    print(f"\nModalitat: {res['sizing']}")
    print(f"  • Avaluacions comprades : {res['evals_comprats']}")
    print(f"  • Comptes Fondejats PA  : {res['pas_activats']}")
    print(f"  • Comptes Petats        : {res['comptes_petats']}")
    print(f"  • Total Retirades (Cash): ${res['total_payouts_usd']:,.2f}")
    print(f"  • Despeses (Fees/Resets): ${res['costos_evals_i_pa']:,.2f}")
    print(f"  👉 BENEFICI NET A LA BUTXACA: ${res['benefici_net_butxaca']:,.2f}")
