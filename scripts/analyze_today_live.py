import json
import pandas as pd
from datetime import datetime
import zoneinfo

with open("/Users/guillemriusviladomiu/.gemini/workspaces-antigravity/backtest-master-pro-2026/data/nq_today.json", "r") as f:
    data = json.load(f)

result = data["chart"]["result"][0]
timestamps = result["timestamp"]
quote = result["indicators"]["quote"][0]

df = pd.DataFrame({
    "timestamp": pd.to_datetime(timestamps, unit="s", utc=True),
    "open": quote["open"],
    "high": quote["high"],
    "low": quote["low"],
    "close": quote["close"],
    "volume": quote["volume"]
})

df = df.dropna().reset_index(drop=True)

ny_tz = zoneinfo.ZoneInfo("America/New_York")
df["dt_ny"] = df["timestamp"].dt.tz_convert(ny_tz)

today_str = df["dt_ny"].iloc[-1].strftime("%Y-%m-%d")
today_df = df[df["dt_ny"].dt.strftime("%Y-%m-%d") == today_str].copy()
print(f"Data for today ({today_str}) | Total bars: {len(today_df)}")
print(f"Time range today: {today_df['dt_ny'].iloc[0].strftime('%H:%M')} EDT to {today_df['dt_ny'].iloc[-1].strftime('%H:%M')} EDT")

t_0200 = datetime.strptime("02:00", "%H:%M").time()
t_0500 = datetime.strptime("05:00", "%H:%M").time()

london_session = today_df[(today_df["dt_ny"].dt.time >= t_0200) & (today_df["dt_ny"].dt.time < t_0500)]

if len(london_session) > 0:
    lon_high = london_session["high"].max()
    lon_low = london_session["low"].min()
    lon_high_time = london_session.loc[london_session["high"].idxmax()]["dt_ny"]
    lon_low_time = london_session.loc[london_session["low"].idxmin()]["dt_ny"]
    print(f"\n--- SESSIÓ LONDRES (02:00 - 05:00 EDT / 08:00 - 11:00 CEST) ---")
    print(f"London High: {lon_high:.2f} a les {lon_high_time.strftime('%H:%M')} EDT ({lon_high_time.tz_convert('Europe/Madrid').strftime('%H:%M')} CEST)")
    print(f"London Low:  {lon_low:.2f} a les {lon_low_time.strftime('%H:%M')} EDT ({lon_low_time.tz_convert('Europe/Madrid').strftime('%H:%M')} CEST)")
    print(f"London Range: {lon_high - lon_low:.2f} punts")
    
    post_london = today_df[today_df["dt_ny"].dt.time >= t_0500].copy()
    
    touch_high = post_london[post_london["high"] >= lon_high]
    if len(touch_high) > 0:
        first_touch_idx = touch_high.index[0]
        first_touch = post_london.loc[first_touch_idx]
        first_touch_time = first_touch["dt_ny"]
        print(f"\n🚨 FIRST TOUCH LONDON HIGH ({lon_high:.2f}):")
        print(f"Hora de toc: {first_touch_time.strftime('%H:%M:%S')} EDT ({first_touch_time.tz_convert('Europe/Madrid').strftime('%H:%M:%S')} CEST)")
        print(f"Barra entrada: O={first_touch['open']:.2f}, H={first_touch['high']:.2f}, L={first_touch['low']:.2f}, C={first_touch['close']:.2f}")
        
        trade_bars = post_london.loc[first_touch_idx:].copy()
        print("\n--- EVOLUCIÓ MINUT A MINUT DES DE L'ENTRADA EN SHORT ---")
        sl_levels = [30, 40, 50, 60]
        tp_levels = [10, 12, 15]
        
        max_runup = 0.0
        max_profit = 0.0
        
        hit_tp = {}
        hit_sl = {}
        
        count = 0
        for idx, row in trade_bars.iterrows():
            count += 1
            t_ny = row["dt_ny"].strftime("%H:%M")
            t_es = row["dt_ny"].tz_convert("Europe/Madrid").strftime("%H:%M")
            high_diff = row["high"] - lon_high  # Runup adverse
            low_diff = lon_high - row["low"]   # Profit favorable
            
            if high_diff > max_runup:
                max_runup = high_diff
            if low_diff > max_profit:
                max_profit = low_diff
                
            for tp in tp_levels:
                if tp not in hit_tp and row["low"] <= lon_high - tp:
                    hit_tp[tp] = (t_ny, t_es, row['low'])
            for sl in sl_levels:
                if sl not in hit_sl and row["high"] >= lon_high + sl:
                    hit_sl[sl] = (t_ny, t_es, row['high'])
                    
            print(f"{t_ny} EDT ({t_es} CEST) | O:{row['open']:.1f} H:{row['high']:.1f} L:{row['low']:.1f} C:{row['close']:.1f} | Fav:{low_diff:+.1f} | Adv:{high_diff:+.1f}")
                
        print("\n--- RESULTATS DETALLATS ---")
        print(f"Màxima excursió favorable (a favor de Short): +{max_profit:.2f} punts")
        print(f"Màxima excursió adversa (en contra de Short): +{max_runup:.2f} punts")
        for tp in tp_levels:
            print(f"TP {tp} pts: {'HIT a ' + hit_tp[tp][1] + ' CEST' if tp in hit_tp else 'NO ASSOLIT'}")
        for sl in sl_levels:
            print(f"SL {sl} pts: {'SALTAT a ' + hit_sl[sl][1] + ' CEST' if sl in hit_sl else 'NO TOCAT'}")
    else:
        print("London High NOT touched yet.")
else:
    print("No London session bars found.")
