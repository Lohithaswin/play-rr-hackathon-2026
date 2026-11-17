import pandas as pd
import numpy as np

valid = pd.read_parquet('valid_v7_ml.parquet')
valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['bowling_team_won'] = 1 - valid['batting_team_won']
valid['stakes'] = valid['match_importance'].fillna(1.0).clip(lower=1.0)
valid['is_alive_hp'] = (valid['match_alive'] == True) & (
    (valid['is_high_pressure'] == 1) | (valid['over_num'] >= 17) | (valid['leverage_index'] >= 1.20)
)

valid['hp_runs_col'] = valid['runs'] * valid['is_alive_hp']
valid['hp_balls_col'] = valid['valid_flag'] * valid['is_alive_hp']
valid['hp_wpa_col'] = valid['wpa_bat_v5'] * valid['is_alive_hp'] * valid['stakes']

bat_m_cons = valid[valid['is_alive_hp'] == 1].groupby(['match_id', 'striker_id', 'striker_name'], as_index=False).agg({
    'hp_runs_col': 'sum',
    'hp_balls_col': 'sum',
    'hp_wpa_col': 'sum'
}).rename(columns={'hp_runs_col':'hp_runs', 'hp_balls_col':'hp_balls', 'hp_wpa_col':'hp_wpa'})

bat_m_cons['hp_sr'] = bat_m_cons['hp_runs'] / bat_m_cons['hp_balls'].clip(lower=1) * 100.0
bat_m_cons['is_positive_hp'] = (
    (bat_m_cons['hp_wpa'] > 0) |
    ((bat_m_cons['hp_runs'] >= 15) & (bat_m_cons['hp_sr'] >= 135.0))
).astype(int)

bat_cons = bat_m_cons.groupby(['striker_id', 'striker_name'], as_index=False).agg({
    'match_id': 'count',
    'is_positive_hp': 'sum'
}).rename(columns={'match_id': 'hp_matches_faced', 'is_positive_hp': 'hp_matches_positive'})
bat_cons['hp_consistency_rate'] = bat_cons['hp_matches_positive'] / bat_cons['hp_matches_faced'].clip(lower=1)

print('Sample Batting Consistency:')
bat_rank = pd.read_parquet('bat_rankings_v15.parquet')[['striker_id', 'striker_name', 'batting_clutch_score', 'rank_bat']]
bat_check = bat_rank.head(15).merge(bat_cons, on=['striker_id', 'striker_name'], how='left')
print(bat_check.to_string())
