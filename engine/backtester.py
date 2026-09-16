#!/usr/bin/env python3
"""
NQ Zones Reversal Backtesting Engine
Sessions:
  - Asia:   20:00 - 00:00 (EDT / UTC-4) -> Sell Limit @ Asia High, Buy Limit @ Asia Low placed at 00:00
  - London: 02:00 - 05:00 (EDT / UTC-4) -> Sell Limit @ London High, Buy Limit @ London Low placed at 05:00
  - Active Window: Orders valid until 17:00 EDT.
  - Rule: 1 trade per level per day (consumed once touched).
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta

class NQZonesBacktester:
    def __init__(self, data_path, tp_points=10.0, sl_points=30.0, point_value=20.0):
        self.data_path = data_path
        self.tp_points = tp_points
        self.sl_points = sl_points
        self.point_value = point_value
        self.df = None
        self.trades = []
        self._load_data()

    def _load_data(self):
        print(f"Loading data from {self.data_path}...")
        if self.data_path.endswith('.parquet'):
            self.df = pd.read_parquet(self.data_path)
        else:
            self.df = pd.read_csv(self.data_path)
            
        if 'ny_time' in self.df.columns:
            self.df.index = pd.to_datetime(self.df['ny_time'])
        elif 'datetime' in self.df.columns:
            self.df.index = pd.to_datetime(self.df['datetime']).dt.tz_convert('America/New_York')
        else:
            if not isinstance(self.df.index, pd.DatetimeIndex):
                self.df.index = pd.to_datetime(self.df.index)
            if self.df.index.tz is None:
                self.df.index = self.df.index.tz_localize('UTC').tz_convert('America/New_York')
            else:
                self.df.index = self.df.index.tz_convert('America/New_York')
        
        # Standardize column names to capitalize
        col_map = {c: c.capitalize() for c in self.df.columns}
        self.df.rename(columns=col_map, inplace=True)
        self.df = self.df.sort_index()
        
        # Precompute trading dates and hours for speed
        # If hour >= 18, it belongs to the NEXT trading day
        hours = self.df.index.hour
        dates = self.df.index.date
        trading_dates = []
        for dt, h in zip(self.df.index, hours):
            if h >= 18:
                t_date = (dt + pd.Timedelta(days=1)).date()
                if t_date.weekday() == 6: # Sunday belongs to Monday
                    t_date = t_date + pd.Timedelta(days=1)
            else:
                t_date = dt.date()
            trading_dates.append(t_date)
            
        self.df['trading_date'] = trading_dates
        self.df['hour'] = hours
        self.df['minute'] = self.df.index.minute
        
        print(f"Data ready: {len(self.df):,} 1m bars from {self.df.index[0]} to {self.df.index[-1]}")

    def run(self, tp=None, sl=None):
        if tp is not None:
            self.tp_points = tp
        if sl is not None:
            self.sl_points = sl

        trades = []
        df = self.df

        # Group by trading date
        grouped = df.groupby('trading_date')
        
        for t_date, day_bars in grouped:
            if len(day_bars) < 60:
                continue

            # 1. Detect Asia session: prev evening 20:00 to 00:00 (hours 20, 21, 22, 23)
            asia_bars = day_bars[day_bars['hour'] >= 20]
            if len(asia_bars) == 0:
                continue

            asia_high = asia_bars['High'].max()
            asia_low = asia_bars['Low'].min()

            # Orders dict
            orders = {
                'Asia High': {
                    'type': 'SHORT',
                    'level': asia_high,
                    'tp': asia_high - self.tp_points,
                    'sl': asia_high + self.sl_points,
                    'active_from_h': 0,
                    'status': 'PENDING',
                    'session': 'ASIA'
                },
                'Asia Low': {
                    'type': 'LONG',
                    'level': asia_low,
                    'tp': asia_low + self.tp_points,
                    'sl': asia_low - self.sl_points,
                    'active_from_h': 0,
                    'status': 'PENDING',
                    'session': 'ASIA'
                }
            }

            # 2. Detect London session: 02:00 to 05:00 (hours 2, 3, 4)
            london_bars = day_bars[(day_bars['hour'] >= 2) & (day_bars['hour'] < 5)]
            if len(london_bars) > 0:
                london_high = london_bars['High'].max()
                london_low = london_bars['Low'].min()
                orders['London High'] = {
                    'type': 'SHORT',
                    'level': london_high,
                    'tp': london_high - self.tp_points,
                    'sl': london_high + self.sl_points,
                    'active_from_h': 5,
                    'status': 'PENDING',
                    'session': 'LONDON'
                }
                orders['London Low'] = {
                    'type': 'LONG',
                    'level': london_low,
                    'tp': london_low + self.tp_points,
                    'sl': london_low - self.sl_points,
                    'active_from_h': 5,
                    'status': 'PENDING',
                    'session': 'LONDON'
                }

            # 3. Step through trading day bars from 00:00 to 17:00
            active_bars = day_bars[day_bars['hour'] < 17]
            
            for bar_time, bar in active_bars.iterrows():
                b_hour = bar['hour']
                b_min = bar['minute']

                for name, o in orders.items():
                    if o['status'] == 'PENDING':
                        if b_hour >= o['active_from_h']:
                            # Check fill
                            if o['type'] == 'SHORT' and bar['High'] >= o['level']:
                                o['status'] = 'OPEN'
                                o['entry_time'] = bar_time
                                o['entry_price'] = o['level']
                                # Conservative intra-bar evaluation
                                if bar['High'] >= o['sl']:
                                    o['status'] = 'CLOSED'
                                    o['exit_time'] = bar_time
                                    o['exit_price'] = o['sl']
                                    o['result'] = 'SL'
                                    o['pnl_pts'] = -self.sl_points
                                    trades.append(self._record_trade(t_date, name, o))
                                elif bar['Low'] <= o['tp']:
                                    o['status'] = 'CLOSED'
                                    o['exit_time'] = bar_time
                                    o['exit_price'] = o['tp']
                                    o['result'] = 'TP'
                                    o['pnl_pts'] = self.tp_points
                                    trades.append(self._record_trade(t_date, name, o))

                            elif o['type'] == 'LONG' and bar['Low'] <= o['level']:
                                o['status'] = 'OPEN'
                                o['entry_time'] = bar_time
                                o['entry_price'] = o['level']
                                if bar['Low'] <= o['sl']:
                                    o['status'] = 'CLOSED'
                                    o['exit_time'] = bar_time
                                    o['exit_price'] = o['sl']
                                    o['result'] = 'SL'
                                    o['pnl_pts'] = -self.sl_points
                                    trades.append(self._record_trade(t_date, name, o))
                                elif bar['High'] >= o['tp']:
                                    o['status'] = 'CLOSED'
                                    o['exit_time'] = bar_time
                                    o['exit_price'] = o['tp']
                                    o['result'] = 'TP'
                                    o['pnl_pts'] = self.tp_points
                                    trades.append(self._record_trade(t_date, name, o))

                    elif o['status'] == 'OPEN':
                        # Position already open
                        if o['type'] == 'SHORT':
                            if bar['High'] >= o['sl']:
                                o['status'] = 'CLOSED'
                                o['exit_time'] = bar_time
                                o['exit_price'] = o['sl']
                                o['result'] = 'SL'
                                o['pnl_pts'] = -self.sl_points
                                trades.append(self._record_trade(t_date, name, o))
                            elif bar['Low'] <= o['tp']:
                                o['status'] = 'CLOSED'
                                o['exit_time'] = bar_time
                                o['exit_price'] = o['tp']
                                o['result'] = 'TP'
                                o['pnl_pts'] = self.tp_points
                                trades.append(self._record_trade(t_date, name, o))
                        elif o['type'] == 'LONG':
                            if bar['Low'] <= o['sl']:
                                o['status'] = 'CLOSED'
                                o['exit_time'] = bar_time
                                o['exit_price'] = o['sl']
                                o['result'] = 'SL'
                                o['pnl_pts'] = -self.sl_points
                                trades.append(self._record_trade(t_date, name, o))
                            elif bar['High'] >= o['tp']:
                                o['status'] = 'CLOSED'
                                o['exit_time'] = bar_time
                                o['exit_price'] = o['tp']
                                o['result'] = 'TP'
                                o['pnl_pts'] = self.tp_points
                                trades.append(self._record_trade(t_date, name, o))

                # End of day 16:59: Close open trades
                if b_hour == 16 and b_min >= 55:
                    for name, o in orders.items():
                        if o['status'] == 'OPEN':
                            o['status'] = 'CLOSED'
                            o['exit_time'] = bar_time
                            o['exit_price'] = bar['Close']
                            o['result'] = 'EOD'
                            if o['type'] == 'LONG':
                                o['pnl_pts'] = bar['Close'] - o['entry_price']
                            else:
                                o['pnl_pts'] = o['entry_price'] - bar['Close']
                            trades.append(self._record_trade(t_date, name, o))
                    break

        self.trades = pd.DataFrame(trades)
        return self.trades

    def _record_trade(self, t_date, name, o):
        return {
            'date': t_date,
            'zone': name,
            'session': o['session'],
            'type': o['type'],
            'entry_time': o.get('entry_time'),
            'exit_time': o.get('exit_time'),
            'entry_price': o.get('entry_price'),
            'exit_price': o.get('exit_price'),
            'result': o.get('result'),
            'pnl_pts': round(o.get('pnl_pts', 0.0), 2),
            'pnl_usd': round(o.get('pnl_pts', 0.0) * self.point_value, 2)
        }

    def compute_stats(self):
        if len(self.trades) == 0:
            return {'total_trades': 0}

        df = self.trades.copy()
        total = len(df)
        wins = df[df['pnl_pts'] > 0]
        losses = df[df['pnl_pts'] < 0]
        eod = df[df['result'] == 'EOD']

        win_rate = len(wins) / total * 100 if total > 0 else 0
        total_pnl_pts = df['pnl_pts'].sum()
        total_pnl_usd = df['pnl_usd'].sum()
        gross_profit = wins['pnl_usd'].sum()
        gross_loss = abs(losses['pnl_usd'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999.0

        df['cum_pnl'] = df['pnl_usd'].cumsum()
        df['peak'] = df['cum_pnl'].cummax()
        df['drawdown'] = df['cum_pnl'] - df['peak']
        max_dd = abs(df['drawdown'].min())

        avg_trade_usd = df['pnl_usd'].mean()

        return {
            'total_trades': total,
            'win_rate': round(win_rate, 2),
            'wins': len(wins),
            'losses': len(losses),
            'eod_exits': len(eod),
            'total_pnl_pts': round(total_pnl_pts, 2),
            'total_pnl_usd': round(total_pnl_usd, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown_usd': round(max_dd, 2),
            'avg_trade_usd': round(avg_trade_usd, 2)
        }

if __name__ == '__main__':
    parquet_path = '/Users/guillemriusviladomiu/.gemini/workspaces-antigravity/backtest-master-pro-2026/data/mnq_1m_1year.parquet'
    engine = NQZonesBacktester(parquet_path, tp_points=10, sl_points=30)
    trades = engine.run()
    print(f"\n✅ Simulation completed! Total trades: {len(trades)}")
    stats = engine.compute_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
