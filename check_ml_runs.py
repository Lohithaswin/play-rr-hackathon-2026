import pandas as pd
import numpy as np

valid = pd.read_parquet('valid_v7_ml.parquet')
valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['bowling_team_won'] = 1 - valid['batting_team_won']
valid['is_alive_hp'] = (valid['match_alive'] == True) & (
    (valid['is_high_pressure'] == 1) | (valid['over_num'] >= 17) | (valid['leverage_index'] >= 1.20)
)
valid['stakes'] = valid['match_importance'].clip(lower=1.0)

# ML-based runs saved
valid['ml_runs_saved'] = (valid['ml_expected_runs'] - valid['bowler_runs']) * valid['valid_flag'] * valid['stakes']
valid['ml_death_alive_saved'] = valid['ml_runs_saved'] * (valid['match_alive'] == True) * (valid['over_num'] >= 17)
valid['ml_hp_runs_saved'] = valid['ml_runs_saved'] * (valid['is_alive_hp'] == 1)

# Check top bowlers by ML death runs saved and ML hp runs saved
bw_ml = valid.groupby(['bowler_id', 'bowler_name'], as_index=False).agg({
    'match_id': 'nunique',
    'valid_flag': 'sum',
    'ml_death_alive_saved': 'sum',
    'ml_hp_runs_saved': 'sum'
}).rename(columns={'match_id': 'matches', 'valid_flag': 'balls'})

bw_ml = bw_ml[bw_ml['matches'] >= 45].sort_values('ml_hp_runs_saved', ascending=False)
print("Top 15 Bowlers by ML High-Pressure Runs Saved:")
print(bw_ml.head(15).to_string())

print("\nSpecific prominent bowlers ML stats:")
check_names = ['Jasprit Bumrah', 'Mustafizur Rahman', 'Haris Rauf', 'Nathan Ellis', 'Maheesh Theekshana', 'Bhuvneshwar Kumar', 'Josh Hazlewood', 'Arshdeep Singh', 'Rashid Khan', 'Axar Patel', 'Wanindu Hasaranga']
for name in check_names:
    r = bw_ml[bw_ml['bowler_name'] == name]
    if len(r):
        row = r.iloc[0]
        print(f"{name:20}: matches={row['matches']}, ML_death_saved={row['ml_death_alive_saved']:6.1f}, ML_hp_saved={row['ml_hp_runs_saved']:6.1f}")
