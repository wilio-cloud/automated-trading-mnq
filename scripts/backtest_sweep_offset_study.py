#!/usr/bin/env python3
"""
ESTUDI QUANTITATIU D'OFFSETS I ESCOMBRADES (SWEEPS) A LES ZONES DE LONDRES
========================================================================
Motor ultra-ràpid vectoritzat amb NumPy (CME Globex MNQ a 1 Segon)

Analitza:
- Offsets: 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0, 15.0 punts.
- Model A: TP Relatiu Fix de 14 pts des de l'entrada (SL 60 pts).
- Model B: Target Ràpid reduït (distància TP = 14 - Offset pts, per sortir a màxima velocitat).
- Model C: Preu Objectiu Original Fix (TP guanya 14 + Offset pts).
- Distribució empírica de l'escombrada (Sweep Depth) dels primers 15-30 minuts post-contacte.
"""

import os
import sys
import datetime
import numpy as np
import pandas as pd

CACHE_1S_MASTER = "data/mnq_1s_full_2025_2026.parquet"
FALLBACK_1S = "data/mnq_1s_london_1year.parquet"
DATA_1M_MASTER = "data/mnq_1m_master.parquet"
RESULTS_DIR = "results"

print("=" * 105)
print("🔬 MOTOR VECTORITZAT: ESTUDI QUANTITATIU D'OFFSETS DE SWEEP A 1 SEGON")
print("=" * 105)

# 1. Carregar dades 1s
if os.path.exists(CACHE_1S_MASTER):
    print(f"📥 Carregant master d'1 segon consolidat ({CACHE_1S_MASTER})...")
    df_1s = pd.read_parquet(CACHE_1S_MASTER)
elif os.path.exists(FALLBACK_1S):
    print(f"📥 Carregant master d'1 segon ({FALLBACK_1S})...")
    df_1s = pd.read_parquet(FALLBACK_1S)
else:
    raise FileNotFoundError("No s'ha trobat cap fitxer parquet d'1 segon.")

if df_1s.index.tz is None:
    df_1s.index = pd.to_datetime(df_1s.index).tz_localize("UTC").tz_convert("America/New_York")
else:
    df_1s.index = pd.to_datetime(df_1s.index).tz_convert("America/New_York")

df_1s["trading_date"] = df_1s.index.date
df_1s["hour"] = df_1s.index.hour
df_1s["minute"] = df_1s.index.minute
df_1s["second"] = df_1s.index.second
print(f"✅ Dades 1s carregades: {len(df_1s):,} barres sobre {df_1s['trading_date'].nunique()} sessions.")

# 2. Carregar dades 1m per a nivells de Londres (02:00 a 05:00 EDT)
print(f"📥 Carregant dades d'1 minut master ({DATA_1M_MASTER})...")
df_1m = pd.read_parquet(DATA_1M_MASTER)
if "ny_time" in df_1m.columns:
    df_1m.index = pd.to_datetime(df_1m["ny_time"])
elif "datetime" in df_1m.columns:
    df_1m.index = pd.to_datetime(df_1m["datetime"]).dt.tz_convert("America/New_York")

col_map = {c: c.capitalize() for c in df_1m.columns}
df_1m.rename(columns=col_map, inplace=True)
df_1m = df_1m.sort_index()
df_1m["hour"] = df_1m.index.hour
df_1m["trading_date"] = [dt.date() if h < 18 else (dt + pd.Timedelta(days=1)).date() for dt, h in zip(df_1m.index, df_1m["hour"])]

