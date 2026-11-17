import pandas as pd
import numpy as np

valid = pd.read_parquet('valid_v7_ml.parquet')
mat = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')

valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['bowling_team_won'] = 1 - valid['batting_team_won']
valid['stakes'] = valid['match_importance'].fillna(1.0).clip(lower=1.0)
valid['is_alive_hp'] = (valid['match_alive'] == True) & (
    (valid['is_high_pressure'] == 1) | (valid['over_num'] >= 17) | (valid['leverage_index'] >= 1.20)
)

def norm(s):
    mi, ma = s.min(), s.max()
    return (s - mi) / (ma - mi + 1e-9) * 100.0

# Batting
valid['hp_runs_col'] = valid['runs'] * valid['is_alive_hp']
valid['hp_balls_col'] = valid['valid_flag'] * valid['is_alive_hp']
valid['hp_wpa_col'] = valid['wpa_bat_v5'] * valid['is_alive_hp'] * valid['stakes']
valid['da_wpa_col'] = valid['wpa_bat_v5'] * valid['bucket_chase_death_alive'] * valid['stakes']
valid['ca_wpa_col'] = valid['wpa_bat_v5'] * valid['is_counter_attack_ball'] * valid['stakes']
valid['rescue_wpa_col'] = valid['wpa_bat_v5'] * valid['rescue_ball'] * valid['stakes']

bat_m = valid.groupby(['match_id', 'innings', 'striker_id', 'striker_name', 'batting_team_won', 'comp_name', 'season'], as_index=False).agg({
    'runs': 'sum', 'valid_flag': 'sum',
    'hp_runs_col': 'sum', 'hp_balls_col': 'sum', 'hp_wpa_col': 'sum',
    'da_wpa_col': 'sum', 'ca_wpa_col': 'sum', 'rescue_wpa_col': 'sum',
    'wp_before': 'min'
}).rename(columns={
    'runs':'total_runs', 'valid_flag':'total_balls',
    'hp_runs_col':'hp_runs', 'hp_balls_col':'hp_balls', 'hp_wpa_col':'hp_wpa',
    'da_wpa_col':'da_wpa', 'ca_wpa_col':'ca_wpa', 'rescue_wpa_col':'rescue_wpa',
    'wp_before':'min_wp'
})

bat_m['total_sr'] = bat_m['total_runs'] / bat_m['total_balls'].clip(lower=1) * 100.0
bat_m['hp_sr'] = bat_m['hp_runs'] / bat_m['hp_balls'].clip(lower=1) * 100.0

bat_m['is_comeback_knock'] = (bat_m['batting_team_won'] == 1) & (bat_m['min_wp'] <= 0.35) & (bat_m['total_runs'] >= 25) & (bat_m['hp_wpa'] >= 0.75)
c1 = (bat_m['hp_balls'] >= 8) & (bat_m['hp_runs'] >= 16) & (bat_m['hp_sr'] >= 135.0) & (bat_m['hp_wpa'] >= 0.50)
c2 = (bat_m['rescue_wpa'] >= 1.50) & (bat_m['total_runs'] >= 25) & (bat_m['total_sr'] >= 125.0)
c3 = (bat_m['innings'] == 2) & (bat_m['batting_team_won'] == 1) & (bat_m['da_wpa'] >= 1.20) & (bat_m['total_sr'] >= 175.0)
bat_m['is_authentic_hp'] = (c1 | c2 | c3).astype(int)

# Batting match-by-match consistency
bat_m_cons = valid[valid['is_alive_hp'] == 1].groupby(['match_id', 'striker_id', 'striker_name'], as_index=False).agg({
    'hp_runs_col': 'sum', 'hp_balls_col': 'sum', 'hp_wpa_col': 'sum'
}).rename(columns={'hp_runs_col':'hp_runs', 'hp_balls_col':'hp_balls', 'hp_wpa_col':'hp_wpa'})
bat_m_cons['hp_sr'] = bat_m_cons['hp_runs'] / bat_m_cons['hp_balls'].clip(lower=1) * 100.0
bat_m_cons['is_positive_hp'] = (
    (bat_m_cons['hp_wpa'] > 0) |
    ((bat_m_cons['hp_runs'] >= 15) & (bat_m_cons['hp_sr'] >= 135.0))
).astype(int)
bat_cons = bat_m_cons.groupby(['striker_id', 'striker_name'], as_index=False).agg({
    'match_id': 'count', 'is_positive_hp': 'sum'
}).rename(columns={'match_id': 'hp_matches_faced', 'is_positive_hp': 'hp_matches_positive'})
bat_cons['hp_consistency_rate'] = bat_cons['hp_matches_positive'] / bat_cons['hp_matches_faced'].clip(lower=1)

