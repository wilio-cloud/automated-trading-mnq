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

# Group by day
grouped = df.groupby('trading_date')

entries_all = []
entries_london = []

for t_date, day_bars in grouped:
    if len(day_bars) < 60:
        continue
        
    # Asia 20:00 to 00:00 (h: 20, 21, 22, 23)
    asia_bars = day_bars[(day_bars['hour'] >= 20) | (day_bars['hour'] == 0)] # actually 20 to 23
    asia_bars = day_bars[(day_bars['hour'] >= 20) & (day_bars['hour'] <= 23)]
    
    # London 02:00 to 05:00
    london_bars = day_bars[(day_bars['hour'] >= 2) & (day_bars['hour'] < 5)]
    
    # Levels
    levels = []
    if len(asia_bars) > 0:
        a_h = asia_bars['High'].max()
        a_l = asia_bars['Low'].min()
        levels.append(('Asia High', 'SHORT', a_h, 0, False))
        levels.append(('Asia Low', 'LONG', a_l, 0, False))
        
    if len(london_bars) > 0:
        l_h = london_bars['High'].max()
        l_l = london_bars['Low'].min()
        levels.append(('London High', 'SHORT', l_h, 5, True))
        levels.append(('London Low', 'LONG', l_l, 5, True))
        
    active_bars = day_bars[(day_bars['hour'] >= 0) & (day_bars['hour'] < 17)]
    if len(active_bars) == 0:
        continue
        
    highs = active_bars['High'].values
    lows = active_bars['Low'].values
    closes = active_bars['Close'].values
    bar_hours = active_bars['hour'].values
    bar_times = active_bars.index
    
    for name, trade_type, level, active_from_h, is_london in levels:
        filled = False
        fill_idx = -1
        for i in range(len(active_bars)):
            if bar_hours[i] < active_from_h:
                continue
            if trade_type == 'SHORT' and highs[i] >= level:
                filled = True
                fill_idx = i
                break
            elif trade_type == 'LONG' and lows[i] <= level:
                filled = True
                fill_idx = i
                break
                
        if filled:
            entry_obj = {
                'date': t_date,
                'datetime': bar_times[fill_idx],
                'zone': name,
                'type': trade_type,
                'entry_price': level,
                'subsequent_highs': highs[fill_idx:],
                'subsequent_lows': lows[fill_idx:],
                'subsequent_closes': closes[fill_idx:],
                'eod_close': closes[-1]
            }
            entries_all.append(entry_obj)
            if is_london:
                entries_london.append(entry_obj)

print(f"Total operacions identificades: Àsia+Londres={len(entries_all)}, Només Londres={len(entries_london)}")