# 3. Filtre de Notícies Institucional
fomc_dates = {
    '2025-01-29', '2025-03-19', '2025-05-07', '2025-06-18', '2025-07-30', '2025-09-17', '2025-10-29', '2025-11-05', '2025-12-10', '2025-12-17',
    '2026-01-28', '2026-03-18', '2026-05-06', '2026-05-20', '2026-06-10', '2026-07-29', '2026-09-16'
}
cpi_nfp_dates = {
    '2025-01-15', '2025-02-12', '2025-03-12', '2025-04-10', '2025-05-13', '2025-06-11', '2025-07-11', '2025-08-13', '2025-09-10', '2025-10-14', '2025-10-15', '2025-11-12', '2025-12-10',
    '2025-01-10', '2025-02-07', '2025-03-07', '2025-04-04', '2025-05-02', '2025-06-06', '2025-07-03', '2025-08-01', '2025-09-05', '2025-10-03', '2025-11-07', '2025-12-05',
    '2026-01-14', '2026-02-11', '2026-02-13', '2026-03-11', '2026-04-10', '2026-05-12', '2026-06-10', '2026-07-14', '2026-08-11', '2026-09-11',
    '2026-01-09', '2026-02-06', '2026-03-06', '2026-04-03', '2026-05-08', '2026-06-05', '2026-07-02', '2026-08-07', '2026-09-04',
    '2025-09-26'
}
opex_rebal_dates = {
    '2025-01-17', '2025-02-21', '2025-03-21', '2025-04-18', '2025-05-16', '2025-06-20', '2025-07-18', '2025-08-15', '2025-09-19', '2025-10-17', '2025-11-21', '2025-12-19',
    '2026-01-16', '2026-02-20', '2026-03-20', '2026-04-17', '2026-05-15', '2026-06-19', '2026-07-17', '2026-08-21', '2026-09-18',
    '2025-01-02', '2025-01-03', '2025-07-07', '2026-01-02', '2026-07-06'
}
all_macro_day_filter = fomc_dates | cpi_nfp_dates | opex_rebal_dates

def is_macro_filtered(d_str, dt):
    if d_str in all_macro_day_filter: return True
    if dt.month in [3, 6, 9, 12] and dt.day >= 29: return True
    if dt.month == 8 and 22 <= dt.day <= 28: return True
    return False

s_grouped = {k: v for k, v in df_1s.groupby("trading_date")}
m_grouped = {k: v for k, v in df_1m.groupby("trading_date")}

# 4. Preprocessar cada dia hàbil en arrays NumPy per a màxima eficiència
print("⚡ Preprocessant sessions a la memòria en memòria cau NumPy...")
day_data_list = []

for t_date in sorted(s_grouped.keys()):
    if t_date not in m_grouped: continue
    d_str = t_date.strftime("%Y-%m-%d")
    if is_macro_filtered(d_str, t_date): continue
    
    m_day = m_grouped[t_date]
    l_bars = m_day[(m_day["hour"] >= 2) & (m_day["hour"] < 5)]
    if len(l_bars) == 0: continue
    l_high = float(l_bars["High"].max())
    l_low = float(l_bars["Low"].min())
    
    s_day = s_grouped[t_date]
    if len(s_day) < 100: continue
    
    h_arr = s_day["high"].to_numpy(dtype=np.float64)
    l_arr = s_day["low"].to_numpy(dtype=np.float64)
    c_arr = s_day["close"].to_numpy(dtype=np.float64)
    
    # Vector de temps en segons des de 00:00 EDT
    hours = s_day["hour"].to_numpy(dtype=np.int32)
    minutes = s_day["minute"].to_numpy(dtype=np.int32)
    seconds = s_day["second"].to_numpy(dtype=np.int32)
    time_secs = hours * 3600 + minutes * 60 + seconds
    
    # Cutoff de col·locació d'ordres: 09:20 EDT = 9 * 3600 + 20 * 60 = 33,600 segons
    cutoff_sec = 33600
    cutoff_mask = time_secs < cutoff_sec
    
    day_data_list.append({
        "t_date": t_date,
        "d_str": d_str,
        "l_high": l_high,
        "l_low": l_low,
        "h_arr": h_arr,
        "l_arr": l_arr,
        "c_arr": c_arr,
        "time_secs": time_secs,
        "cutoff_mask": cutoff_mask
    })

