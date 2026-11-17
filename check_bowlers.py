import pandas as pd
import numpy as np

valid = pd.read_parquet('valid_v6.parquet')
valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['bowling_team_won'] = 1 - valid['batting_team_won']
valid['is_alive_hp'] = (valid['match_alive'] == True) & (
    (valid['is_high_pressure'] == 1) | (valid['over_num'] >= 17) | (valid['leverage_index'] >= 1.20)
)
valid['stakes'] = valid['match_importance'].clip(lower=1.0)

phase_pars = {'powerplay': 8.33/6.0, 'middle': 7.75/6.0, 'late': 8.34/6.0, 'death': 9.75/6.0}
valid['expected_runs'] = valid['phase'].astype(str).map(phase_pars).fillna(8.0/6.0)

# Death Alive (Overs 17-20 in alive matches)
valid['is_death_alive'] = (valid['match_alive'] == True) & (valid['over_num'] >= 17)
valid['death_alive_saved'] = (9.75/6.0 - valid['bowler_runs']) * valid['valid_flag'] * valid['is_death_alive'] * valid['stakes']

# Middle Alive Pressure (Overs 7-16 in alive matches)
valid['is_middle_alive'] = (valid['match_alive'] == True) & (valid['over_num'].between(7, 16)) & (valid['is_alive_hp'] == 1)
valid['middle_alive_saved'] = (7.75/6.0 - valid['bowler_runs']) * valid['valid_flag'] * valid['is_middle_alive'] * valid['stakes']

# HP runs saved
valid['hp_runs_saved'] = (valid['expected_runs'] - valid['bowler_runs']) * valid['valid_flag'] * valid['is_alive_hp'] * valid['stakes']

# HP Bowling WPA
valid['hp_wpa_b'] = valid['wpa_bowl_v5'] * valid['is_alive_hp'] * valid['stakes']

valid['hp_ball'] = valid['is_alive_hp'] == 1
valid['hp_runs_col'] = valid['bowler_runs'] * valid['hp_ball']

bw = valid.groupby(['bowler_id', 'bowler_name'], as_index=False).agg({
    'match_id': 'nunique',
    'valid_flag': 'sum',
    'bowler_runs': 'sum',
    'is_valid_wicket': 'sum',
    'hp_ball': 'sum',
    'hp_runs_col': 'sum',
    'death_alive_saved': 'sum',
    'middle_alive_saved': 'sum',
    'hp_runs_saved': 'sum',
    'hp_wpa_b': 'sum',
    'death_yorker': 'sum'
}).rename(columns={'match_id': 'matches', 'valid_flag': 'balls', 'bowler_runs': 'runs', 'is_valid_wicket': 'wkts'})

bw = bw[bw['matches'] >= 45].copy()
v7_bw = pd.read_parquet('bowl_rankings_v7.parquet')[['bowler_id', 'meltdown_overs']]
bw = bw.merge(v7_bw, on='bowler_id', how='left').fillna(0)
bw['hp_eco'] = bw['hp_runs_col'] / bw['hp_ball'].clip(lower=1) * 6.0

print('--- BOWLERS FACTOR NEGATIVE COUNTS ---')
for col in ['death_alive_saved', 'hp_runs_saved', 'hp_wpa_b']:
    neg_count = (bw[col] < 0).sum()
    print(f'{col} < 0 count: {neg_count} / {len(bw)}')

high_eco = (bw['hp_eco'] > 8.5).sum()
print(f'hp_eco > 8.5 count: {high_eco} / {len(bw)}')

high_meltdowns = (bw['meltdown_overs'] > 10).sum()
print(f'meltdowns > 10 count: {high_meltdowns} / {len(bw)}')

print('\nCheck prominent bowlers:')
check_names = [
    'Jasprit Bumrah', 'Bhuvneshwar Kumar', 'Mustafizur Rahman', 'Maheesh Theekshana',
    'Haris Rauf', 'Axar Patel', 'Josh Hazlewood', 'Wanindu Hasaranga', 'Nathan Ellis',
    'Jason Holder', 'Rashid Khan', 'Arshdeep Singh', 'Ravi Bishnoi', 'Mohammed Siraj',
    'Avesh Khan', 'Trent Boult', 'Kagiso Rabada', 'Sam Curran', 'Anrich Nortje'
]
for name in check_names:
    r = bw[bw['bowler_name'] == name]
    if len(r):
        row = r.iloc[0]
        print(f"{name:20}: matches={row['matches']}, death_saved={row['death_alive_saved']:6.1f}, hp_saved={row['hp_runs_saved']:6.1f}, hp_wpa={row['hp_wpa_b']:6.2f}, hp_eco={row['hp_eco']:4.2f}, meltdowns={row['meltdown_overs']:2.0f}, yorkers={row['death_yorker']:2.0f}")
