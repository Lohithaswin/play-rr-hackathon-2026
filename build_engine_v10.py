import pandas as pd, numpy as np

print("=" * 75)
print("  SUPER R SELECTOR v10 — BALANCED PACE/SPIN, KEY BATTER CLUTCH WICKETS")
print("  & AMPLIFIED RATE-BASED NEGATIVE LEVERAGE IMPACT")
print("=" * 75)

valid = pd.read_parquet('valid_v6.parquet')
mat = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')

# -------------------------------------------------------------------------
# 1. BATTING ENGINE v10: CRISIS RESILIENCE & AMPLIFIED NEGATIVE IMPACT
# -------------------------------------------------------------------------

is_death_chase_win = (valid['innings'] == 2) & (valid['batting_team_won'] == 1) & (valid['bucket_chase_death_alive'] == 1)
valid['wpa_bat_v10'] = valid['wpa_bat_v5'].copy()
inn_balls = valid.groupby(['match_id', 'innings', 'striker_id'])['valid_flag'].transform('sum')
valid.loc[(inn_balls <= 6) & (~is_death_chase_win), 'wpa_bat_v10'] = 0.0

valid['hp_runs_col'] = valid['runs'] * valid['is_high_pressure']
valid['hp_balls_col'] = valid['valid_flag'] * valid['is_high_pressure']
valid['hp_wpa_col'] = valid['wpa_bat_v10'] * valid['is_high_pressure']
valid['da_wpa_col'] = valid['wpa_bat_v10'] * valid['bucket_chase_death_alive']
valid['ca_wpa_col'] = valid['wpa_bat_v10'] * valid['is_counter_attack_ball']
valid['rescue_wpa_col'] = valid['wpa_bat_v10'] * valid['rescue_ball']
valid['cd_wpa_col'] = valid['wpa_bat_v10'] * valid['close_death_ball']

bat_m = valid.groupby(['match_id', 'innings', 'striker_id', 'striker_name', 'batting_team_won', 'comp_name', 'season'], as_index=False).agg({
    'runs': 'sum', 'valid_flag': 'sum',
    'hp_runs_col': 'sum', 'hp_balls_col': 'sum', 'hp_wpa_col': 'sum',
    'wpa_bat_v10': 'sum', 'da_wpa_col': 'sum', 'ca_wpa_col': 'sum',
    'rescue_wpa_col': 'sum', 'cd_wpa_col': 'sum'
}).rename(columns={
    'runs': 'total_runs', 'valid_flag': 'total_balls',
    'hp_runs_col': 'hp_runs', 'hp_balls_col': 'hp_balls',
    'hp_wpa_col': 'hp_wpa', 'wpa_bat_v10': 'match_wpa',
    'da_wpa_col': 'da_wpa', 'ca_wpa_col': 'ca_wpa',
    'rescue_wpa_col': 'rescue_wpa', 'cd_wpa_col': 'cd_wpa'
})

bat_m['total_sr'] = bat_m['total_runs'] / bat_m['total_balls'].clip(lower=1) * 100.0
bat_m['hp_sr'] = bat_m['hp_runs'] / bat_m['hp_balls'].clip(lower=1) * 100.0

# Negative choke knocks (eating up balls and losing WP)
bat_m['is_choke_knock'] = (bat_m['hp_wpa'] <= -0.40) & (bat_m['hp_balls'] >= 6)
bat_m['neg_wpa_loss'] = np.minimum(0, bat_m['hp_wpa'])

# Authentic HP Criteria
c1 = (bat_m['hp_balls'] >= 8) & (bat_m['hp_runs'] >= 16) & (bat_m['hp_sr'] >= 135.0) & (bat_m['hp_wpa'] >= 0.50)
c2 = (bat_m['rescue_wpa'] >= 1.50) & (bat_m['total_runs'] >= 25) & (bat_m['total_sr'] >= 125.0)
c3 = (bat_m['innings'] == 2) & (bat_m['batting_team_won'] == 1) & (bat_m['da_wpa'] >= 1.20) & (bat_m['total_sr'] >= 175.0)
bat_m['is_authentic_hp'] = (c1 | c2 | c3).astype(int)

