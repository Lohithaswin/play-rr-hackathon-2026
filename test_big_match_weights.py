import pandas as pd
import numpy as np

b = pd.read_parquet('bat_rankings_final.parquet')

# Test weights: 0% raw volume, 16% consistency, 30% big match impact (15% KO + 15% Win Matches), 15% Quality Win WPA, 16% CA, 12% Rescue, 8% Death, 3% SR Elevation
weights = {
    'S_win_wpa': 0.15,
    'S_win_matches': 0.15,
    'S_must_win': 0.15,
    'S_consistency': 0.16,
    'S_ca': 0.16,
    'S_rescue': 0.12,
    'S_da': 0.08,
    'S_elevation': 0.03
}

b_new = b.copy()
b_new['raw_clutch'] = sum(b_new[k] * w for k, w in weights.items())
b_new['batting_clutch_score'] = np.clip(b_new['raw_clutch'] * b_new['reliability'] - b_new['fair_deductions'], 0, 100)
b_new = b_new.sort_values(by='batting_clutch_score', ascending=False).reset_index(drop=True)
b_new['rank_bat'] = b_new.index + 1

print('=== REFINED TOP 15 BATTERS (ZERO VOLUME, HIGH BIG MATCH + HIGH CONSISTENCY) ===')
for idx, r in b_new.head(15).iterrows():
    print(f"{r['rank_bat']}. {r['striker_name']}: Score={r['batting_clutch_score']:.1f}, Consistency={r['hp_consistency_rate']*100:.1f}%, WinMatches={r['win_successive_matches']:.0f}, KO_Wins={r['must_win_hp_wins']:.0f}, CA_WPA={r['ca_wpa']:+.2f}, Rescue={r['rescue_wpa']:+.2f}, Ded={r['fair_deductions']:.1f}")