print(f"✅ {len(day_data_list)} sessions filtrades i vectoritzades a la memòria.")

# 5. Distribució empírica de l'escombrada (Sweep Wicks)
print("\n📊 Mesurant la distribució real del Sweep (excursions més enllà de la zona abans de 09:20 EDT):")
short_sweeps = []
long_sweeps = []

for day in day_data_list:
    l_high = day["l_high"]
    l_low = day["l_low"]
    h_arr = day["h_arr"]
    l_arr = day["l_arr"]
    mask = day["cutoff_mask"]
    
    # Per a High (Short)
    touch_h = np.where(mask & (h_arr >= l_high))[0]
    if len(touch_h) > 0:
        first_i = touch_h[0]
        # Veure quant traspassa en els següents minuts abans del cutoff
        sub_h = h_arr[first_i:]
        max_pen = float(np.max(sub_h) - l_high)
        short_sweeps.append(max_pen)
        
    # Per a Low (Long)
    touch_l = np.where(mask & (l_arr <= l_low))[0]
    if len(touch_l) > 0:
        first_i = touch_l[0]
        sub_l = l_arr[first_i:]
        max_pen = float(l_low - np.min(sub_l))
        long_sweeps.append(max_pen)

all_sweeps = short_sweeps + long_sweeps
print(f"   • Contactes totals a la línia exacta: {len(all_sweeps)} ({len(short_sweeps)} Shorts, {len(long_sweeps)} Longs)")
print("   • Distribució de penetració (punts):")
for p in [10, 25, 50, 75, 90]:
    print(f"     - Percentil {p}%: {np.percentile(all_sweeps, p):.2f} pts")

