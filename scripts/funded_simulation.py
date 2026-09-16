#!/usr/bin/env python3
"""
Simulació per a Comptes Fondejats de 50K (Drawdown Límit: $2,000)
- Mes a mes: PnL, Win Rate, Max Drawdown
- Comparativa NQ vs MNQ (1 MNQ, 2 MNQ, 3 MNQ, 4 MNQ, 5 MNQ, 1 NQ)
- Anàlisi de supervivència de compte i estratègia d'agressivitat (petar comptes vs conservar)
"""

import sys
import os
import pandas as pd
import numpy as np

# Load 1-year parquet
parquet_path = '/Users/guillemriusviladomiu/.gemini/workspaces-antigravity/backtest-master-pro-2026/data/mnq_1m_1year.parquet'
df = pd.read_parquet(parquet_path)

if 'ny_time' in df.columns:
    df.index = pd.to_datetime(df['ny_time'])
elif 'datetime' in df.columns:
    df.index = pd.to_datetime(df['datetime']).dt.tz_convert('America/New_York')

col_map = {c: c.capitalize() for c in df.columns}
df.rename(columns=col_map, inplace=True)
df = df.sort_index()

hours = df.index.hour
trading_dates = []
for dt, h in zip(df.index, hours):
    if h >= 18:
        t_date = (dt + pd.Timedelta(days=1)).date()
        if t_date.weekday() == 6:
            t_date = t_date + pd.Timedelta(days=1)
    else:
        t_date = dt.date()
    trading_dates.append(t_date)

df['trading_date'] = trading_dates
df['hour'] = hours
df['minute'] = df.index.minute

def simulate_trades(tp, sl, london_only=False):
    grouped = df.groupby('trading_date')
    trades = []
    
    for t_date, day_bars in grouped:
        if len(day_bars) < 60:
            continue
            
        levels = []
        
        if not london_only:
            asia_bars = day_bars[day_bars['hour'] >= 20]
            if len(asia_bars) > 0:
                levels.append(('Asia High', 'SHORT', asia_bars['High'].max(), 0))
                levels.append(('Asia Low', 'LONG', asia_bars['Low'].min(), 0))
                
        london_bars = day_bars[(day_bars['hour'] >= 2) & (day_bars['hour'] < 5)]
        if len(london_bars) > 0:
            levels.append(('London High', 'SHORT', london_bars['High'].max(), 5))
            levels.append(('London Low', 'LONG', london_bars['Low'].min(), 5))
            
        active_bars = day_bars[day_bars['hour'] < 17]
        highs = active_bars['High'].values
        lows = active_bars['Low'].values
        closes = active_bars['Close'].values
        bar_hours = active_bars['hour'].values
        bar_times = active_bars.index
        
        for name, ttype, lvl, active_from_h in levels:
            filled = False
            fill_idx = -1
            for i in range(len(active_bars)):
                if bar_hours[i] >= active_from_h:
                    if ttype == 'SHORT' and highs[i] >= lvl:
                        filled = True; fill_idx = i; break
                    elif ttype == 'LONG' and lows[i] <= lvl:
                        filled = True; fill_idx = i; break
                        
            if filled:
                sub_h = highs[fill_idx:]
                sub_l = lows[fill_idx:]
                outcome = None
                pnl = 0
                exit_idx = -1
                
                if ttype == 'SHORT':
                    for k in range(len(sub_h)):
                        if sub_h[k] >= lvl + sl:
                            outcome = 'SL'; pnl = -sl; exit_idx = fill_idx + k; break
                        elif sub_l[k] <= lvl - tp:
                            outcome = 'TP'; pnl = tp; exit_idx = fill_idx + k; break
                else:
                    for k in range(len(sub_h)):
                        if sub_l[k] <= lvl - sl:
                            outcome = 'SL'; pnl = -sl; exit_idx = fill_idx + k; break
                        elif sub_h[k] >= lvl + tp:
                            outcome = 'TP'; pnl = tp; exit_idx = fill_idx + k; break
                            
                if outcome is None:
                    outcome = 'EOD'
                    pnl = lvl - closes[-1] if ttype == 'SHORT' else closes[-1] - lvl
                    exit_idx = len(active_bars) - 1
                    
                trades.append({
                    'trading_date': t_date,
                    'datetime': bar_times[fill_idx],
                    'zone': name,
                    'type': ttype,
                    'entry_price': lvl,
                    'outcome': outcome,
                    'pnl_pts': pnl
                })
                
    res = pd.DataFrame(trades)
    res['year_month'] = pd.to_datetime(res['trading_date']).dt.to_period('M')
    return res

