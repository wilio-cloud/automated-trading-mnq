#!/usr/bin/env python3
"""
Optimització i Backtest Exclusiu per a LONDRES (London High & London Low)
1 Any Complet de Futures CME Globex (352.220 barres d'1 minut)
"""

import os
import pandas as pd
import numpy as np

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

print("🔍 Extraient operacions exclusives de LONDRES...")

entries = []
grouped = df.groupby('trading_date')

for t_date, day_bars in grouped:
    if len(day_bars) < 60:
        continue
        
    london_bars = day_bars[(day_bars['hour'] >= 2) & (day_bars['hour'] < 5)]
    if len(london_bars) == 0:
        continue
        
    london_high = london_bars['High'].max()
    london_low = london_bars['Low'].min()
    
    levels = [
        ('London High', 'SHORT', london_high, 5),
        ('London Low', 'LONG', london_low, 5)
    ]
    
    # Active window from 05:00 to 16:59
    active_bars = day_bars[(day_bars['hour'] >= 5) & (day_bars['hour'] < 17)]
    if len(active_bars) == 0:
        continue
        
    highs = active_bars['High'].values
    lows = active_bars['Low'].values
    closes = active_bars['Close'].values
    bar_hours = active_bars['hour'].values
    bar_times = active_bars.index
    
    for name, trade_type, level, active_from_h in levels:
        filled = False
        fill_idx = -1
        for i in range(len(active_bars)):
            if trade_type == 'SHORT' and highs[i] >= level:
                filled = True
                fill_idx = i
                break
            elif trade_type == 'LONG' and lows[i] <= level:
                filled = True
                fill_idx = i
                break
                
        if filled:
            entries.append({
                'date': t_date,
                'datetime': bar_times[fill_idx],
                'zone': name,
                'type': trade_type,
                'entry_price': level,
                'subsequent_highs': highs[fill_idx:],
                'subsequent_lows': lows[fill_idx:],
                'subsequent_closes': closes[fill_idx:],
                'eod_close': closes[-1]
            })

print(f"✅ Total operacions de LONDRES identificades en 1 any: {len(entries)}")

def evaluate_grid(tp_list, sl_list):
    results = []
    point_value = 20.0 # 1 NQ
    
    for tp in tp_list:
        for sl in sl_list:
            total_pnl_pts = 0.0
            wins = 0
            losses = 0
            eod_exits = 0
            trade_pnls = []
            
            for e in entries:
                ttype = e['type']
                entry = e['entry_price']
                highs = e['subsequent_highs']
                lows = e['subsequent_lows']
                eod = e['eod_close']
                
                outcome = None
                pnl = 0.0
                
                if ttype == 'SHORT':
                    target_tp = entry - tp
                    target_sl = entry + sl
                    
                    for h, l in zip(highs, lows):
                        if h >= target_sl:
                            outcome = 'SL'; pnl = -sl; break
                        elif l <= target_tp:
                            outcome = 'TP'; pnl = tp; break
                            
                    if outcome is None:
                        outcome = 'EOD'
                        pnl = entry - eod
                else:
                    target_tp = entry + tp
                    target_sl = entry - sl
                    
                    for h, l in zip(highs, lows):
                        if l <= target_sl:
                            outcome = 'SL'; pnl = -sl; break
                        elif h >= target_tp:
                            outcome = 'TP'; pnl = tp; break
                            
                    if outcome is None:
                        outcome = 'EOD'
                        pnl = eod - entry
                        
                trade_pnls.append(pnl)
                total_pnl_pts += pnl
                if pnl > 0:
                    wins += 1
                elif pnl < 0:
                    losses += 1
                else:
                    eod_exits += 1
                    
            pnl_series = np.array(trade_pnls)
            cum_pnl = np.cumsum(pnl_series * point_value)
            peak = np.maximum.accumulate(cum_pnl)
            max_dd = np.max(peak - cum_pnl) if len(cum_pnl) > 0 else 0.0
            
            win_pnl = np.sum(pnl_series[pnl_series > 0]) * point_value
            loss_pnl = abs(np.sum(pnl_series[pnl_series < 0])) * point_value
            pf = win_pnl / loss_pnl if loss_pnl > 0 else 999.0
            
            total_t = len(entries)
            wr = wins / total_t * 100 if total_t > 0 else 0.0
            
            results.append({
                'tp_pts': tp,
                'sl_pts': sl,
                'rr_ratio': round(tp / sl, 2),
                'risk_mult': round(sl / tp, 2),
                'total_trades': total_t,
                'win_rate': round(wr, 2),
                'wins': wins,
                'losses': losses,
                'pnl_pts': round(total_pnl_pts, 2),
                'pnl_usd': round(total_pnl_pts * point_value, 2),
                'profit_factor': round(pf, 2),
                'max_dd_usd': round(max_dd, 2),
                'avg_trade_usd': round((total_pnl_pts * point_value) / total_t, 2)
            })
            
    return pd.DataFrame(results)

tp_list = [5, 8, 10, 12, 15, 20, 25, 30, 40, 50]
sl_list = [15, 20, 25, 30, 35, 40, 45, 50, 60, 75]

df_grid = evaluate_grid(tp_list, sl_list)
df_grid = df_grid.sort_values(by='pnl_usd', ascending=False).reset_index(drop=True)

out_csv = '/Users/guillemriusviladomiu/.gemini/workspaces-antigravity/backtest-master-pro-2026/results/grid_london_only.csv'
df_grid.to_csv(out_csv, index=False)

print("\n" + "="*85)
print("🏆 TOP 15 CONFIGURACIONS PER BENEFICI NET (NOMÉS LONDRES - 1 ANY)")
print("="*85)
print(df_grid[['tp_pts', 'sl_pts', 'risk_mult', 'win_rate', 'profit_factor', 'pnl_usd', 'max_dd_usd', 'avg_trade_usd']].head(15).to_string(index=False))

print("\n" + "="*85)
print("💎 TOP 10 CONFIGURACIONS PER PROFIT FACTOR (NOMÉS LONDRES)")
print("="*85)
df_pf = df_grid.sort_values(by='profit_factor', ascending=False).reset_index(drop=True)
print(df_pf[['tp_pts', 'sl_pts', 'risk_mult', 'win_rate', 'profit_factor', 'pnl_usd', 'max_dd_usd', 'avg_trade_usd']].head(10).to_string(index=False))
