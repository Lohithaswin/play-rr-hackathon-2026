import pandas as pd, numpy as np
bat = pd.read_parquet('bat_rankings_v4.parquet')
bowl = pd.read_parquet('bowl_rankings_v4.parquet')
bt = bat.sort_values('batting_clutch_score', ascending=False).head(10)
bw = bowl.sort_values('bowling_clutch_score', ascending=False).head(10)

print('=== TOP 10 BATTERS (v4) ===')
for i, r in bt.reset_index(drop=True).iterrows():
    name = r['striker_name']
    print(f"  #{i+1:2d}: {name:<26} SR={r['sr']:.1f} Avg={r['avg']:.1f} WPA={r['wpa']:.2f} "
          f"DA_WPA={r['da_wpa']:.2f} ChokeDis={int(r['choke_dismissals'])} "
          f"CB={int(r['comeback_inn'])} Rel={int(r['release_moments'])} "
          f"Score={r['batting_clutch_score']:.2f}")

print()
print('=== TOP 10 BOWLERS (v4) ===')
for i, r in bw.reset_index(drop=True).iterrows():
    name = r['bowler_name']
    print(f"  #{i+1:2d}: {name:<26} Eco={r['economy']:.2f} Wkts={int(r['wkts'])} "
          f"WPA={r['wpa']:.2f} DA_WPA={r['da_wpa']:.2f} "
          f"SD={int(r['shutdown_overs'])} CB={int(r['comeback_spells'])} "
          f"Score={r['bowling_clutch_score']:.2f}")