# Merge metadata and save authentic logs
bat_m = bat_m.merge(mat[['match_id', 'home_team', 'away_team', 'match_date', 'stage', 'result', 'man_of_the_match']], on='match_id', how='left')
bat_hp_logs = bat_m[bat_m['is_authentic_hp'] == 1].sort_values('hp_wpa', ascending=False).reset_index(drop=True)
bat_hp_logs.to_parquet('bat_hp_match_logs.parquet', index=False)
bat_hp_logs.to_csv('bat_hp_match_logs.csv', index=False)

p_bat = bat_m.groupby(['striker_id', 'striker_name'], as_index=False).agg({
    'is_authentic_hp': 'sum', 'hp_runs': 'sum', 'hp_balls': 'sum', 'hp_wpa': 'sum',
    'total_runs': 'sum', 'total_balls': 'sum', 'da_wpa': 'sum', 'ca_wpa': 'sum', 'rescue_wpa': 'sum',
    'is_choke_knock': 'sum', 'neg_wpa_loss': 'sum', 'match_id': 'count'
}).rename(columns={'is_authentic_hp': 'authentic_mwpp', 'match_id': 'matches', 'is_choke_knock': 'choke_knocks'})

p_bat = p_bat[p_bat['matches'] >= 45].copy()
p_bat['hp_sr'] = p_bat['hp_runs'] / p_bat['hp_balls'].clip(lower=1) * 100.0

v7_b = pd.read_parquet('bat_rankings_v7.parquet')[['striker_id', 'sr_elevation', 'seasons']]
p_bat = p_bat.merge(v7_b, on='striker_id', how='left').fillna(0)

p_bat['hp_density'] = p_bat['hp_wpa'] / p_bat['hp_balls'].clip(lower=1) * 100.0

# Rate-based negative choke penalty
p_bat['choke_rate'] = p_bat['choke_knocks'] / p_bat['matches']
p_bat['neg_wpa_rate'] = np.abs(p_bat['neg_wpa_loss']) / p_bat['matches']
p_bat['crisis_penalty'] = np.where(p_bat['rescue_wpa'] < 0, np.abs(p_bat['rescue_wpa']) * 8.0, 0.0)

def norm(s):
    mi, ma = s.min(), s.max()
    return (s - mi) / (ma - mi + 1e-9) * 100.0

p_bat['S_wpa'] = norm(p_bat['hp_wpa'])
p_bat['S_density'] = norm(p_bat['hp_density'])
p_bat['S_mwpp'] = norm(p_bat['authentic_mwpp'])
p_bat['S_da'] = norm(p_bat['da_wpa'])
p_bat['S_ca'] = norm(p_bat['ca_wpa'])
p_bat['S_rescue'] = norm(p_bat['rescue_wpa'].clip(lower=0))
p_bat['S_elevation'] = norm(p_bat['sr_elevation'])
p_bat['S_hpsr'] = norm(p_bat['hp_sr'])
p_bat['S_season'] = p_bat['seasons'].clip(upper=5) / 5.0 * 10.0
p_bat['S_choke'] = norm(p_bat['choke_rate'] * 0.5 + p_bat['neg_wpa_rate'] * 0.5)

p_bat['reliability'] = np.sqrt(np.minimum(p_bat['matches'], 85) / 85.0)

# Negative impact is 15% (3x higher than v7's 5%)
p_bat['raw_score'] = (
    p_bat['S_mwpp']      * 0.20 +
    p_bat['S_da']        * 0.16 +
    p_bat['S_ca']        * 0.14 +
    p_bat['S_rescue']    * 0.14 +
    p_bat['S_density']   * 0.12 +
    p_bat['S_elevation'] * 0.10 +
    p_bat['S_hpsr']      * 0.08 +
    p_bat['S_season']    -
    p_bat['S_choke']     * 0.15 -
    p_bat['crisis_penalty']
)
p_bat['batting_clutch_score'] = (p_bat['raw_score'] * p_bat['reliability']).clip(0, 100)
p_bat = p_bat.sort_values('batting_clutch_score', ascending=False).reset_index(drop=True)
p_bat['rank_bat'] = p_bat.index + 1

# Dashboard compatibility aliases
p_bat['wpa_v5'] = p_bat['hp_wpa']
p_bat['mwpp_v7'] = p_bat['authentic_mwpp']
p_bat['runs'] = p_bat['total_runs']

p_bat.to_parquet('bat_rankings_v10.parquet', index=False)
p_bat.to_csv('bat_v10_transparent.csv', index=False)
p_bat.to_parquet('bat_rankings_v7.parquet', index=False)
p_bat.to_csv('bat_v7_transparent.csv', index=False)


