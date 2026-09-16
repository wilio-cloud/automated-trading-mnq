#!/usr/bin/env python3
"""
Simulació d'1 Any Real a Tradovate amb Capital Inicial de 1.000$ i Escalat Dinàmic
- Estratègia: Només Londres (London High & London Low)
- TP: 10 punts | SL: 60 punts | EOD Exit a 16:55 EDT
- Instrument: MNQ (1 punt = $2.00 USD)
- Comissions reals Tradovate: -$1.50 USD per contracte Round-Trip
"""

import os
import pandas as pd
import numpy as np

parquet_path = 'data/mnq_1m_1year.parquet'
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

# Extreure operacions cronològiques
trades_raw = []
grouped = df.groupby('trading_date')

TP_PTS = 10.0
SL_PTS = 60.0
COMMISSION_PER_CONTRACT_RT = 1.50
POINT_VALUE = 2.0  # 1 punt MNQ = $2.00

for t_date, day_bars in grouped:
    if len(day_bars) < 60:
        continue

    london_bars = day_bars[(day_bars['hour'] >= 2) & (day_bars['hour'] < 5)]
    if len(london_bars) == 0:
        continue

    london_high = london_bars['High'].max()
    london_low = london_bars['Low'].min()

    levels = [
        ('London High', 'SHORT', london_high),
        ('London Low', 'LONG', london_low)
    ]

    active_bars = day_bars[(day_bars['hour'] >= 5) & (day_bars['hour'] < 17)]
    if len(active_bars) == 0:
        continue

    highs = active_bars['High'].values
    lows = active_bars['Low'].values
    closes = active_bars['Close'].values
    bar_times = active_bars.index

    # Processar cadascun dels 2 nivells (sense límit d'1 pèrdua, ambdós independents)
    for name, trade_type, level in levels:
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
            sub_h = highs[fill_idx:]
            sub_l = lows[fill_idx:]
            eod_c = closes[-1]
            entry_time = bar_times[fill_idx]

            outcome = None
            pnl_pts = 0.0

            if trade_type == 'SHORT':
                target_tp = level - TP_PTS
                target_sl = level + SL_PTS
                for h, l in zip(sub_h, sub_l):
                    if h >= target_sl:
                        outcome = 'SL'
                        pnl_pts = -SL_PTS
                        break
                    elif l <= target_tp:
                        outcome = 'TP'
                        pnl_pts = TP_PTS
                        break
                if outcome is None:
                    outcome = 'EOD'
                    pnl_pts = level - eod_c
            else:
                target_tp = level + TP_PTS
                target_sl = level - SL_PTS
                for h, l in zip(sub_h, sub_l):
                    if l <= target_sl:
                        outcome = 'SL'
                        pnl_pts = -SL_PTS
                        break
                    elif h >= target_tp:
                        outcome = 'TP'
                        pnl_pts = TP_PTS
                        break
                if outcome is None:
                    outcome = 'EOD'
                    pnl_pts = eod_c - level

            trades_raw.append({
                'datetime': entry_time,
                'date': t_date,
                'zone': name,
                'type': trade_type,
                'outcome': outcome,
                'pnl_pts': pnl_pts
            })

# Ordenar cronològicament per datetime
trades_df = pd.DataFrame(trades_raw).sort_values('datetime').reset_index(drop=True)
print(f"📊 Total d'operacions generades per la sessió de Londres en 1 any: {len(trades_df)}")

# Funció per executar una simulació amb una regla de sizing
def run_simulation(name, sizing_func, initial_capital=1000.0):
    capital = initial_capital
    peak = initial_capital
    max_dd = 0.0
    max_dd_pct = 0.0
    min_capital = initial_capital

    history = []
    
    for idx, row in trades_df.iterrows():
        contracts = sizing_func(capital)
        pts = row['pnl_pts']
        gross_pnl = pts * POINT_VALUE * contracts
        comm = COMMISSION_PER_CONTRACT_RT * contracts
        net_pnl = gross_pnl - comm
        
        capital += net_pnl
        if capital > peak:
            peak = capital
        dd = peak - capital
        dd_pct = (dd / peak) * 100.0 if peak > 0 else 0.0
        
        if dd > max_dd:
            max_dd = dd
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct
        if capital < min_capital:
            min_capital = capital
            
        history.append({
            'datetime': row['datetime'],
            'date': row['date'],
            'month': row['datetime'].strftime('%Y-%m'),
            'outcome': row['outcome'],
            'pnl_pts': pts,
            'contracts': contracts,
            'gross_pnl': gross_pnl,
            'comm': comm,
            'net_pnl': net_pnl,
            'capital': capital,
            'peak': peak,
            'dd': dd
        })

    hist_df = pd.DataFrame(history)
    
    total_trades = len(hist_df)
    wins = (hist_df['pnl_pts'] > 0).sum()
    losses = (hist_df['pnl_pts'] < 0).sum()
    wr = (wins / total_trades) * 100.0
    total_comm = hist_df['comm'].sum()
    net_profit = capital - initial_capital
    roi = (net_profit / initial_capital) * 100.0
    
    return {
        'name': name,
        'final_capital': capital,
        'net_profit': net_profit,
        'roi': roi,
        'total_comm': total_comm,
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'win_rate': wr,
        'max_dd': max_dd,
        'max_dd_pct': max_dd_pct,
        'min_capital': min_capital,
        'history': hist_df
    }