p_bat = bat_m.groupby(['striker_id', 'striker_name'], as_index=False).agg({
    'is_authentic_hp': 'sum', 'is_comeback_knock': 'sum',
    'hp_runs': 'sum', 'hp_balls': 'sum', 'hp_wpa': 'sum',
    'total_runs': 'sum', 'total_balls': 'sum',
    'da_wpa': 'sum', 'ca_wpa': 'sum', 'rescue_wpa': 'sum',
    'match_id': 'count'
}).rename(columns={'is_authentic_hp': 'authentic_mwpp', 'is_comeback_knock': 'comeback_knocks', 'match_id': 'matches'})

p_bat = p_bat.merge(bat_cons[['striker_id', 'hp_consistency_rate', 'hp_matches_faced']], on='striker_id', how='left').fillna(0)
p_bat = p_bat[p_bat['matches'] >= 45].copy()
p_bat['total_sr'] = p_bat['total_runs'] / p_bat['total_balls'].clip(lower=1) * 100.0
p_bat['hp_sr'] = p_bat['hp_runs'] / p_bat['hp_balls'].clip(lower=1) * 100.0
p_bat['sr_elevation'] = p_bat['hp_sr'] - p_bat['total_sr']

# FAIR NEGATIVE DEDUCTIONS (BATTING):
p_bat['pen_rescue'] = np.where(p_bat['rescue_wpa'] < 0, 15.0 + np.abs(p_bat['rescue_wpa']) * 10.0, 0.0)
p_bat['pen_da'] = np.where(p_bat['da_wpa'] < 0, 15.0 + np.abs(p_bat['da_wpa']) * 10.0, 0.0)
p_bat['pen_ca'] = np.where(p_bat['ca_wpa'] < 0, 15.0 + np.abs(p_bat['ca_wpa']) * 10.0, 0.0)
p_bat['pen_elev'] = np.where(p_bat['sr_elevation'] < 0, 10.0 + np.abs(p_bat['sr_elevation']) * 0.50, 0.0)
p_bat['pen_hp_wpa'] = np.where(p_bat['hp_wpa'] < 0, 20.0 + np.abs(p_bat['hp_wpa']) * 10.0, 0.0)

p_bat['fair_deductions'] = (
    p_bat['pen_rescue'] + p_bat['pen_da'] + p_bat['pen_ca'] +
    p_bat['pen_elev'] + p_bat['pen_hp_wpa']
)

p_bat['S_ca'] = norm(p_bat['ca_wpa'].clip(lower=0))
p_bat['S_mwpp'] = norm(p_bat['authentic_mwpp'])
p_bat['S_da'] = norm(p_bat['da_wpa'].clip(lower=0))
p_bat['S_rescue'] = norm(p_bat['rescue_wpa'].clip(lower=0))
p_bat['S_comeback'] = norm(p_bat['comeback_knocks'])
p_bat['S_consistency'] = norm(p_bat['hp_consistency_rate'])
p_bat['S_elevation'] = norm(p_bat['sr_elevation'].clip(lower=0))

p_bat['reliability'] = np.sqrt(np.minimum(p_bat['matches'], 80) / 80.0)

p_bat['raw_positive'] = (
    p_bat['S_ca']          * 0.20 + # 20% Counter-Attack WPA
    p_bat['S_mwpp']        * 0.16 + # 16% Authentic MWPP Volume
    p_bat['S_consistency'] * 0.16 + # 16% Match-to-Match Pressure Consistency
    p_bat['S_da']          * 0.14 + # 14% Death-Alive Chase Finishing
    p_bat['S_rescue']      * 0.13 + # 13% Post-Collapse Rescue
    p_bat['S_elevation']   * 0.11 + # 11% SR Elevation under Pressure
    p_bat['S_comeback']    * 0.10   # 10% Comeback Knocks in Wins
)

p_bat['batting_clutch_score'] = ((p_bat['raw_positive'] - p_bat['fair_deductions']) * p_bat['reliability']).clip(0, 100)
p_bat['has_flaw'] = (p_bat['fair_deductions'] > 0).astype(int)
p_bat = p_bat.sort_values(['has_flaw', 'batting_clutch_score'], ascending=[True, False]).reset_index(drop=True)
p_bat['rank_bat'] = p_bat.index + 1

print("\n=== FINAL BALANCED TOP 10 BATTERS (Multi-Dimension + Consistency) ===")
print(p_bat.head(10)[['rank_bat', 'striker_name', 'matches', 'hp_consistency_rate', 'authentic_mwpp', 'comeback_knocks', 'ca_wpa', 'da_wpa', 'rescue_wpa', 'sr_elevation', 'fair_deductions', 'batting_clutch_score']].to_string())