def run_eval(entry_list, tp_val, sl_val, label):
    point_val_nq = 20.0
    point_val_mnq5 = 10.0 # 5 MNQ = $10/pt
    comm_mnq5 = 6.50 # ~$1.30 RT x 5 MNQ = $6.50
    comm_nq = 4.50  # ~$4.50 RT x 1 NQ
    
    pnls_pts = []
    wins = 0
    losses = 0
    eod_exits = 0
    
    for e in entry_list:
        ttype = e['type']
        entry = e['entry_price']
        highs = e['subsequent_highs']
        lows = e['subsequent_lows']
        eod = e['eod_close']
        
        outcome = None
        pnl = 0.0
        
        if ttype == 'SHORT':
            target_tp = entry - tp_val
            target_sl = entry + sl_val
            for h, l in zip(highs, lows):
                if h >= target_sl:
                    outcome = 'SL'; pnl = -sl_val; break
                elif l <= target_tp:
                    outcome = 'TP'; pnl = tp_val; break
            if outcome is None:
                outcome = 'EOD'; pnl = entry - eod
        else:
            target_tp = entry + tp_val
            target_sl = entry - sl_val
            for h, l in zip(highs, lows):
                if l <= target_sl:
                    outcome = 'SL'; pnl = -sl_val; break
                elif h >= target_tp:
                    outcome = 'TP'; pnl = tp_val; break
            if outcome is None:
                outcome = 'EOD'; pnl = eod - entry
                
        if outcome == 'TP' or pnl > 0:
            wins += 1
        elif outcome == 'SL' or pnl < 0:
            losses += 1
        pnls_pts.append(pnl)
        
    pnls = np.array(pnls_pts)
    total_trades = len(pnls)
    wr = (wins / total_trades) * 100
    gross_pts = pnls.sum()
    
    # 5 MNQ ($10/pt)
    gross_5mnq = gross_pts * 10.0
    net_5mnq = gross_5mnq - (total_trades * comm_mnq5)
    cum_5mnq = np.cumsum(pnls * 10.0 - comm_mnq5)
    peak_5mnq = np.maximum.accumulate(cum_5mnq)
    dd_5mnq = np.max(peak_5mnq - cum_5mnq)
    
    # 1 NQ ($20/pt)
    gross_1nq = gross_pts * 20.0
    net_1nq = gross_1nq - (total_trades * comm_nq)
    cum_1nq = np.cumsum(pnls * 20.0 - comm_nq)
    peak_1nq = np.maximum.accumulate(cum_1nq)
    dd_1nq = np.max(peak_1nq - cum_1nq)
    
    # Profit factor
    pos = pnls[pnls > 0].sum()
    neg = abs(pnls[pnls < 0].sum())
    pf = (pos / neg) if neg > 0 else 99.0
    
    # Avg per trade (5 MNQ)
    avg_gross_5mnq = gross_5mnq / total_trades
    avg_net_5mnq = net_5mnq / total_trades
    
    return {
        'label': label,
        'tp': tp_val,
        'sl': sl_val,
        'trades': total_trades,
        'wins': wins,
        'losses': losses,
        'wr': wr,
        'pf': pf,
        'gross_pts': gross_pts,
        'gross_5mnq': gross_5mnq,
        'net_5mnq': net_5mnq,
        'dd_5mnq': dd_5mnq,
        'avg_gross_5mnq': avg_gross_5mnq,
        'avg_net_5mnq': avg_net_5mnq,
        'net_1nq': net_1nq,
        'dd_1nq': dd_1nq
    }

print("\n" + "="*80)
print("TEST COMPARATIU: TP 10 vs TP 11 vs TP 12 (amb SL 60 i SL 50)")
print("Comissions aplicades: $6.50 RT per trade en 5 MNQ | $4.50 RT en 1 NQ")
print("="*80)

# London Only
results_lon = []
for sl in [60, 50]:
    for tp in [10, 11, 12]:
        res = run_eval(entries_london, tp, sl, f"Londres TP {tp}/SL {sl}")
        results_lon.append(res)

df_lon = pd.DataFrame(results_lon)
print("\n--- RESULTATS NOMÉS LONDRES (London-Only) ---")
for r in results_lon:
    print(f"Config: {r['label']:<20} | WR: {r['wr']:5.2f}% ({r['wins']}W/{r['losses']}L) | PF: {r['pf']:4.2f} | 5MNQ Brut: ${r['gross_5mnq']:,.0f} | 5MNQ Net: ${r['net_5mnq']:,.0f} | MaxDD: ${r['dd_5mnq']:,.0f} | Net/Trade: ${r['avg_net_5mnq']:5.2f}")

# Asia + London
results_all = []
for sl in [60, 50]:
    for tp in [10, 11, 12]:
        res = run_eval(entries_all, tp, sl, f"Àsia+Lon TP {tp}/SL {sl}")
        results_all.append(res)

print("\n--- RESULTATS TOTES LES SESSIONS (Àsia + Londres) ---")
for r in results_all:
    print(f"Config: {r['label']:<20} | WR: {r['wr']:5.2f}% ({r['wins']}W/{r['losses']}L) | PF: {r['pf']:4.2f} | 5MNQ Brut: ${r['gross_5mnq']:,.0f} | 5MNQ Net: ${r['net_5mnq']:,.0f} | MaxDD: ${r['dd_5mnq']:,.0f} | Net/Trade: ${r['avg_net_5mnq']:5.2f}")