# 6. Funció d'avaluació ràpida per vectorització
def run_vectorized_study(offsets, model="A", tp_pts=14.0, sl_pts=60.0):
    CONTRACTS = 5
    POINT_VAL = 2.0 * CONTRACTS  # 5 MNQ = $10 / punt
    COMMISSION = 1.50 * CONTRACTS  # $7.50 RT
    
    rows = []
    
    for offset in offsets:
        trades = []
        
        for day in day_data_list:
            l_high = day["l_high"]
            l_low = day["l_low"]
            h_arr = day["h_arr"]
            l_arr = day["l_arr"]
            c_arr = day["c_arr"]
            time_secs = day["time_secs"]
            mask = day["cutoff_mask"]
            d_str = day["d_str"]
            
            # Avaluar SHORT (London High + offset) i LONG (London Low - offset)
            for z_name, ttype, base_lvl, entry_lvl in [
                ("London High", "SHORT", l_high, l_high + offset),
                ("London Low", "LONG", l_low, l_low - offset)
            ]:
                if ttype == "SHORT":
                    fill_cands = np.where(mask & (h_arr >= entry_lvl))[0]
                else:
                    fill_cands = np.where(mask & (l_arr <= entry_lvl))[0]
                    
                if len(fill_cands) == 0:
                    continue
                    
                fill_i = fill_cands[0]
                fill_sec = time_secs[fill_i]
                
                sub_h = h_arr[fill_i+1:]
                sub_l = l_arr[fill_i+1:]
                sub_t = time_secs[fill_i+1:]
                
                if len(sub_h) == 0:
                    continue
                    
                # Definició de preus objectiu segons Model A, B o C
                if model == "A":
                    # Model A: 14 pts relatius des de l'entrada (SL 60 pts)
                    curr_tp = tp_pts
                    curr_sl = sl_pts
                    if ttype == "SHORT":
                        t_tp = entry_lvl - curr_tp
                        t_sl = entry_lvl + curr_sl
                    else:
                        t_tp = entry_lvl + curr_tp
                        t_sl = entry_lvl - curr_sl
                elif model == "B":
                    # Model B: TP ràpid reduït per l'offset (distància = 14 - offset, mínim 4 pts)
                    dist = max(4.0, tp_pts - offset)
                    curr_tp = dist
                    curr_sl = sl_pts
                    if ttype == "SHORT":
                        t_tp = entry_lvl - dist
                        t_sl = entry_lvl + curr_sl
                    else:
                        t_tp = entry_lvl + dist
                        t_sl = entry_lvl - curr_sl
                elif model == "C":
                    # Model C: Target de preu original absolut (SHORT: High - 14; LONG: Low + 14)
                    if ttype == "SHORT":
                        t_tp = base_lvl - tp_pts
                        t_sl = entry_lvl + sl_pts
                        curr_tp = entry_lvl - t_tp
                    else:
                        t_tp = base_lvl + tp_pts
                        t_sl = entry_lvl - sl_pts
                        curr_tp = t_tp - entry_lvl
                    curr_sl = sl_pts
                    
                # Detecció de primeres barres d'execució amb NumPy
                if ttype == "SHORT":
                    sl_hits = np.where(sub_h >= t_sl)[0]
                    tp_hits = np.where(sub_l <= t_tp)[0]
                else:
                    sl_hits = np.where(sub_l <= t_sl)[0]
                    tp_hits = np.where(sub_h >= t_tp)[0]
                    
                first_sl = sl_hits[0] if len(sl_hits) > 0 else 99999999
                first_tp = tp_hits[0] if len(tp_hits) > 0 else 99999999
                
                if first_sl < first_tp:
                    out = "LOSS"
                    pnl_pts = -curr_sl
                    exit_i = first_sl
                    dur_s = float(sub_t[exit_i] - fill_sec)
                    if ttype == "SHORT":
                        mae_pts = float(np.max(sub_h[:exit_i+1]) - entry_lvl)
                    else:
                        mae_pts = float(entry_lvl - np.min(sub_l[:exit_i+1]))
                elif first_tp < first_sl:
                    out = "WIN"
                    pnl_pts = curr_tp
                    exit_i = first_tp
                    dur_s = float(sub_t[exit_i] - fill_sec)
                    if ttype == "SHORT":
                        mae_pts = float(np.max(sub_h[:exit_i+1]) - entry_lvl)
                    else:
                        mae_pts = float(entry_lvl - np.min(sub_l[:exit_i+1]))
                else:
                    out = "EOD"
                    last_c = c_arr[-1]
                    pnl_pts = (entry_lvl - last_c) if ttype == "SHORT" else (last_c - entry_lvl)
                    dur_s = float(time_secs[-1] - fill_sec)
                    if ttype == "SHORT":
                        mae_pts = float(np.max(sub_h) - entry_lvl)
                    else:
                        mae_pts = float(entry_lvl - np.min(sub_l))
                        
                net_usd = (pnl_pts * POINT_VAL) - COMMISSION
                trades.append({
                    "date": d_str,
                    "zone": z_name,
                    "type": ttype,
                    "offset": offset,
                    "out": out,
                    "pnl_pts": pnl_pts,
                    "net_usd": net_usd,
                    "dur_s": dur_s,
                    "mae_pts": mae_pts
                })
                
        df_tr = pd.DataFrame(trades)
        if len(df_tr) == 0:
            continue
            
        n_trades = len(df_tr)
        n_wins = len(df_tr[df_tr["out"] == "WIN"])
        n_losses = len(df_tr[df_tr["out"] == "LOSS"])
        n_eod = len(df_tr[df_tr["out"] == "EOD"])
        wr = (n_wins / n_trades * 100) if n_trades > 0 else 0.0
        
        gross_win = df_tr[df_tr["net_usd"] > 0]["net_usd"].sum()
        gross_loss = abs(df_tr[df_tr["net_usd"] < 0]["net_usd"].sum())
        pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
        net_usd_tot = df_tr["net_usd"].sum()
        
        # Max Drawdown
        df_tr["cum_pnl"] = df_tr["net_usd"].cumsum()
        df_tr["peak"] = df_tr["cum_pnl"].cummax()
        df_tr["dd"] = df_tr["cum_pnl"] - df_tr["peak"]
        max_dd = abs(df_tr["dd"].min()) if len(df_tr) > 0 else 0.0
        
        win_tr = df_tr[df_tr["out"] == "WIN"]
        avg_dur_min = (win_tr["dur_s"].mean() / 60.0) if len(win_tr) > 0 else 0.0
        median_dur_min = (win_tr["dur_s"].median() / 60.0) if len(win_tr) > 0 else 0.0
        avg_mae = win_tr["mae_pts"].mean() if len(win_tr) > 0 else 0.0
        
        # Shorts vs Longs
        sh = df_tr[df_tr["type"] == "SHORT"]
        sh_wr = (len(sh[sh["out"] == "WIN"]) / len(sh) * 100) if len(sh) > 0 else 0.0
        sh_net = sh["net_usd"].sum() if len(sh) > 0 else 0.0
        
        lg = df_tr[df_tr["type"] == "LONG"]
        lg_wr = (len(lg[lg["out"] == "WIN"]) / len(lg) * 100) if len(lg) > 0 else 0.0
        lg_net = lg["net_usd"].sum() if len(lg) > 0 else 0.0
        
        rows.append({
            "model": model,
            "offset": offset,
            "trades": n_trades,
            "wins": n_wins,
            "losses": n_losses,
            "eod": n_eod,
            "wr_pct": round(wr, 1),
            "net_usd": round(net_usd_tot, 2),
            "pf": round(pf, 2),
            "max_dd": round(max_dd, 2),
            "avg_dur_min": round(avg_dur_min, 1),
            "med_dur_min": round(median_dur_min, 1),
            "avg_mae": round(avg_mae, 2),
            "sh_trades": len(sh),
            "sh_wr": round(sh_wr, 1),
            "sh_net": round(sh_net, 2),
            "lg_trades": len(lg),
            "lg_wr": round(lg_wr, 1),
            "lg_net": round(lg_net, 2)
        })
        
    return pd.DataFrame(rows)

