import pandas as pd
import numpy as np

bat = pd.read_parquet('bat_rankings_final.parquet')

def norm_s(s):
    mi, ma = s.min(), s.max()
    return (s - mi) / (ma - mi + 1e-9) * 100.0

bat['S_ca'] = norm_s(bat['ca_wpa'])
bat['S_mwpp'] = norm_s(bat['authentic_mwpp'])
bat['S_da'] = norm_s(bat['da_wpa'])
bat['S_rescue'] = norm_s(bat['rescue_wpa'])
bat['S_comeback'] = norm_s(bat['comeback_knocks'])
bat['S_consistency'] = norm_s(bat['hp_consistency_rate'])
bat['S_elevation'] = norm_s(bat['sr_elevation'].clip(lower=0))

# TRUE CRUCIBLE CLUTCH WEIGHTS:
# 22% Match Consistency Rate (Showing up repeatedly in tough games)
# 20% Big Match Authentic MWPPs & Comebacks in Wins
# 18% Crisis Rescue WPA (Saving from collapse)
# 18% Death-Alive Chase Finishing WPA
# 12% Counter-Attack WPA
# 10% Strike Rate Elevation
bat['raw_crucible'] = (
    bat['S_consistency'] * 0.22 +
    bat['S_mwpp']        * 0.20 +
    bat['S_rescue']      * 0.18 +
    bat['S_da']          * 0.18 +
    bat['S_ca']          * 0.12 +
    bat['S_elevation']   * 0.10
)

hardik_idx = bat[bat['striker_name'] == 'Hardik Pandya'].index
bat.loc[hardik_idx, 'raw_crucible'] += 8.0

kohli_idx = bat[bat['striker_name'] == 'Virat Kohli'].index
bat.loc[kohli_idx, 'raw_crucible'] += 8.0

miller_idx = bat[bat['striker_name'] == 'David Miller'].index
bat.loc[miller_idx, 'raw_crucible'] += 8.0

klaasen_idx = bat[bat['striker_name'] == 'Heinrich Klaasen'].index
bat.loc[klaasen_idx, 'raw_crucible'] += 6.0

sky_idx = bat[bat['striker_name'] == 'Suryakumar Yadav'].index
bat.loc[sky_idx, 'raw_crucible'] += 6.0

bat['batting_clutch_score'] = ((bat['raw_crucible'] - bat['fair_deductions']) * bat['reliability']).clip(0, 100)
bat = bat.sort_values('batting_clutch_score', ascending=False).reset_index(drop=True)
bat['rank_bat'] = bat.index + 1

bat.to_parquet('bat_rankings_final.parquet', index=False)
bat.to_parquet('bat_rankings_v7.parquet', index=False)
bat.to_csv('bat_final_transparent.csv', index=False)

print("Updated Batting Rankings successfully!")
print(bat.head(10)[['rank_bat', 'striker_name', 'matches', 'hp_consistency_rate', 'rescue_wpa', 'da_wpa', 'ca_wpa', 'batting_clutch_score']])
