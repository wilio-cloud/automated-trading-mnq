#!/usr/bin/env python3
import pandas as pd
import numpy as np
from funded_simulation import simulate_trades

combos = [
    ("TP 12 / SL 60 (Límit 5:1)", 12, 60),
    ("TP 10 / SL 50 (Límit 5:1)", 10, 50),
    ("TP 12 / SL 50 (Ràtio 4.17:1)", 12, 50),
    ("TP 15 / SL 60 (Ràtio 4:1)", 15, 60),
    ("TP 15 / SL 50 (Ràtio 3.33:1)", 15, 50),
    ("TP 10 / SL 45 (Ràtio 4.5:1)", 10, 45),
    ("TP 10 / SL 40 (Ràtio 4:1)", 10, 40),
    ("TP 10 / SL 30 (Baseline 3:1)", 10, 30),
]

print("="*95)
print("🛡️ AVALUACIÓ DE CONFIGURACIONS PER A APEX LEGACY (RÀTIO <= 5:1)")
print("="*95)

for london_only in [True, False]:
    mode_name = "NOMÉS LONDRES" if london_only else "ÀSIA + LONDRES"
    print(f"\n📍 MODALITAT: {mode_name}")
    print(f"{'Configuració':30s} | {'Ràtio':7s} | {'WR (%)':7s} | {'PF':5s} | {'PnL 1 NQ':12s} | {'Max DD 1 NQ':12s} | {'PnL 5 MNQ (DD)':18s}")
    print("-" * 105)
    
    for name, tp, sl in combos:
        df_trades = simulate_trades(tp, sl, london_only=london_only)
        n = len(df_trades)
        wins = len(df_trades[df_trades['pnl_pts'] > 0])
        losses = len(df_trades[df_trades['pnl_pts'] < 0])
        wr = wins / n * 100
        
        pts = df_trades['pnl_pts'].sum()
        pnl_1nq = pts * 20.0
        
        # Drawdown 1 NQ
        cum_1nq = (df_trades['pnl_pts'] * 20.0).cumsum()
        dd_1nq = (cum_1nq.cummax() - cum_1nq).max()
        
        # 5 MNQ stats
        pnl_5m = pts * 10.0
        cum_5m = (df_trades['pnl_pts'] * 10.0).cumsum()
        dd_5m = (cum_5m.cummax() - cum_5m).max()
        
        # PF
        w_usd = df_trades[df_trades['pnl_pts'] > 0]['pnl_pts'].sum()
        l_usd = abs(df_trades[df_trades['pnl_pts'] < 0]['pnl_pts'].sum())
        pf = w_usd / l_usd if l_usd > 0 else 999.0
        
        ratio_str = f"{sl/tp:.2f}:1"
        print(f"{name:30s} | {ratio_str:7s} | {wr:5.1f}% | {pf:4.2f} | ${pnl_1nq:10,.0f} | ${dd_1nq:10,.0f} | ${pnl_5m:7,.0f} (${dd_5m:5,.0f})")

