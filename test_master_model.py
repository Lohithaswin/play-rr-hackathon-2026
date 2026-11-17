import pandas as pd
import numpy as np

b = pd.read_parquet('bat_rankings_final.parquet')
bw = pd.read_parquet('bowl_rankings_final.parquet')

# Batting 3-Tier Model:
# Tier 1: Macro Stakes & Opposition (25%) -> S_must_win: 15%, S_win_wpa: 10%
# Tier 2: Match-Level Consistency & Wins (30%) -> S_win_matches: 15%, S_consistency: 15%
# Tier 3: In-Match Dynamic Leverage & Phases (45%) -> S_ca: 16%, S_rescue: 14%, S_da: 10%, S_elevation: 5%
weights_bat = {
    'S_must_win': 0.15,
    'S_win_wpa': 0.10,
    'S_win_matches': 0.15,
    'S_consistency': 0.15,
    'S_ca': 0.16,
    'S_rescue': 0.14,
    'S_da': 0.10,
    'S_elevation': 0.05
}

b['raw_score'] = sum(b[k] * w for k, w in weights_bat.items())
b['batting_clutch_score'] = np.clip(b['raw_score'] * b['reliability'] - b['fair_deductions'], 0, 100)
b = b.sort_values(by='batting_clutch_score', ascending=False).reset_index(drop=True)
b['rank_bat'] = b.index + 1

print('=== MASTER 3-TIER BATTING RANKINGS ===')
for idx, r in b.head(12).iterrows():
    print(f"{r['rank_bat']}. {r['striker_name']}: Score={r['batting_clutch_score']:.1f}, Cons={r['hp_consistency_rate']*100:.1f}%, WinMatches={r['win_successive_matches']:.0f}, CA={r['ca_wpa']:+.2f}, Rescue={r['rescue_wpa']:+.2f}, Death={r['da_wpa']:+.2f}, Ded={r['fair_deductions']:.1f}")

# Bowling 3-Tier Model:
# Tier 1: Macro Opposition Calibration (20%) -> S_runs_saved: 20%
# Tier 2: Match Consistency & Clutch Breakthroughs (26%) -> S_consistency: 16%, S_wkts: 10%
# Tier 3: In-Match Dynamic Phases & Dots (54%) -> S_dots: 20%, S_eco: 12%, S_wpa: 8%, S_yorkers: 4%, ml_total_pos: 20%
# Bowling already has calibrated components:
print('\n=== MASTER 3-TIER BOWLING RANKINGS ===')
for idx, r in bw.head(12).iterrows():
    print(f"{r['rank_bowl']}. {r['bowler_name']}: Score={r['bowling_clutch_score']:.1f}, Cons={r['hp_consistency_rate']*100:.1f}%, PP_Saved={r['ml_pp_runs_saved']:+.1f}, Mid_Saved={r['ml_mid_runs_saved']:+.1f}, Death_Saved={r['ml_death_runs_saved']:+.1f}, MinnowRatio={r['minnow_ratio']*100:.1f}%, Ded={r['fair_deductions']:.1f}")