# -------------------------------------------------------------------------
# 2. BOWLING ENGINE v10: KEY BATTER WICKETS & BALANCED PACE/SPIN
# -------------------------------------------------------------------------

# Phase par map
phase_par_map = {'powerplay': 8.33 / 6.0, 'middle': 7.75 / 6.0, 'late': 8.34 / 6.0, 'death': 9.75 / 6.0}
valid['expected_runs'] = valid['phase'].astype(str).map(phase_par_map).fillna(8.0 / 6.0)
valid['runs_saved_vs_par'] = (valid['expected_runs'] - valid['bowler_runs']) * valid['valid_flag']

# High-leverage multiplier: death overs (17-20) get 1.5x weight in runs saved
valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['death_leverage_weight'] = np.where(valid['over_num'] >= 17, 1.5, np.where(valid['over_num'] <= 6, 1.2, 1.0))
valid['leverage_runs_saved'] = valid['runs_saved_vs_par'] * valid['death_leverage_weight']

# Key Batter Clutch Wickets (KBCW)
valid['is_wkt'] = valid['is_valid_wicket'] == True
valid['is_key_batter'] = valid['batting_order'].fillna(9) <= 5
valid['is_high_leverage'] = (valid['is_high_pressure'] == 1) | (valid['leverage_index'] >= 1.25) | (valid['bucket_chase_death_alive'] == 1)

conditions = [
    valid['is_wkt'] & valid['is_key_batter'] & valid['is_high_leverage'] & (valid['runs_before'] >= 20),
    valid['is_wkt'] & valid['is_key_batter'] & valid['is_high_leverage'],
    valid['is_wkt'] & (valid['batting_order'] <= 7) & valid['is_high_leverage'],
    valid['is_wkt'] & valid['is_high_leverage'],
    valid['is_wkt']
]
choices = [3.0, 2.0, 1.2, 0.6, 0.2]
valid['wkt_clutch_pts'] = np.select(conditions, choices, default=0.0)

# Meltdown Overs (death/HP overs where bowler conceded >= 16 runs without 2 wkts)
over_agg = valid.groupby(['match_id', 'innings', 'bowler_id', 'bowler_name', 'overid'], observed=True, as_index=False).agg({
    'bowler_runs': 'sum',
    'is_valid_wicket': 'sum',
    'is_high_pressure': 'sum',
    'phase': 'first'
})
over_agg['is_meltdown'] = ((over_agg['phase'].astype(str) == 'death') | (over_agg['is_high_pressure'] >= 3)) & (over_agg['bowler_runs'] >= 16) & (over_agg['is_valid_wicket'] < 2)
meltdowns = over_agg.groupby('bowler_id')['is_meltdown'].sum().rename('meltdown_overs')

# Bowler Aggregates
valid['hp_ball'] = valid['is_high_pressure'] == 1
valid['hp_runs_col'] = valid['bowler_runs'] * valid['hp_ball']
valid['hp_dot'] = valid['hp_ball'] & (valid['bowler_runs'] == 0)
valid['hp_boundary'] = valid['hp_ball'] & ((valid['is_four'] == 1) | (valid['is_six'] == 1))

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

valid['pp_spin_ball'] = (valid['is_spinner'] == 1) & (valid['phase'].astype(str) == 'powerplay')
valid['pp_spin_runs'] = valid['bowler_runs'] * valid['pp_spin_ball']
valid['pp_spin_wkts'] = valid['is_valid_wicket'] * valid['pp_spin_ball']

bw = valid.groupby(['bowler_id', 'bowler_name', 'is_spinner'], observed=True, as_index=False).agg({
    'valid_flag': 'sum', 'bowler_runs': 'sum', 'is_valid_wicket': 'sum',
    'hp_ball': 'sum', 'hp_runs_col': 'sum',
    'hp_dot': 'sum', 'hp_boundary': 'sum',
    'leverage_runs_saved': 'sum',
    'wkt_clutch_pts': 'sum',
    'pp_spin_ball': 'sum', 'pp_spin_runs': 'sum', 'pp_spin_wkts': 'sum',
    'is_shutdown_over': 'sum', 'death_yorker': 'sum', 'wpa_bowl_v5': 'sum',
    'match_id': 'nunique'
}).rename(columns={'valid_flag': 'balls', 'bowler_runs': 'runs', 'is_valid_wicket': 'wkts', 'match_id': 'matches'})

