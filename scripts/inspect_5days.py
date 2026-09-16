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

# Pick 5 diverse dates:
# 1. 2026-09-11 (Recent Friday)
# 2. 2026-07-15 (Summer)
# 3. 2026-04-16 (Spring)
# 4. 2026-01-22 (Winter)
# 5. 2025-10-23 (Autumn)

test_dates = [
    pd.to_datetime('2026-09-11').date(),
    pd.to_datetime('2026-07-15').date(),
    pd.to_datetime('2026-04-16').date(),
    pd.to_datetime('2026-01-22').date(),
    pd.to_datetime('2025-10-23').date(),
]

TP = 10.0
SL = 60.0

for t_date in test_dates:
    day_bars = df[df['trading_date'] == t_date]
    if len(day_bars) < 60:
        continue
        
    print(f"\n{'='*80}")
    print(f"📅 DATA D'AUDITORIA: {t_date.strftime('%d/%m/%Y')} (NQ 1m)")
    print(f"{'='*80}")
    
    # Asia
    asia_bars = day_bars[day_bars['hour'] >= 20]
    asia_h = asia_bars['High'].max()
    asia_l = asia_bars['Low'].min()
    asia_h_time = asia_bars['High'].idxmax().strftime('%H:%M')
    asia_l_time = asia_bars['Low'].idxmin().strftime('%H:%M')
    
    print(f"1. SESSIÓ ÀSIA (20:00h - 00:00h EDT):")
    print(f"   • Asia High : {asia_h:,.2f} (format a les {asia_h_time}h)")
    print(f"   • Asia Low  : {asia_l:,.2f} (format a les {asia_l_time}h)")
    
    # London
    london_bars = day_bars[(day_bars['hour'] >= 2) & (day_bars['hour'] < 5)]
    london_h = london_bars['High'].max()
    london_l = london_bars['Low'].min()
    london_h_time = london_bars['High'].idxmax().strftime('%H:%M')
    london_l_time = london_bars['Low'].idxmin().strftime('%H:%M')
    
    print(f"2. SESSIÓ LONDRES (02:00h - 05:00h EDT):")
    print(f"   • London High: {london_h:,.2f} (format a les {london_h_time}h)")
    print(f"   • London Low : {london_l:,.2f} (format a les {london_l_time}h)")
    
    # Trace executions
    levels = [
        ('Asia High', 'SHORT', asia_h, 0),
        ('Asia Low', 'LONG', asia_l, 0),
        ('London High', 'SHORT', london_h, 5),
        ('London Low', 'LONG', london_l, 5)
    ]
    
    active_bars = day_bars[day_bars['hour'] < 17]
    highs = active_bars['High'].values
    lows = active_bars['Low'].values
    closes = active_bars['Close'].values
    bar_hours = active_bars['hour'].values
    bar_times = active_bars.index
    
    print(f"\n3. DESENVOLUPAMENT I OPERACIONS (Config: TP {TP} pts / SL {SL} pts):")
    
    for name, ttype, lvl, active_from_h in levels:
        filled = False
        fill_idx = -1
        for i in range(len(active_bars)):
            if bar_hours[i] >= active_from_h:
                if ttype == 'SHORT' and highs[i] >= lvl:
                    filled = True; fill_idx = i; break
                elif ttype == 'LONG' and lows[i] <= lvl:
                    filled = True; fill_idx = i; break
                    
        if not filled:
            print(f"   ⚪ {name:12s} ({ttype:5s} @ {lvl:,.2f}): NO TOCADA. Cancel·lada a les 16:55h.")
        else:
            fill_time = bar_times[fill_idx].strftime('%H:%M')
            sub_h = highs[fill_idx:]
            sub_l = lows[fill_idx:]
            outcome = None
            exit_time = None
            pnl = 0
            
            target_tp = lvl - TP if ttype == 'SHORT' else lvl + TP
            target_sl = lvl + SL if ttype == 'SHORT' else lvl - SL
            
            if ttype == 'SHORT':
                for k in range(len(sub_h)):
                    if sub_h[k] >= target_sl:
                        outcome = 'SL'; pnl = -SL; exit_time = bar_times[fill_idx + k].strftime('%H:%M'); break
                    elif sub_l[k] <= target_tp:
                        outcome = 'TP'; pnl = TP; exit_time = bar_times[fill_idx + k].strftime('%H:%M'); break
            else:
                for k in range(len(sub_h)):
                    if sub_l[k] <= target_sl:
                        outcome = 'SL'; pnl = -SL; exit_time = bar_times[fill_idx + k].strftime('%H:%M'); break
                    elif sub_h[k] >= target_tp:
                        outcome = 'TP'; pnl = TP; exit_time = bar_times[fill_idx + k].strftime('%H:%M'); break
                        
            if outcome is None:
                outcome = 'EOD'
                exit_time = '16:55'
                pnl = round(lvl - closes[-1] if ttype == 'SHORT' else closes[-1] - lvl, 2)
                
            icon = "✅" if pnl > 0 else ("❌" if pnl < 0 else "⚪")
            print(f"   {icon} {name:12s} ({ttype:5s} @ {lvl:,.2f}) | Fill: {fill_time}h | Sortida: {exit_time}h ({outcome}) | PnL: {pnl:+.1f} pts (${pnl*20:+,.0f} USD)")