offsets_to_test = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0, 15.0]

print("\n" + "="*115)
print("🚀 MODEL A: TP Relatiu Fix de 14.0 punts des de l'entrada (SL 60 pts)")
print("   • Entrada a London ± Offset (Guanya 14 pts de reversió, sortida més propera a la zona)")
print("="*115)
df_res_a = run_vectorized_study(offsets_to_test, model="A", tp_pts=14.0, sl_pts=60.0)
cols_disp = ["offset", "trades", "wins", "losses", "wr_pct", "net_usd", "pf", "max_dd", "avg_dur_min", "med_dur_min", "avg_mae"]
print(df_res_a[cols_disp].to_string(index=False))

print("\n" + "="*115)
print("🚀 MODEL B: TP Ultraràpid reduït (Distància TP = 14 - Offset punts)")
print("   • Aprofita el millor preu per sortir al TP en menys temps i recorregut més curt")
print("="*115)
df_res_b = run_vectorized_study(offsets_to_test, model="B", tp_pts=14.0, sl_pts=60.0)
print(df_res_b[cols_disp].to_string(index=False))

print("\n" + "="*115)
print("🚀 MODEL C: Preu Objectiu Original Fix (Guanya 14 + Offset punts)")
print("   • Target absolut al nivell de sempre (London High - 14 / London Low + 14)")
print("="*115)
df_res_c = run_vectorized_study(offsets_to_test, model="C", tp_pts=14.0, sl_pts=60.0)
print(df_res_c[cols_disp].to_string(index=False))

# Guardar resultats
os.makedirs(RESULTS_DIR, exist_ok=True)
all_summaries = pd.concat([df_res_a, df_res_b, df_res_c], ignore_index=True)
all_summaries.to_csv(os.path.join(RESULTS_DIR, "sweep_offset_study_summary.csv"), index=False)
print(f"\n💾 Resultats guardats satisfactòriament a {RESULTS_DIR}/sweep_offset_study_summary.csv")