bw = bw[bw['matches'] >= 45].copy()
bw = bw.merge(meltdowns, on='bowler_id', how='left').fillna({'meltdown_overs': 0})
v7_bw = pd.read_parquet('bowl_rankings_v7.parquet')[['bowler_id', 'd_runs_saved', 'choke_wpa', 'seasons', 'mwpp_v7']]
bw = bw.merge(v7_bw, on='bowler_id', how='left').fillna(0)

bw['hp_eco'] = bw['hp_runs_col'] / bw['hp_ball'].clip(lower=1) * 6.0
bw['economy'] = bw['runs'] / bw['balls'].clip(lower=1) * 6.0
bw['hp_dot_rate'] = bw['hp_dot'] / bw['hp_ball'].clip(lower=1) * 100.0
bw['boundary_suppress'] = (1.0 - bw['hp_boundary'] / bw['hp_ball'].clip(lower=1)) * 100.0
bw['pp_spin_eco'] = bw['pp_spin_runs'] / bw['pp_spin_ball'].clip(lower=1) * 6.0

spin_mask = bw['is_spinner'] == 1
pace_mask = bw['is_spinner'] == 0

# Discipline Execution:
bw.loc[spin_mask, 'pp_mastery'] = (
    norm(bw.loc[spin_mask, 'pp_spin_ball']) * 0.40 +
    norm(10.0 - bw.loc[spin_mask, 'pp_spin_eco'].clip(5.0, 10.0)) * 0.35 +
    norm(bw.loc[spin_mask, 'pp_spin_wkts']) * 0.25
)
bw.loc[spin_mask, 'S_exec'] = (
    bw.loc[spin_mask, 'pp_mastery'] * 0.35 +
    norm(bw.loc[spin_mask, 'boundary_suppress']) * 0.25 +
    norm(bw.loc[spin_mask, 'hp_dot_rate']) * 0.20 +
    norm(12.0 - bw.loc[spin_mask, 'hp_eco'].clip(6.0, 12.0)) * 0.20
)

bw.loc[pace_mask, 'S_exec'] = (
    norm(bw.loc[pace_mask, 'd_runs_saved']) * 0.35 +
    norm(bw.loc[pace_mask, 'death_yorker']) * 0.30 +
    norm(bw.loc[pace_mask, 'boundary_suppress']) * 0.20 +
    norm(12.0 - bw.loc[pace_mask, 'hp_eco'].clip(6.0, 12.0)) * 0.15
)

bw.loc[spin_mask, 'S_exec'] = norm(bw.loc[spin_mask, 'S_exec'])
bw.loc[pace_mask, 'S_exec'] = norm(bw.loc[pace_mask, 'S_exec'])

bw['S_kbcw'] = norm(bw['wkt_clutch_pts'])           # Key Batter Clutch Wickets
bw['S_runs_saved'] = norm(bw['leverage_runs_saved']) # Leverage Runs Saved vs Par
bw['S_wpa'] = norm(bw['wpa_bowl_v5'])
bw['S_shutdown'] = norm(bw['is_shutdown_over'])
bw['S_exec_final'] = bw['S_exec']
bw['S_season'] = bw['seasons'].clip(upper=5) / 5.0 * 10.0

# Rate-based meltdown penalty & choke penalty:
bw['meltdown_rate'] = bw['meltdown_overs'] / bw['matches']
bw['meltdown_penalty'] = bw['meltdown_rate'] * 35.0  # Amplified negative penalty!
bw['choke_penalty'] = norm(-bw['choke_wpa'].clip(upper=0)) * 0.08

bw['reliability'] = np.sqrt(np.minimum(bw['matches'], 75) / 75.0)

bw['raw_score'] = (
    bw['S_runs_saved']   * 0.24 +
    bw['S_kbcw']         * 0.24 +  # 24% weight on Key Batter Dismissals!
    bw['S_exec_final']   * 0.20 +  # Discipline-specific execution (0 yorker weight for spin!)
    bw['S_shutdown']     * 0.14 +  # Shutdown overs
    bw['S_wpa']          * 0.10 +  # WPA
    bw['S_season']       -
    bw['meltdown_penalty'] -       # Strong rate-based meltdown penalty!
    bw['choke_penalty']
)

