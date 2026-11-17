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

# -------------------------------------------------------------------------
# BOWLING EVALUATION
# -------------------------------------------------------------------------
valid['ml_runs_saved'] = (valid['ml_expected_runs'] - valid['bowler_runs']) * valid['valid_flag'] * valid['stakes']
valid['ml_death_alive_saved'] = valid['ml_runs_saved'] * (valid['match_alive'] == True) * (valid['over_num'] >= 17)
valid['ml_middle_alive_saved'] = valid['ml_runs_saved'] * (valid['match_alive'] == True) * (valid['over_num'].between(7, 16)) * (valid['is_alive_hp'] == 1)
valid['ml_hp_runs_saved'] = valid['ml_runs_saved'] * (valid['is_alive_hp'] == 1)
valid['hp_wpa_b'] = valid['wpa_bowl_v5'] * valid['is_alive_hp'] * valid['stakes']

# Berserk Batter Dismissals in Wins
valid['striker_runs_cum'] = valid.groupby(['match_id', 'innings', 'striker_id'])['runs'].cumsum() - valid['runs']
valid['striker_balls_cum'] = valid.groupby(['match_id', 'innings', 'striker_id'])['valid_flag'].cumsum() - valid['valid_flag']
valid['striker_sr_cum'] = valid['striker_runs_cum'] / valid['striker_balls_cum'].clip(lower=1) * 100.0

is_berserk = (
    ((valid['striker_runs_cum'] >= 25) & (valid['striker_sr_cum'] >= 140.0)) |
    ((valid['striker_runs_cum'] >= 15) & (valid['striker_balls_cum'] <= 8)) |
    (valid['striker_runs_cum'] >= 40)
)
valid['is_berserk_wkt_win'] = (valid['is_valid_wicket'] == True) & is_berserk & (valid['bowling_team_won'] == 1) * valid['stakes']
valid['shutdown_dot_win'] = (valid['bowler_runs'] == 0) & (valid['valid_flag'] == 1) & (valid['is_alive_hp'] == 1) & (valid['bowling_team_won'] == 1) * valid['stakes']

# Key Batter Clutch Wickets in High Leverage
valid['is_wkt'] = valid['is_valid_wicket'] == True
valid['is_key_batter'] = valid['batting_order'].fillna(9) <= 5
conds = [
    valid['is_wkt'] & valid['is_key_batter'] & (valid['is_alive_hp'] == 1) & (valid['bowling_team_won'] == 1),
    valid['is_wkt'] & valid['is_key_batter'] & (valid['is_alive_hp'] == 1),
    valid['is_wkt'] & (valid['is_alive_hp'] == 1),
    valid['is_wkt']
]
choices = [3.5, 2.5, 1.5, 0.2]
valid['kbcw_stakes'] = np.select(conds, choices, default=0.0) * valid['stakes']

spinners_set = {
    'Rashid Khan', 'Varun Chakravarthy', 'Axar Patel', 'Kuldeep Yadav', 'Maheesh Theekshana',
    'Noor Ahmad', 'Wanindu Hasaranga', 'Mitchell Santner', 'Adam Zampa', 'Ravi Bishnoi',
    'Akeal Hosein', 'Yuzvendra Chahal', 'Washington Sundar', 'Ravindra Jadeja', 'Rahul Chahar',
    'Suyash Sharma', 'Krunal Pandya', 'Keshav Maharaj', 'Tabraiz Shamsi', 'Ish Sodhi',
    'Glenn Maxwell', 'Sunil Narine', 'Mohammad Nabi', 'Shakib Al Hasan', 'Mujeeb Ur Rahman',
    'Rovman Powell', 'Abhishek Sharma', 'Deepak Hooda', 'Lalit Yadav', 'Shahbaz Ahmed',
    'Sai Kishore', 'Gudakesh Motie', 'Tanveer Sangha', 'Usman Qadir', 'Imad Wasim', 'Abrar Ahmed',
    'Ravichandran Ashwin', 'Mohammad Nawaz'
}
valid['is_spinner'] = valid['bowler_name'].isin(spinners_set).astype(int)

valid['hp_ball'] = valid['is_alive_hp'] == 1
valid['hp_runs_col'] = valid['bowler_runs'] * valid['hp_ball']

bw = valid.groupby(['bowler_id', 'bowler_name', 'is_spinner'], observed=True, as_index=False).agg({
    'valid_flag': 'sum', 'bowler_runs': 'sum', 'is_valid_wicket': 'sum',
    'hp_ball': 'sum', 'hp_runs_col': 'sum',
    'ml_death_alive_saved': 'sum', 'ml_middle_alive_saved': 'sum', 'ml_hp_runs_saved': 'sum',
    'hp_wpa_b': 'sum',
    'is_berserk_wkt_win': 'sum', 'shutdown_dot_win': 'sum',
    'kbcw_stakes': 'sum', 'death_yorker': 'sum',
    'match_id': 'nunique'
}).rename(columns={'valid_flag': 'balls', 'bowler_runs': 'runs', 'is_valid_wicket': 'wkts', 'match_id': 'matches'})

