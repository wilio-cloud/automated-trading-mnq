#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/guillemriusviladomiu/.gemini/workspaces-antigravity/backtest-master-pro-2026')
from engine.backtester import NQZonesBacktester
import pandas as pd

engine = NQZonesBacktester('/Users/guillemriusviladomiu/.gemini/antigravity/scratch/nq_5m_recent.csv', tp_points=15, sl_points=50)
trades = engine.run()

print("=== DESGLOSSAMENT PER ZONA (TP: 15, SL: 50) ===")
for zone, grp in trades.groupby('zone'):
    wins = len(grp[grp['pnl_pts'] > 0])
    losses = len(grp[grp['pnl_pts'] < 0])
    wr = wins / len(grp) * 100
    pnl = grp['pnl_usd'].sum()
    print(f"  {zone:12s} | Trades: {len(grp):2d} | WR: {wr:5.1f}% ({wins}W / {losses}L) | Net PnL: ${pnl:8.2f}")

print("\n=== DESGLOSSAMENT PER TIPUS D'OPERACIÓ (LONG vs SHORT) ===")
for ttype, grp in trades.groupby('type'):
    wins = len(grp[grp['pnl_pts'] > 0])
    losses = len(grp[grp['pnl_pts'] < 0])
    wr = wins / len(grp) * 100
    pnl = grp['pnl_usd'].sum()
    print(f"  {ttype:6s} | Trades: {len(grp):2d} | WR: {wr:5.1f}% ({wins}W / {losses}L) | Net PnL: ${pnl:8.2f}")
