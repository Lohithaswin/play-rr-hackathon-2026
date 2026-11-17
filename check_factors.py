import pandas as pd
import numpy as np

valid = pd.read_parquet('valid_v6.parquet')
valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['bowling_team_won'] = 1 - valid['batting_team_won']
valid['is_alive_hp'] = (valid['match_alive'] == True) & (
    (valid['is_high_pressure'] == 1) | (valid['over_num'] >= 17) | (valid['leverage_index'] >= 1.20)
)
valid['stakes'] = valid['match_importance'].clip(lower=1.0)

# Batting metrics
valid['hp_runs_col'] = valid['runs'] * valid['is_alive_hp']
valid['hp_balls_col'] = valid['valid_flag'] * valid['is_alive_hp']
valid['hp_wpa_col'] = valid['wpa_bat_v5'] * valid['is_alive_hp'] * valid['stakes']
valid['da_wpa_col'] = valid['wpa_bat_v5'] * valid['bucket_chase_death_alive'] * valid['stakes']
valid['ca_wpa_col'] = valid['wpa_bat_v5'] * valid['is_counter_attack_ball'] * valid['stakes']
valid['rescue_wpa_col'] = valid['wpa_bat_v5'] * valid['rescue_ball'] * valid['stakes']

bat_agg = valid.groupby(['striker_id', 'striker_name'], as_index=False).agg({
    'match_id': 'nunique',
    'valid_flag': 'sum',
    'runs': 'sum',
    'hp_balls_col': 'sum',
    'hp_runs_col': 'sum',
    'hp_wpa_col': 'sum',
    'da_wpa_col': 'sum',
    'ca_wpa_col': 'sum',
    'rescue_wpa_col': 'sum'
}).rename(columns={
    'match_id': 'matches', 'valid_flag': 'balls', 'hp_balls_col': 'hp_balls',
    'hp_runs_col': 'hp_runs', 'hp_wpa_col': 'hp_wpa', 'da_wpa_col': 'da_wpa',
    'ca_wpa_col': 'ca_wpa', 'rescue_wpa_col': 'rescue_wpa'
})

bat_agg = bat_agg[bat_agg['matches'] >= 45].copy()
bat_agg['overall_sr'] = bat_agg['runs'] / bat_agg['balls'] * 100.0
bat_agg['hp_sr'] = bat_agg['hp_runs'] / bat_agg['hp_balls'].clip(lower=1) * 100.0
bat_agg['sr_elevation'] = bat_agg['hp_sr'] - bat_agg['overall_sr']

print('--- BATTERS SAMPLE WITH NEGATIVES ---')
for col in ['rescue_wpa', 'da_wpa', 'ca_wpa', 'sr_elevation', 'hp_wpa']:
    neg_count = (bat_agg[col] < 0).sum()
    print(f'{col} < 0 count: {neg_count} / {len(bat_agg)}')

print('\nCheck prominent batters:')
for name in ['David Miller', 'Suryakumar Yadav', 'Tilak Varma', 'Phil Salt', 'Shimron Hetmyer', 'Glenn Phillips', 'Nicholas Pooran', 'Hardik Pandya', 'Virat Kohli', 'Shubman Gill', 'Heinrich Klaasen', 'Rovman Powell', 'Dinesh Karthik', 'Sanju Samson', 'Jos Buttler', 'KL Rahul']:
    r = bat_agg[bat_agg['striker_name'] == name]
    if len(r):
        row = r.iloc[0]
        print(f"{name:18}: matches={row['matches']}, ca={row['ca_wpa']:.2f}, da={row['da_wpa']:.2f}, rescue={row['rescue_wpa']:.2f}, sr_elev={row['sr_elevation']:.1f}, hp_wpa={row['hp_wpa']:.2f}")
