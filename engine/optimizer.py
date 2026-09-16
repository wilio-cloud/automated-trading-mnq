#!/usr/bin/env python3
"""
NQ Zones Strategy - 2D Parameter Grid Search Optimizer
Optimizes Take Profit (TP) and Stop Loss (SL) across key performance metrics:
- Net PnL ($ and pts)
- Win Rate (%)
- Profit Factor
- Max Drawdown ($)
- Sharpe Ratio / Expectancy ($/trade)
"""

import os
import sys
import pandas as pd
import numpy as np
from engine.backtester import NQZonesBacktester

def optimize(data_path, tp_range, sl_range, output_csv=None):
    engine = NQZonesBacktester(data_path)
    
    results = []
    total_combos = len(tp_range) * len(sl_range)
    print(f"\n🔍 Starting Grid Search: {len(tp_range)} TPs × {len(sl_range)} SLs = {total_combos} combinations")
    
    count = 0
    for tp in tp_range:
        for sl in sl_range:
            count += 1
            engine.run(tp=tp, sl=sl)
            stats = engine.compute_stats()
            
            rr_ratio = round(tp / sl, 2)
            risk_to_reward = round(sl / tp, 2) # e.g. 3.0 for 30 SL / 10 TP
            
            row = {
                'tp_pts': tp,
                'sl_pts': sl,
                'rr_ratio': rr_ratio,
                'risk_mult': risk_to_reward,
                'total_trades': stats['total_trades'],
                'win_rate': stats['win_rate'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'pnl_pts': stats['total_pnl_pts'],
                'pnl_usd': stats['total_pnl_usd'],
                'profit_factor': stats['profit_factor'],
                'max_dd_usd': stats['max_drawdown_usd'],
                'avg_trade_usd': stats['avg_trade_usd']
            }
            results.append(row)
            if count % 10 == 0 or count == total_combos:
                print(f"  [{count}/{total_combos}] TP: {tp:4.1f} | SL: {sl:4.1f} | WR: {stats['win_rate']:5.1f}% | PF: {stats['profit_factor']:4.2f} | PnL: ${stats['total_pnl_usd']:8.2f} | DD: ${stats['max_drawdown_usd']:6.2f}")

    df_res = pd.DataFrame(results)
    
    # Sort by Net PnL USD
    df_sorted = df_res.sort_values(by='pnl_usd', ascending=False).reset_index(drop=True)
    
    if output_csv:
        df_sorted.to_csv(output_csv, index=False)
        print(f"\n💾 Full grid results saved to {output_csv}")
        
    return df_sorted

if __name__ == '__main__':
    data_path = '/Users/guillemriusviladomiu/.gemini/antigravity/scratch/nq_5m_recent.csv'
    
    # Define exploration grid
    tps = [5, 8, 10, 12, 15, 20, 25, 30, 40, 50]
    sls = [10, 15, 20, 25, 30, 35, 40, 50, 60]
    
    out_file = '/Users/guillemriusviladomiu/.gemini/workspaces-antigravity/backtest-master-pro-2026/results/grid_search_results.csv'
    df_results = optimize(data_path, tps, sls, output_csv=out_file)
    
    print("\n" + "="*80)
    print("🏆 TOP 15 CONFIGURACIONS PER NET PNL (USD)")
    print("="*80)
    print(df_results[['tp_pts', 'sl_pts', 'risk_mult', 'win_rate', 'profit_factor', 'pnl_usd', 'max_dd_usd', 'avg_trade_usd']].head(15).to_string(index=False))

    print("\n" + "="*80)
    print("💎 TOP 10 CONFIGURACIONS PER PROFIT FACTOR (min 50 trades)")
    print("="*80)
    filtered = df_results[df_results['total_trades'] >= 50].sort_values(by='profit_factor', ascending=False)
    print(filtered[['tp_pts', 'sl_pts', 'risk_mult', 'win_rate', 'profit_factor', 'pnl_usd', 'max_dd_usd', 'avg_trade_usd']].head(10).to_string(index=False))
