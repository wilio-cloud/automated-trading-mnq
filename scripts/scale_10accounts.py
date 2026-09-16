#!/usr/bin/env python3
print("="*115)
print(f"{'Comptes':10s} | {'4 MNQ Només Londres':24s} | {'3 MNQ Àsia + Londres':24s} | {'5 MNQ Només Londres':24s} | {'1 NQ Burn & Replace':22s}")
print(f"{'':10s} | {'Anual (Mitjana/mes)':24s} | {'Anual (Mitjana/mes)':24s} | {'Anual (Mitjana/mes)':24s} | {'Anual (Mitjana/mes)':22s}")
print("="*115)

# Per account net values:
# 4 MNQ London: $20,080
# 3 MNQ Asia+Lon: $22,200
# 5 MNQ London: $25,100
# 1 NQ Burn&Replace: $58,260 (taking into account fees & resets)

for n in range(1, 11):
    f_4m = n * 20080
    f_4m_m = f_4m / 12
    
    f_3m = n * 22200
    f_3m_m = f_3m / 12
    
    f_5m = n * 25100
    f_5m_m = f_5m / 12
    
    f_1nq = n * 58260
    f_1nq_m = f_1nq / 12
    
    print(f"{n:2d} comptes  | ${f_4m:8,d} (${f_4m_m:6,.0f}/m)    | ${f_3m:8,d} (${f_3m_m:6,.0f}/m)    | ${f_5m:8,d} (${f_5m_m:6,.0f}/m)    | ${f_1nq:8,d} (${f_1nq_m:6,.0f}/m)")
