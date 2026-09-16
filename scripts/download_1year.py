#!/usr/bin/env python3
import sys
import os
from datetime import datetime
import databento as db
import pandas as pd

API_KEY = "db-uAGgYJvtrenJEYV34RCb7t8jSqDyb"
DATASET = "GLBX.MDP3"
SYMBOL = "MNQ.c.0"
SCHEMA = "ohlcv-1m"
START = "2025-09-15"
END = "2026-09-15"
MAX_ALLOWED_COST = 3.00  # Safety threshold in USD

OUTPUT_DIR = "/Users/guillemriusviladomiu/.gemini/workspaces-antigravity/backtest-master-pro-2026/data"
OUTPUT_PARQUET = os.path.join(OUTPUT_DIR, "mnq_1m_1year.parquet")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "mnq_1m_1year.csv")

print(f"{'='*60}")
print(f"📡 DATABENTO DOWNLOADER: {SYMBOL} ({SCHEMA})")
print(f"📅 Rang: {START} -> {END}")
print(f"{'='*60}")

client = db.Historical(key=API_KEY)

# 1. Comprovació estricta de cost
try:
    cost = client.metadata.get_cost(
        dataset=DATASET,
        symbols=[SYMBOL],
        schema=SCHEMA,
        start=START,
        end=END,
        stype_in="continuous"
    )
    print(f"💰 Cost calculat per Databento: ${cost:.4f} USD")
except Exception as e:
    print(f"❌ Error al consultar el cost: {e}")
    sys.exit(1)

if cost > MAX_ALLOWED_COST:
    print(f"⛔ ALERTA: El cost (${cost:.4f}) supera el límit de seguretat (${MAX_ALLOWED_COST:.2f})!")
    sys.exit(1)

print(f"✅ Cost verificat i segur (${cost:.4f} <= ${MAX_ALLOWED_COST:.2f}). Procedint a la descàrrega...")

# 2. Descàrrega
try:
    data = client.timeseries.get_range(
        dataset=DATASET,
        symbols=[SYMBOL],
        schema=SCHEMA,
        start=START,
        end=END,
        stype_in="continuous"
    )
    df = data.to_df()
    print(f"✅ Descàrrega completada! {len(df):,} barres obtingudes.")
except Exception as e:
    print(f"❌ Error durant la descàrrega: {e}")
    sys.exit(1)

# 3. Processament i neteja
print("🔄 Netejant i convertint timestamps...")
df = df.reset_index()
ts_col = None
for col in ['ts_event', 'timestamp', 'datetime', 'index']:
    if col in df.columns:
        ts_col = col
        break
if ts_col is None:
    ts_col = df.select_dtypes(include=['datetime64']).columns[0]

df['datetime'] = pd.to_datetime(df[ts_col], utc=True)
df['ny_time'] = df['datetime'].dt.tz_convert('America/New_York')
df = df.sort_values('datetime').drop_duplicates(subset='datetime')

# Guardar en parquet i CSV
df.to_parquet(OUTPUT_PARQUET, index=False)
print(f"💾 Guardat a Parquet: {OUTPUT_PARQUET}")

# Guardar versió compacta en CSV
cols = ['datetime', 'ny_time', 'open', 'high', 'low', 'close', 'volume']
available_cols = [c for c in cols if c in df.columns]
df[available_cols].to_csv(OUTPUT_CSV, index=False)
print(f"💾 Guardat a CSV: {OUTPUT_CSV}")
print(f"🎉 Procés finalitzat amb èxit! Dades llestes per al backtest.")
