#!/usr/bin/env python3
import pandas as pd
import numpy as np

# Load 1-year parquet
df = pd.read_parquet('/Users/guillemriusviladomiu/.gemini/workspaces-antigravity/backtest-master-pro-2026/data/mnq_1m_1year.parquet')
if 'ny_time' in df.columns:
    df.index = pd.to_datetime(df['ny_time'])
elif 'datetime' in df.columns:
    df.index = pd.to_datetime(df['datetime']).dt.tz_convert('America/New_York')

col_map = {c: c.capitalize() for c in df.columns}
df.rename(columns=col_map, inplace=True)

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

# Evaluate per zone with TP=10, SL=30 and TP=10, SL=60
for tp, sl in [(10, 30), (10, 60), (8, 60), (12, 60)]:
    print(f"=== CONFIG TP: {tp} | SL: {sl} (1 FULL YEAR) ===")
    grouped = df.groupby('trading_date')
    zone_trades = {'Asia High': [], 'Asia Low': [], 'London High': [], 'London Low': []}
    
    for t_date, day_bars in grouped:
        if len(day_bars) < 60:
            continue
        asia_bars = day_bars[day_bars['hour'] >= 20]
        if len(asia_bars) == 0:
            continue
        asia_h = asia_bars['High'].max()
        asia_l = asia_bars['Low'].min()
        
        levels = [
            ('Asia High', 'SHORT', asia_h, 0),
            ('Asia Low', 'LONG', asia_l, 0)
        ]
        london_bars = day_bars[(day_bars['hour'] >= 2) & (day_bars['hour'] < 5)]
        if len(london_bars) > 0:
            levels.append(('London High', 'SHORT', london_bars['High'].max(), 5))
            levels.append(('London Low', 'LONG', london_bars['Low'].min(), 5))
            
        active_bars = day_bars[day_bars['hour'] < 17]
        highs = active_bars['High'].values
        lows = active_bars['Low'].values
        closes = active_bars['Close'].values
        bar_hours = active_bars['hour'].values
        
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
                if ttype == 'SHORT':
                    for h, l in zip(sub_h, sub_l):
                        if h >= lvl + sl:
                            outcome = 'SL'; pnl = -sl; break
                        elif l <= lvl - tp:
                            outcome = 'TP'; pnl = tp; break
                else:
                    for h, l in zip(sub_h, sub_l):
                        if l <= lvl - sl:
                            outcome = 'SL'; pnl = -sl; break
                        elif h >= lvl + tp:
                            outcome = 'TP'; pnl = tp; break
                if outcome is None:
                    pnl = lvl - closes[-1] if ttype == 'SHORT' else closes[-1] - lvl
                zone_trades[name].append(pnl)
                
    for zname, pnl_list in zone_trades.items():
        arr = np.array(pnl_list)
        wins = np.sum(arr > 0)
        losses = np.sum(arr < 0)
        wr = wins / len(arr) * 100 if len(arr) > 0 else 0
        total_pnl = np.sum(arr) * 20.0
        print(f"  {zname:12s} | Trades: {len(arr):3d} | WR: {wr:5.1f}% ({wins}W / {losses}L) | Net PnL: ${total_pnl:9.2f}")
    print()