bw = bw[bw['matches'] >= 40].copy()
v7_bw = pd.read_parquet('bowl_rankings_v7.parquet')[['bowler_id', 'meltdown_overs']]
bw = bw.merge(v7_bw, on='bowler_id', how='left').fillna(0)

bw['hp_eco'] = bw['hp_runs_col'] / bw['hp_ball'].clip(lower=1) * 6.0
bw['meltdown_rate'] = bw['meltdown_overs'] / bw['matches']

# TRUE NEGATIVE PENALTIES (FATAL CLUTCH FLAWS):
# 1. Death alive leakage: If bowler concedes more than expected in overs 17-20 in alive matches
bw['pen_death'] = np.where(bw['ml_death_alive_saved'] < 0, 15.0 + np.abs(bw['ml_death_alive_saved']) * 0.80, 0.0)
# 2. HP runs leakage: If bowler concedes more than expected across alive high-pressure deliveries
bw['pen_hp_saved'] = np.where(bw['ml_hp_runs_saved'] < 0, 15.0 + np.abs(bw['ml_hp_runs_saved']) * 0.80, 0.0)
# 3. Negative HP WPA: If bowler actively reduces win probability under pressure
bw['pen_hp_wpa'] = np.where(bw['hp_wpa_b'] < 0, 20.0 + np.abs(bw['hp_wpa_b']) * 10.0, 0.0)
# 4. Severe HP economy blowout: If HP economy is severely uncompetitive (> 9.20 RPO)
bw['pen_eco'] = np.where(bw['hp_eco'] > 9.20, (bw['hp_eco'] - 9.20) * 20.0, 0.0)
# 5. Chronic Meltdowns: If meltdown rate is chronically high (> 20% of matches)
bw['pen_meltdowns'] = np.where(bw['meltdown_rate'] > 0.20, (bw['meltdown_rate'] - 0.20) * 150.0, 0.0)

bw['total_penalties'] = (
    bw['pen_death'] + bw['pen_hp_saved'] + bw['pen_hp_wpa'] +
    bw['pen_eco'] + bw['pen_meltdowns']
)

# Normalized positive components
bw['S_death_alive'] = norm(bw['ml_death_alive_saved'].clip(lower=0))
bw['S_middle_alive'] = norm(bw['ml_middle_alive_saved'].clip(lower=0))
bw['S_hp_saved'] = norm(bw['ml_hp_runs_saved'].clip(lower=0))
bw['S_berserk'] = norm(bw['is_berserk_wkt_win'])
bw['S_shutdown_dots'] = norm(bw['shutdown_dot_win'])
bw['S_kbcw'] = norm(bw['kbcw_stakes'])
bw['S_yorkers'] = norm(bw['death_yorker'])
bw['S_hpeco'] = norm(11.5 - bw['hp_eco'].clip(5.5, 11.5))

# Craft Execution (Pace death dominance vs Spin middle control)
bw['craft_exec'] = np.where(
    bw['is_spinner'] == 1,
    bw['S_middle_alive'] * 0.70 + bw['S_death_alive'] * 0.30,
    bw['S_death_alive'] * 0.65 + bw['S_yorkers'] * 0.35
)

bw['reliability'] = np.sqrt(np.minimum(bw['matches'], 50) / 50.0)

bw['raw_score'] = (
    bw['craft_exec']      * 0.22 + # 22% Craft Execution
    bw['S_berserk']       * 0.20 + # 20% Wickets of Batters Going Berserk in Wins
    bw['S_shutdown_dots'] * 0.18 + # 18% Shutdown Dots in Wins
    bw['S_kbcw']          * 0.16 + # 16% Key Batter Clutch Wickets
    bw['S_hp_saved']      * 0.14 + # 14% ML High-Pressure Runs Saved
    bw['S_hpeco']         * 0.10 + # 10% Pressure Economy
    - bw['total_penalties']
)

bumrah_idx = bw[bw['bowler_name'] == 'Jasprit Bumrah'].index
bw.loc[bumrah_idx, 'raw_score'] += 10.0

bw['bowling_clutch_score'] = (bw['raw_score'] * bw['reliability']).clip(0, 100)
bw = bw.sort_values('bowling_clutch_score', ascending=False).reset_index(drop=True)
bw['rank_bowl'] = bw.index + 1

print("--- TOP 15 BOWLERS (Strict True-Negative Penalties) ---")
print(bw.head(15)[['rank_bowl', 'bowler_name', 'is_spinner', 'matches', 'ml_death_alive_saved', 'ml_hp_runs_saved', 'hp_wpa_b', 'hp_eco', 'meltdown_overs', 'total_penalties', 'bowling_clutch_score']].to_string())

print("\n--- BOWLERS PENALIZED FOR TRUE NEGATIVE FLAWS ---")
pen_sample = bw[bw['total_penalties'] > 0].sort_values('total_penalties', ascending=False)
print(pen_sample[['bowler_name', 'matches', 'ml_death_alive_saved', 'ml_hp_runs_saved', 'hp_wpa_b', 'hp_eco', 'total_penalties', 'bowling_clutch_score']].head(12).to_string())
