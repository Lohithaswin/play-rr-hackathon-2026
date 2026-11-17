"""
================================================================================
  MATCH-ON-THE-LINE DEFINITIVE ENGINE (v13.0)
  Priority: Authentic Match-Winning Performances When The Match Is On The Line
  Exclusions: Bowlers (Rashid Khan), Low-Impact All-rounders (Green), Cameos (DK, MSD)
================================================================================
"""

import pandas as pd
import numpy as np

print("Loading raw rankings tables...")
b_raw = pd.read_parquet('bat_rankings_v11.parquet')
bw = pd.read_parquet('bowl_rankings_final.parquet')

# 1. SPECIALIST BATTING FILTER: >= 750 balls faced
# Eliminates non-specialists (#8 bowlers like Rashid Khan, cameo finishers like DK and MSD)
b = b_raw[b_raw['total_balls'] >= 750].copy()

# 2. MATCH-ON-THE-LINE WEIGHTAGES:
# - Counter-Attack Chasing when match is on the line (RRR >= 10.0): 24%
# - Crisis Collapse Rescue (early <= 2 wkts down): 20%
# - Quality Win WPA (impact in team victories against elite teams): 20%
# - Authentic Match-Winning Pressure Performances (authentic_mwpp): 14%
# - Death Chase Finishing (overs 16-20 with margin < 36): 12%
# - Pressure Consistency Rate: 10%
weights_bat = {
    'S_ca': 0.24,
    'S_rescue': 0.20,
    'S_win_wpa': 0.20,
    'S_mwpp': 0.14,
    'S_da': 0.12,
    'S_consistency': 0.10
}

# Strict Non-Compensatory Flaw Penalties:
# - Negative Crisis Rescue: penalized at 7.5x (demoting collapse liabilities like Shubman Gill)
# - Negative Death Finishing: penalized at 3.0x
b['flaw_deductions'] = (
    b['rescue_wpa'].apply(lambda x: abs(x) * 7.5 if x < 0 else 0.0) +
    b['da_wpa'].apply(lambda x: abs(x) * 3.0 if x < 0 else 0.0)
)
b['fair_deductions'] = b['flaw_deductions']

b['raw_score'] = sum(b[k] * w for k, w in weights_bat.items())
b['batting_clutch_score'] = np.clip(b['raw_score'] * b['reliability'] - b['flaw_deductions'], 0, 100)
b = b.sort_values(by='batting_clutch_score', ascending=False).reset_index(drop=True)
b['rank_bat'] = b.index + 1

# Save Batting Master Dataset
b.to_parquet('bat_rankings_final.parquet', index=False)
b.to_csv('bat_final_transparent.csv', index=False)
print("Saved bat_rankings_final.parquet & bat_final_transparent.csv")

# Save Bowling Master Dataset (already perfectly aligned)
bw.to_parquet('bowl_rankings_final.parquet', index=False)
bw.to_csv('bowl_final_transparent.csv', index=False)
print("Saved bowl_rankings_final.parquet & bowl_final_transparent.csv")

# Print verification
print("\n=== TOP 10 BATTERS (MATCH ON THE LINE MASTER ENGINE) ===")
print(b[['rank_bat', 'striker_name', 'batting_clutch_score', 'total_balls', 'authentic_mwpp', 'win_successive_matches', 'ca_wpa', 'rescue_wpa', 'da_wpa', 'hp_consistency_rate', 'fair_deductions']].head(10).to_string())

print("\n=== IMMEDIATE RESERVES & EXCLUSIONS ===")
print(b[['rank_bat', 'striker_name', 'batting_clutch_score', 'total_balls', 'authentic_mwpp', 'win_successive_matches', 'ca_wpa', 'rescue_wpa', 'fair_deductions']].iloc[10:14].to_string())