print("⚙️ Generant simulacions per a comptes de 50k...")

# We will test two core setups:
# Setup 1: TP 10 / SL 60 (All zones)
# Setup 2: TP 8 / SL 60 (All zones - highest winrate 94.6%)
# Setup 3: TP 10 / SL 60 (London Only)
# Setup 4: TP 10 / SL 30 (Baseline)

setups = [
    ("Sweet Spot (TP 10 / SL 60)", 10, 60, False),
    ("Ultra-WinRate (TP 8 / SL 60)", 8, 60, False),
    ("London-Only (TP 10 / SL 60)", 10, 60, True),
    ("Baseline (TP 10 / SL 30)", 10, 30, False),
]

# Sizing options
sizings = [
    ("1 NQ", 20.0),
    ("5 MNQ", 10.0),
    ("4 MNQ", 8.0),
    ("3 MNQ", 6.0),
    ("2 MNQ", 4.0),
    ("1 MNQ", 2.0),
]

DD_LIMIT = 2000.0

for setup_name, tp, sl, london_only in setups:
    df_trades = simulate_trades(tp, sl, london_only)
    print("\n" + "="*95)
    print(f"📊 ESTRATÈGIA: {setup_name}")
    print(f"   Total trades: {len(df_trades)} | Punts totals: {df_trades['pnl_pts'].sum():.1f} pts")
    print("="*95)
    
    # Table of sizing impact over full year
    print("\n📈 RESUM ANUAL PER SIZING EN COMPTE DE 50K (Límit DD: $2.000):")
    print(f"{'Sizing':10s} | {'Valor/pt':9s} | {'Net PnL ($)':13s} | {'Max Trailing DD':16s} | {'% Límit DD':11s} | {'Supera DD?':12s}")
    print("-" * 80)
    for s_name, pt_val in sizings:
        cum = (df_trades['pnl_pts'] * pt_val).cumsum()
        peak = cum.cummax()
        dd = peak - cum
        max_dd = dd.max()
        net_pnl = cum.iloc[-1]
        pct_limit = (max_dd / DD_LIMIT) * 100
        survived = "✅ SALVAT" if max_dd < DD_LIMIT else "❌ PETAT"
        print(f"{s_name:10s} | ${pt_val:7.2f}/p | ${net_pnl:11,.2f} | ${max_dd:14,.2f} | {pct_limit:9.1f}% | {survived}")
        
    # Month by month breakdown for key sizings: 1 NQ, 3 MNQ, 2 MNQ
    print(f"\n📅 DESGLOSSAMENT MES A MES PER A: 1 NQ vs 3 MNQ vs 2 MNQ:")
    print(f"{'Mes':8s} | {'Trades':6s} | {'WinRate':7s} | {'PnL 1 NQ':11s} (DD NQ)   | {'PnL 3 MNQ':11s} (DD 3M)  | {'PnL 2 MNQ':11s} (DD 2M)")
    print("-" * 90)
    
    for ym, grp in df_trades.groupby('year_month'):
        n_trades = len(grp)
        wins = len(grp[grp['pnl_pts'] > 0])
        wr = wins / n_trades * 100 if n_trades > 0 else 0
        
        # Calculate within-month max drawdown for each sizing
        def get_m_stats(pt_val):
            m_pnl = grp['pnl_pts'].sum() * pt_val
            c = (grp['pnl_pts'] * pt_val).cumsum()
            pk = c.cummax()
            m_dd = (pk - c).max()
            return m_pnl, m_dd
            
        pnl_1nq, dd_1nq = get_m_stats(20.0)
        pnl_3m, dd_3m = get_m_stats(6.0)
        pnl_2m, dd_2m = get_m_stats(4.0)
        
        flag_nq = "⚠️" if dd_1nq >= DD_LIMIT else "  "
        print(f"{str(ym):8s} | {n_trades:6d} | {wr:6.1f}% | ${pnl_1nq:9,.0f} (${dd_1nq:5,.0f}){flag_nq} | ${pnl_3m:9,.0f} (${dd_3m:5,.0f}) | ${pnl_2m:9,.0f} (${dd_2m:5,.0f})")