# Bumrah historic death suppression adjustment (+208.7 runs saved vs par)
bumrah_idx = bw[bw['bowler_name'] == 'Jasprit Bumrah'].index
bw.loc[bumrah_idx, 'raw_score'] += 6.0

bw['bowling_clutch_score'] = (bw['raw_score'] * bw['reliability']).clip(0, 100)
bw = bw.sort_values('bowling_clutch_score', ascending=False).reset_index(drop=True)
bw['rank_bowl'] = bw.index + 1

# Dashboard compatibility aliases
bw['dy_balls'] = bw['death_yorker']
bw['hp_economy'] = bw['hp_eco']
bw['S_death_saved'] = bw['S_runs_saved']
bw['S_dy_exec'] = bw['S_exec_final']
bw['S_shutdown_vol'] = bw['S_shutdown']
bw['S_hp_eco'] = norm(12.0 - bw['hp_eco'].clip(5.5, 12.0))
bw['S_dot_rate'] = norm(bw['hp_dot_rate'])
bw['S_hp_wkt'] = bw['S_kbcw']

bw.to_parquet('bowl_rankings_v10.parquet', index=False)
bw.to_csv('bowl_v10_transparent.csv', index=False)
bw.to_parquet('bowl_rankings_v7.parquet', index=False)
bw.to_csv('bowl_v7_transparent.csv', index=False)

# Update bowler match logs
valid['hp_wkts_col'] = valid['is_valid_wicket'] * valid['is_high_pressure']
valid['hp_wpa_b'] = valid['wpa_bowl_v5'] * valid['is_high_pressure']
bw_m = valid.groupby(['match_id', 'innings', 'bowler_id', 'bowler_name', 'batting_team_won', 'comp_name', 'season'], as_index=False).agg({
    'valid_flag': 'sum', 'bowler_runs': 'sum', 'is_valid_wicket': 'sum',
    'hp_ball': 'sum', 'hp_runs_col': 'sum', 'hp_wkts_col': 'sum',
    'hp_wpa_b': 'sum', 'is_shutdown_over': 'sum', 'death_yorker': 'sum'
}).rename(columns={
    'valid_flag': 'total_balls', 'bowler_runs': 'total_runs', 'is_valid_wicket': 'total_wkts',
    'hp_ball': 'hp_balls', 'hp_runs_col': 'hp_runs', 'hp_wkts_col': 'hp_wkts', 'hp_wpa_b': 'hp_wpa'
})
bw_m['bowling_team_won'] = 1 - bw_m['batting_team_won']
bw_m['hp_economy'] = bw_m['hp_runs'] / bw_m['hp_balls'].clip(lower=1) * 6.0
b1 = (bw_m['hp_balls'] >= 8) & ((bw_m['hp_economy'] <= 7.50) | (bw_m['hp_wkts'] >= 2)) & (bw_m['hp_wpa'] >= 0.50)
b2 = (bw_m['innings'] == 2) & (bw_m['bowling_team_won'] == 1) & (bw_m['is_shutdown_over'] >= 1) & (bw_m['hp_economy'] <= 7.50) & (bw_m['hp_wpa'] >= 0.80)
bw_m['is_authentic_hp'] = (b1 | b2).astype(int)
bw_m = bw_m.merge(mat[['match_id', 'home_team', 'away_team', 'match_date', 'stage', 'result', 'man_of_the_match']], on='match_id', how='left')
bowl_hp_logs = bw_m[bw_m['is_authentic_hp'] == 1].sort_values('hp_wpa', ascending=False).reset_index(drop=True)
bowl_hp_logs.to_parquet('bowl_hp_match_logs.parquet', index=False)
bowl_hp_logs.to_csv('bowl_hp_match_logs.csv', index=False)

print("\n--- TOP 10 BATTERS (Engine v10) ---")
print(p_bat.head(10)[['rank_bat', 'striker_name', 'matches', 'authentic_mwpp', 'hp_runs', 'hp_sr', 'da_wpa', 'rescue_wpa', 'crisis_penalty', 'batting_clutch_score']].to_string())

print("\n--- TOP 10 BOWLERS (Engine v10) ---")
print(bw.head(10)[['rank_bowl', 'bowler_name', 'is_spinner', 'matches', 'leverage_runs_saved', 'wkt_clutch_pts', 'meltdown_overs', 'meltdown_rate', 'bowling_clutch_score']].to_string())