# 1. Model Fixe: 1 MNQ sempre
sim_fixed = run_simulation("Fixe 1 MNQ (Sense Escalat)", lambda cap: 1)

# 2. Model Prudent (Configuració per defecte bot/config.py)
def sizing_prudent(cap):
    if cap >= 4800:
        return 4
    elif cap >= 3500:
        return 3
    elif cap >= 2200:
        return 2
    else:
        return 1

sim_prudent = run_simulation("Escalat Prudent (Max 4 MNQ)", sizing_prudent)

# 3. Model Institucional Fondejat (Escalat fins a 5 MNQ amb coixí de $1.200 per contracte)
def sizing_institucional(cap):
    if cap >= 6000:
        return 5
    elif cap >= 4600:
        return 4
    elif cap >= 3300:
        return 3
    elif cap >= 2100:
        return 2
    else:
        return 1

sim_inst = run_simulation("Escalat Institucional (1 a 5 MNQ)", sizing_institucional)

# 4. Model Agresiu (1 MNQ per cada $1.000 de capital, fins a 10 MNQ)
def sizing_agressiu(cap):
    qty = int(cap // 1000)
    return max(1, min(qty, 10))

sim_agressiu = run_simulation("Escalat Compost Continu (fins a 10 MNQ)", sizing_agressiu)

print("\n" + "="*85)
print("🏆 RESULTATS COMPARATIUS DE LA SIMULACIÓ D'1 ANY (CAPITAL INICIAL: $1.000 USD)")
print("="*85)

sims = [sim_fixed, sim_prudent, sim_inst, sim_agressiu]
for s in sims:
    print(f"\n📌 {s['name'].upper()}:")
    print(f"   • Saldo Final:           ${s['final_capital']:,.2f} USD")
    print(f"   • Benefici Net:          +${s['net_profit']:,.2f} USD (+{s['roi']:,.1f}%)")
    print(f"   • Comissions CME:        -${s['total_comm']:,.2f} USD")
    print(f"   • Win Rate:              {s['win_rate']:.2f}% ({s['wins']} guanys / {s['losses']} pèrdues)")
    print(f"   • Max Drawdown:          -${s['max_dd']:,.2f} USD ({s['max_dd_pct']:.1f}%)")
    print(f"   • Saldo Mínim Històric:  ${s['min_capital']:,.2f} USD (Cushion sobre marge mínim de $100)")

# Desglossament mensual de la modalitat Institucional (1 a 5 MNQ)
hist = sim_inst['history']
print("\n" + "="*85)
print("📅 DESGLOSSAMENT MES A MES - MODEL ESCALAT INSTITUCIONAL (1 a 5 MNQ)")
print("="*85)
print(f"{'Mes':<10} | {'Trades':<6} | {'WR (%)':<7} | {'Contractes':<10} | {'Benefici Net':<14} | {'Saldo Final':<12} | {'Max DD ($)':<10}")
print("-" * 85)

for m, m_group in hist.groupby('month'):
    m_trades = len(m_group)
    m_wins = (m_group['pnl_pts'] > 0).sum()
    m_wr = (m_wins / m_trades) * 100.0 if m_trades > 0 else 0.0
    m_net = m_group['net_pnl'].sum()
    m_end_cap = m_group['capital'].iloc[-1]
    m_contracts = f"{m_group['contracts'].min()}-{m_group['contracts'].max()}" if m_group['contracts'].min() != m_group['contracts'].max() else f"{m_group['contracts'].iloc[0]}"
    
    # DD dins del mes
    m_peaks = m_group['capital'].cummax()
    m_dds = m_peaks - m_group['capital']
    m_max_dd = m_dds.max()
    
    print(f"{m:<10} | {m_trades:<6} | {m_wr:>6.1f}% | {m_contracts:<10} | {m_net:>+13,.2f}$ | {m_end_cap:>11,.2f}$ | -{m_max_dd:>8,.2f}$")

print("="*85)
