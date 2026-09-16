#!/usr/bin/env python3
"""
Ultra-fast 1-Year Optimizer for NQ Zones Reversal Strategy
Precomputes all trade entries (which are fixed at the unswept levels),
then evaluates TP and SL combinations instantly in vectorized fashion.
"""

import sys
import os
import pandas as pd
import numpy as np

# Load preprocessed parquet
parquet_path = '/Users/guillemriusviladomiu/.gemini/workspaces-antigravity/backtest-master-pro-2026/data/mnq_1m_1year.parquet'
print(f"📥 Loading {parquet_path}...")
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

print("🔍 Extracting entries for each trading day...")

# Find all entries: (trading_date, zone_name, type, entry_price, entry_idx, active_bars_high, active_bars_low, active_bars_close)
entries = []

grouped = df.groupby('trading_date')
for t_date, day_bars in grouped:
    if len(day_bars) < 60:
        continue
        
    asia_bars = day_bars[day_bars['hour'] >= 20]
    if len(asia_bars) == 0:
        continue
        
    asia_high = asia_bars['High'].max()
    asia_low = asia_bars['Low'].min()
    
    levels = [
        ('Asia High', 'SHORT', asia_high, 0),
        ('Asia Low', 'LONG', asia_low, 0)
    ]
    
    london_bars = day_bars[(day_bars['hour'] >= 2) & (day_bars['hour'] < 5)]
    if len(london_bars) > 0:
        london_high = london_bars['High'].max()
        london_low = london_bars['Low'].min()
        levels.append(('London High', 'SHORT', london_high, 5))
        levels.append(('London Low', 'LONG', london_low, 5))
        
    active_bars = day_bars[day_bars['hour'] < 17]
    highs = active_bars['High'].values
    lows = active_bars['Low'].values
    closes = active_bars['Close'].values
    bar_hours = active_bars['hour'].values
    bar_mins = active_bars['minute'].values
    
    for name, trade_type, level, active_from_h in levels:
        # Find first bar where level is touched
        filled = False
        fill_idx = -1
        for i in range(len(active_bars)):
            if bar_hours[i] >= active_from_h:
                if trade_type == 'SHORT' and highs[i] >= level:
                    filled = True
                    fill_idx = i
                    break
                elif trade_type == 'LONG' and lows[i] <= level:
                    filled = True
                    fill_idx = i
                    break
                    
        if filled:
            # Store remaining bars after fill
            entries.append({
                'date': t_date,
                'zone': name,
                'type': trade_type,
                'entry_price': level,
                'subsequent_highs': highs[fill_idx:],
                'subsequent_lows': lows[fill_idx:],
                'subsequent_closes': closes[fill_idx:],
                'eod_close': closes[-1]
            })

print(f"✅ Total entries identified across the year: {len(entries)}")

# Now evaluate any TP and SL in milliseconds!
def evaluate_grid(tp_list, sl_list):
    results = []
    point_value = 20.0 # 1 NQ contract
    
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
                        # Intra-bar check
                        if h >= target_sl:
                            outcome = 'SL'
                            pnl = -sl
                            break
                        elif l <= target_tp:
                            outcome = 'TP'
                            pnl = tp
                            break
                            
                    if outcome is None:
                        outcome = 'EOD'
                        pnl = entry - eod
                        
                else: # LONG
                    target_tp = entry + tp
                    target_sl = entry - sl
                    
                    for h, l in zip(highs, lows):
                        if l <= target_sl:
                            outcome = 'SL'
                            pnl = -sl
                            break
                        elif h >= target_tp:
                            outcome = 'TP'
                            pnl = tp
                            break
                            
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

# Grid parameters
tp_list = [5, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60]
sl_list = [15, 20, 25, 30, 35, 40, 45, 50, 60, 75]

print(f"\n🚀 Running vector evaluation across {len(tp_list)*len(sl_list)} combinations...")
res_df = evaluate_grid(tp_list, sl_list)
res_df = res_df.sort_values(by='pnl_usd', ascending=False).reset_index(drop=True)

out_csv = '/Users/guillemriusviladomiu/.gemini/workspaces-antigravity/backtest-master-pro-2026/results/grid_1year_results.csv'
res_df.to_csv(out_csv, index=False)
print(f"💾 Results saved to {out_csv}")

print("\n" + "="*85)
print("🏆 TOP 15 CONFIGURACIONS PER BENEFICI NET (1 ANY COMPLET NQ - 352K BARRES 1M)")
print("="*85)
print(res_df[['tp_pts', 'sl_pts', 'risk_mult', 'win_rate', 'profit_factor', 'pnl_usd', 'max_dd_usd', 'avg_trade_usd']].head(15).to_string(index=False))

print("\n" + "="*85)
print("💎 TOP 15 CONFIGURACIONS PER PROFIT FACTOR (1 ANY COMPLET NQ)")
print("="*85)
pf_sorted = res_df.sort_values(by='profit_factor', ascending=False).reset_index(drop=True)
print(pf_sorted[['tp_pts', 'sl_pts', 'risk_mult', 'win_rate', 'profit_factor', 'pnl_usd', 'max_dd_usd', 'avg_trade_usd']].head(15).to_string(index=False))

# Specific comparison with user baseline (10 TP, 30 SL)
base = res_df[(res_df['tp_pts'] == 10) & (res_df['sl_pts'] == 30)].iloc[0]
best_pnl = res_df.iloc[0]
best_pf = pf_sorted.iloc[0]

print("\n" + "="*85)
print("⚖️ COMPARATIVA DIRECTA: BASELINE USUARI VS SWEET SPOT DESCOBERT")
print("="*85)
print(f"1. BASELINE USUARI (TP 10 / SL 30):")
print(f"   Win Rate: {base['win_rate']}% | Profit Factor: {base['profit_factor']} | PnL: ${base['pnl_usd']:,.2f} | Max DD: ${base['max_dd_usd']:,.2f} | Avg/Trade: ${base['avg_trade_usd']:.2f}")

print(f"\n2. MÀXIM BENEFICI NET (TP {best_pnl['tp_pts']} / SL {best_pnl['sl_pts']}):")
print(f"   Win Rate: {best_pnl['win_rate']}% | Profit Factor: {best_pnl['profit_factor']} | PnL: ${best_pnl['pnl_usd']:,.2f} | Max DD: ${best_pnl['max_dd_usd']:,.2f} | Avg/Trade: ${best_pnl['avg_trade_usd']:.2f}")

print(f"\n3. MÀXIMA ROBUBTESA / PROFIT FACTOR (TP {best_pf['tp_pts']} / SL {best_pf['sl_pts']}):")
print(f"   Win Rate: {best_pf['win_rate']}% | Profit Factor: {best_pf['profit_factor']} | PnL: ${best_pf['pnl_usd']:,.2f} | Max DD: ${best_pf['max_dd_usd']:,.2f} | Avg/Trade: ${best_pf['avg_trade_usd']:.2f}")
