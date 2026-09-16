#!/usr/bin/env python3
"""
Simulació a 5 Anys (60 Mesos / ~2.100 operacions) de l'Estratègia NQ Zones (Només Londres)
4 Escenaris:
1. Re-inversió Total amb Sostre de Risc (fins a 5 NQ = 50 MNQ)
2. Estrès de Mercat (Win Rate degradat al 86% amb slippage)
3. Model de Renda / Sou Mensual (Retirades de beneficis a partir de l'Any 2)
4. Sostre Cautelós Fixe (Màxim 3 MNQ per sempre)
"""

import numpy as np
import pandas as pd

try:
    from scripts.simulate_tradovate_1000_scaling import trades_df
except ImportError:
    from simulate_tradovate_1000_scaling import trades_df

np.random.seed(42)

TOTAL_YEARS = 5
TRADES_PER_YEAR = len(trades_df)  # 419 trades/any
TOTAL_TRADES = TRADES_PER_YEAR * TOTAL_YEARS  # ~2,095 trades

# Base trades array (pnl_pts)
raw_pnls = trades_df['pnl_pts'].values

def simulate_scenario(name, sizing_fn, win_rate_target=None, withdrawal_fn=None, slippage_pts=0.0):
    """
    Simula 5 anys barra a barra/trade a trade.
    """
    capital = 1000.0
    peak = 1000.0
    max_dd = 0.0
    max_dd_pct = 0.0
    total_withdrawn = 0.0
    total_comm = 0.0
    
    yearly_stats = []
    current_year_pnl = 0.0
    current_year_withdrawn = 0.0
    current_year_comm = 0.0
    current_year_trades = 0
    current_year_wins = 0

    trade_idx = 0
    
    # Repeat the 1-year trades over 5 years (with noise / bootstrap or deterministic sequence)
    # To be rigorous, we repeat the 5 consecutive years, with optional regime degradation
    for year in range(1, TOTAL_YEARS + 1):
        year_start_cap = capital
        y_trades = 0
        y_wins = 0
        y_pnl = 0.0
        y_comm = 0.0
        y_withdrawn = 0.0
        
        for t_in_year in range(TRADES_PER_YEAR):
            base_pts = raw_pnls[t_in_year]
            
            # If stress regime (win_rate_target), randomly degrade some wins into losses
            if win_rate_target is not None:
                # Historical WR is 94.27%
                if base_pts > 0 and np.random.rand() > (win_rate_target / 94.27):
                    # Convert this win to an SL
                    pts = -60.0 - slippage_pts
                else:
                    pts = base_pts - slippage_pts if base_pts > 0 else base_pts - slippage_pts
            else:
                pts = base_pts - slippage_pts
                
            contracts = sizing_fn(capital, year)
            # 1 MNQ = $2.00/pt
            comm_rate = 1.50  # RT per MNQ
            
            gross = pts * 2.0 * contracts
            comm = comm_rate * contracts
            net = gross - comm
            
            capital += net
            y_pnl += net
            y_comm += comm
            y_trades += 1
            if pts > 0:
                y_wins += 1
                
            if capital > peak:
                peak = capital
            dd = peak - capital
            dd_pct = (dd / peak) * 100.0 if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
                
            # Month-end check for withdrawals (roughly every 35 trades)
            if withdrawal_fn and (t_in_year + 1) % 35 == 0:
                withdrawn = withdrawal_fn(capital, year)
                capital -= withdrawn
                y_withdrawn += withdrawn
                total_withdrawn += withdrawn

        yearly_stats.append({
            'year': year,
            'start_cap': year_start_cap,
            'end_cap': capital,
            'net_profit': y_pnl,
            'withdrawn': y_withdrawn,
            'comm': y_comm,
            'trades': y_trades,
            'wr': (y_wins / y_trades) * 100.0,
            'contracts_end': contracts
        })
        
    return {
        'name': name,
        'final_capital': capital,
        'total_withdrawn': total_withdrawn,
        'total_value': capital + total_withdrawn,
        'total_profit': (capital + total_withdrawn) - 1000.0,
        'max_dd': max_dd,
        'max_dd_pct': max_dd_pct,
        'yearly': yearly_stats
    }

# 1. Escenari Compost Institucional (1 MNQ per $1.500 de coixí, fins a 5 NQ = 50 MNQ)
def sizing_compounded(cap, year):
    # Coixí de 1.500$ per contracte MNQ
    qty = int(cap // 1500)
    qty = max(1, min(qty, 50))  # Sostre a 50 MNQ (equivalent a 5 contractes grans NQ)
    return qty

res_comp = simulate_scenario("1. Re-inversió Total (Sostre 5 NQ / 50 MNQ)", sizing_compounded)

# 2. Escenari Estrès (Win Rate baixa a 86%, 1 tick de slippage)
res_stress = simulate_scenario(
    "2. Estrès i Degradació de Mercat (WR 86% + Slippage)", 
    sizing_compounded, 
    win_rate_target=86.0, 
    slippage_pts=0.25
)

# 3. Escenari Renda / Sou Mensual:
# Any 1 creix fins a 15k. A partir d'Any 2, fixem màxim 5 MNQ (o 10 MNQ) i retirem el 60% dels beneficis mensuals
def sizing_income(cap, year):
    if year == 1:
        qty = int(cap // 1500)
        return max(1, min(qty, 5))
    else:
        # A partir d'any 2 operem amb 5 MNQ tranquils
        return 5

def withdraw_income(cap, year):
    if year >= 2:
        # Si el compte està per sobre de 10.000$, retirar 1.500$ mensuals de sou
        if cap > 10000:
            return 1500.0
    return 0.0

res_income = simulate_scenario(
    "3. Model Renda / Sou Mensual (5 MNQ Fixe + $1.500/mes a la butxaca)", 
    sizing_income, 
    withdrawal_fn=withdraw_income
)

# 4. Escenari Ultra-Cautelós (Màxim 3 MNQ per sempre)
def sizing_cautelous(cap, year):
    qty = int(cap // 1500)
    return max(1, min(qty, 3))

res_caut = simulate_scenario("4. Model Ultra-Cautelós (Max 3 MNQ per sempre)", sizing_cautelous)

print("="*90)
print("📊 PROJECCIÓ A 5 ANYS (60 MESOS) - ESTRATÈGIA TRADOVATE MNQ ZONES LONDRES")
print("="*90)

for r in [res_comp, res_stress, res_income, res_caut]:
    print(f"\n🔹 {r['name'].upper()}:")
    print(f"   • Saldo en Broker (Any 5):    ${r['final_capital']:,.2f} USD")
    if r['total_withdrawn'] > 0:
        print(f"   • Diners Retirats al Banc:   ${r['total_withdrawn']:,.2f} USD")
    print(f"   • Valor Total Generat:        ${r['total_value']:,.2f} USD")
    print(f"   • Benefici Net Total:         +${r['total_profit']:,.2f} USD")
    print(f"   • Max Drawdown Històric:      -${r['max_dd']:,.2f} USD ({r['max_dd_pct']:.1f}%)")
    print("\n   Evolució Any a Any:")
    print(f"   {'Any':<5} | {'Saldo Inicial':<14} | {'Benefici Net':<14} | {'Retirat':<11} | {'Saldo Final':<14} | {'Contractes':<10}")
    print("   " + "-"*75)
    for y in r['yearly']:
        print(f"   {y['year']:<5} | ${y['start_cap']:>12,.2f} | +${y['net_profit']:>11,.2f} | ${y['withdrawn']:>9,.2f} | ${y['end_cap']:>12,.2f} | {y['contracts_end']} MNQ")

print("\n" + "="*90)
