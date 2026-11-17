import pandas as pd, numpy as np

print("=" * 70)
print("  SUPER R SELECTOR v9 — INDUSTRY STANDARD PRESSURE ENGINE")
print("  (Role-Adjusted, Spin-Powerplay Specialized, Crisis-Penalized)")
print("=" * 70)

valid = pd.read_parquet('valid_v6.parquet')
mat = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')

# ---------------------------------------------------------
# 1. BATTING ENGINE v9: ROLE-ADJUSTED CRISIS & IMPACT MODEL
# ---------------------------------------------------------

# Ball-level cameo nullification: balls <= 6 in an inning gets 0 WPA unless it is a winning death chase
is_death_chase_win = (valid['innings'] == 2) & (valid['batting_team_won'] == 1) & (valid['bucket_chase_death_alive'] == 1)
valid['wpa_bat_v9'] = valid['wpa_bat_v5'].copy()
inn_balls = valid.groupby(['match_id', 'innings', 'striker_id'])['valid_flag'].transform('sum')
valid.loc[(inn_balls <= 6) & (~is_death_chase_win), 'wpa_bat_v9'] = 0.0

# Vectorized HP metrics
valid['hp_runs_col'] = valid['runs'] * valid['is_high_pressure']
valid['hp_balls_col'] = valid['valid_flag'] * valid['is_high_pressure']
valid['hp_wpa_col'] = valid['wpa_bat_v9'] * valid['is_high_pressure']
valid['da_wpa_col'] = valid['wpa_bat_v9'] * valid['bucket_chase_death_alive']
valid['ca_wpa_col'] = valid['wpa_bat_v9'] * valid['is_counter_attack_ball']
valid['rescue_wpa_col'] = valid['wpa_bat_v9'] * valid['rescue_ball']
valid['cd_wpa_col'] = valid['wpa_bat_v9'] * valid['close_death_ball']

# Match level aggregation
bat_m = valid.groupby(['match_id', 'innings', 'striker_id', 'striker_name', 'batting_team_won', 'comp_name', 'season'], as_index=False).agg({
    'runs': 'sum', 'valid_flag': 'sum',
    'hp_runs_col': 'sum', 'hp_balls_col': 'sum', 'hp_wpa_col': 'sum',
    'wpa_bat_v9': 'sum', 'da_wpa_col': 'sum', 'ca_wpa_col': 'sum',
    'rescue_wpa_col': 'sum', 'cd_wpa_col': 'sum'
}).rename(columns={
    'runs': 'total_runs', 'valid_flag': 'total_balls',
    'hp_runs_col': 'hp_runs', 'hp_balls_col': 'hp_balls',
    'hp_wpa_col': 'hp_wpa', 'wpa_bat_v9': 'match_wpa',
    'da_wpa_col': 'da_wpa', 'ca_wpa_col': 'ca_wpa',
    'rescue_wpa_col': 'rescue_wpa', 'cd_wpa_col': 'cd_wpa'
})

bat_m['total_sr'] = bat_m['total_runs'] / bat_m['total_balls'].clip(lower=1) * 100.0
bat_m['hp_sr'] = bat_m['hp_runs'] / bat_m['hp_balls'].clip(lower=1) * 100.0

# Strict Authentic HP criteria (no 4(4) or 9(3))
c1 = (bat_m['hp_balls'] >= 8) & (bat_m['hp_runs'] >= 16) & (bat_m['hp_sr'] >= 135.0) & (bat_m['hp_wpa'] >= 0.50)
c2 = (bat_m['rescue_wpa'] >= 1.50) & (bat_m['total_runs'] >= 25) & (bat_m['total_sr'] >= 125.0)
c3 = (bat_m['innings'] == 2) & (bat_m['batting_team_won'] == 1) & (bat_m['da_wpa'] >= 1.20) & (bat_m['total_sr'] >= 175.0)
bat_m['is_authentic_hp'] = (c1 | c2 | c3).astype(int)

# Merge match metadata
bat_m = bat_m.merge(mat[['match_id', 'home_team', 'away_team', 'match_date', 'stage', 'result', 'man_of_the_match']], on='match_id', how='left')
bat_hp_logs = bat_m[bat_m['is_authentic_hp'] == 1].sort_values('hp_wpa', ascending=False).reset_index(drop=True)
bat_hp_logs.to_parquet('bat_hp_match_logs.parquet', index=False)
bat_hp_logs.to_csv('bat_hp_match_logs.csv', index=False)

# Aggregate Batters
p_bat = bat_m.groupby(['striker_id', 'striker_name'], as_index=False).agg({
    'is_authentic_hp': 'sum',
    'hp_runs': 'sum',
    'hp_balls': 'sum',
    'hp_wpa': 'sum',
    'total_runs': 'sum',
    'total_balls': 'sum',
    'da_wpa': 'sum',
    'ca_wpa': 'sum',
    'rescue_wpa': 'sum',
    'cd_wpa': 'sum',
    'match_id': 'count'
}).rename(columns={'is_authentic_hp': 'authentic_mwpp', 'match_id': 'matches'})

p_bat = p_bat[p_bat['matches'] >= 45].copy()
p_bat['hp_sr'] = p_bat['hp_runs'] / p_bat['hp_balls'].clip(lower=1) * 100.0

# Bring v7 metrics
v7_b = pd.read_parquet('bat_rankings_v7.parquet')[['striker_id', 'sr_elevation', 'ko_wpa', 'choke_wpa', 'seasons']]
p_bat = p_bat.merge(v7_b, on='striker_id', how='left').fillna(0)

# Impact Density
p_bat['hp_density'] = p_bat['hp_wpa'] / p_bat['hp_balls'].clip(lower=1) * 100.0

# CRISIS VULNERABILITY PENALTY:
# If rescue_wpa < 0, penalize strictly
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
p_bat['S_choke'] = norm(-p_bat['choke_wpa'].clip(upper=0))
p_bat['S_season'] = p_bat['seasons'].clip(upper=5) / 5.0 * 10.0
p_bat['reliability'] = np.sqrt(np.minimum(p_bat['matches'], 85) / 85.0)

p_bat['raw_score'] = (
    p_bat['S_mwpp']      * 0.20 +
    p_bat['S_da']        * 0.16 +
    p_bat['S_ca']        * 0.14 +
    p_bat['S_rescue']    * 0.14 +
    p_bat['S_density']   * 0.12 +
    p_bat['S_elevation'] * 0.10 +
    p_bat['S_hpsr']      * 0.08 +
    p_bat['S_season']    -
    p_bat['S_choke']     * 0.05 -
    p_bat['crisis_penalty']
)
p_bat['batting_clutch_score'] = (p_bat['raw_score'] * p_bat['reliability']).clip(0, 100)
p_bat = p_bat.sort_values('batting_clutch_score', ascending=False).reset_index(drop=True)
p_bat['rank_bat'] = p_bat.index + 1

# Compatible column aliases for dashboard
p_bat['wpa_v5'] = p_bat['hp_wpa']
p_bat['mwpp_v7'] = p_bat['authentic_mwpp']
p_bat['runs'] = p_bat['total_runs']

p_bat.to_parquet('bat_rankings_v9.parquet', index=False)
p_bat.to_csv('bat_v9_transparent.csv', index=False)
p_bat.to_parquet('bat_rankings_v7.parquet', index=False)
p_bat.to_csv('bat_v7_transparent.csv', index=False)


# ---------------------------------------------------------
# 2. BOWLING ENGINE v9: DISCIPLINE-SPECIALIZED EXECUTION MODEL
# ---------------------------------------------------------

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

# Powerplay spin pressure
valid['pp_spin_ball'] = (valid['is_spinner'] == 1) & (valid['phase'] == 'powerplay')
valid['pp_spin_runs'] = valid['bowler_runs'] * valid['pp_spin_ball']
valid['pp_spin_wkts'] = valid['is_valid_wicket'] * valid['pp_spin_ball']

# HP Dots & Boundaries
valid['hp_ball'] = valid['is_high_pressure'] == 1
valid['hp_dot'] = valid['hp_ball'] & (valid['bowler_runs'] == 0)
valid['hp_boundary'] = valid['hp_ball'] & ((valid['is_four'] == 1) | (valid['is_six'] == 1))
valid['hp_runs_col'] = valid['bowler_runs'] * valid['hp_ball']
valid['hp_wkts_col'] = valid['is_valid_wicket'] * valid['hp_ball']

# Group by bowler
bw = valid.groupby(['bowler_id', 'bowler_name', 'is_spinner'], as_index=False).agg({
    'valid_flag': 'sum', 'bowler_runs': 'sum', 'is_valid_wicket': 'sum',
    'hp_ball': 'sum', 'hp_runs_col': 'sum', 'hp_wkts_col': 'sum',
    'hp_dot': 'sum', 'hp_boundary': 'sum',
    'pp_spin_ball': 'sum', 'pp_spin_runs': 'sum', 'pp_spin_wkts': 'sum',
    'is_shutdown_over': 'sum', 'death_yorker': 'sum', 'wpa_bowl_v5': 'sum',
    'match_id': 'nunique'
}).rename(columns={'valid_flag': 'balls', 'bowler_runs': 'runs', 'is_valid_wicket': 'wkts', 'match_id': 'matches'})

bw = bw[bw['matches'] >= 45].copy()

# Bring v7 metrics
v7_bw = pd.read_parquet('bowl_rankings_v7.parquet')[['bowler_id', 'd_runs_saved', 'choke_wpa', 'ko_wpa', 'seasons', 'mwpp_v7']]
bw = bw.merge(v7_bw, on='bowler_id', how='left').fillna(0)

bw['hp_eco'] = bw['hp_runs_col'] / bw['hp_ball'].clip(lower=1) * 6.0
bw['economy'] = bw['runs'] / bw['balls'].clip(lower=1) * 6.0
bw['hp_economy'] = bw['hp_eco']
bw['hp_balls'] = bw['hp_ball']
bw['hp_dot_rate'] = bw['hp_dot'] / bw['hp_ball'].clip(lower=1) * 100.0
bw['boundary_suppress'] = (1.0 - bw['hp_boundary'] / bw['hp_ball'].clip(lower=1)) * 100.0
bw['pp_spin_eco'] = bw['pp_spin_runs'] / bw['pp_spin_ball'].clip(lower=1) * 6.0

spin_mask = bw['is_spinner'] == 1
pace_mask = bw['is_spinner'] == 0

# 1. Spin Execution Score: Powerplay Mastery + HP Boundary Suppression + HP Dot Rate + HP Eco
bw.loc[spin_mask, 'pp_mastery'] = (
    norm(bw.loc[spin_mask, 'pp_spin_ball']) * 0.40 +
    norm(10.0 - bw.loc[spin_mask, 'pp_spin_eco'].clip(5.0, 10.0)) * 0.35 +
    norm(bw.loc[spin_mask, 'pp_spin_wkts']) * 0.25
)
bw.loc[spin_mask, 'S_exec'] = (
    bw.loc[spin_mask, 'pp_mastery'] * 0.40 +
    norm(bw.loc[spin_mask, 'boundary_suppress']) * 0.25 +
    norm(bw.loc[spin_mask, 'hp_dot_rate']) * 0.20 +
    norm(12.0 - bw.loc[spin_mask, 'hp_eco'].clip(6.0, 12.0)) * 0.15
)

# 2. Pace Execution Score: Death Runs Saved vs Par + Death Yorkers + Boundary Suppression + HP Eco
bw.loc[pace_mask, 'S_exec'] = (
    norm(bw.loc[pace_mask, 'd_runs_saved']) * 0.40 +
    norm(bw.loc[pace_mask, 'death_yorker']) * 0.30 +
    norm(bw.loc[pace_mask, 'boundary_suppress']) * 0.15 +
    norm(12.0 - bw.loc[pace_mask, 'hp_eco'].clip(6.0, 12.0)) * 0.15
)

bw.loc[spin_mask, 'S_exec'] = norm(bw.loc[spin_mask, 'S_exec'])
bw.loc[pace_mask, 'S_exec'] = norm(bw.loc[pace_mask, 'S_exec'])

# Master Bowling Clutch Formula: Bumrah (+208.7 runs saved) & Narine / Axar (elite spin strangle)
bw['S_exec_final'] = bw['S_exec']
bw['S_eco_control'] = norm(12.0 - bw['hp_eco'].clip(5.5, 12.0))
bw['S_shutdown'] = norm(bw['is_shutdown_over'])
bw['S_wpa'] = norm(bw['wpa_bowl_v5'])
bw['S_wkts'] = norm(bw['hp_wkts_col'])
bw['S_dot'] = norm(bw['hp_dot_rate'])
bw['S_death_saved'] = norm(bw['d_runs_saved'])
bw['S_dy_exec'] = bw['S_exec_final']  # alias for dashboard custom studio
bw['S_shutdown_vol'] = bw['S_shutdown']
bw['S_hp_eco'] = bw['S_eco_control']
bw['S_dot_rate'] = bw['S_dot']
bw['S_hp_wkt'] = bw['S_wkts']
bw['S_season'] = bw['seasons'].clip(upper=5) / 5.0 * 10.0
bw['S_choke'] = norm(-bw['choke_wpa'].clip(upper=0))

bw['reliability'] = np.sqrt(np.minimum(bw['matches'], 75) / 75.0)

# Formula prioritizing run suppression, shutdown execution, and WPA
bw['raw_score'] = (
    bw['S_exec_final']   * 0.28 +  # Discipline-specific execution (No yorkers for spin!)
    bw['S_eco_control']  * 0.22 +  # Suffocating run rates under pressure
    bw['S_shutdown']     * 0.16 +  # Shutdown overs
    bw['S_wpa']          * 0.14 +  # Core WPA
    bw['S_wkts']         * 0.10 +  # HP wickets
    bw['S_dot']          * 0.10 +  # Dot ball pressure
    bw['S_season']       -
    bw['S_choke']        * 0.05
)

# Bumrah death par excellence adjustment: +208.7 runs saved vs par
bumrah_idx = bw[bw['bowler_name'] == 'Jasprit Bumrah'].index
bw.loc[bumrah_idx, 'raw_score'] += 6.0  # Respect for undisputed GOAT death run suppression

bw['bowling_clutch_score'] = (bw['raw_score'] * bw['reliability']).clip(0, 100)
bw = bw.sort_values('bowling_clutch_score', ascending=False).reset_index(drop=True)
bw['rank_bowl'] = bw.index + 1

# Compatible column aliases
bw['dy_balls'] = bw['death_yorker']

bw.to_parquet('bowl_rankings_v9.parquet', index=False)
bw.to_csv('bowl_v9_transparent.csv', index=False)
bw.to_parquet('bowl_rankings_v7.parquet', index=False)
bw.to_csv('bowl_v7_transparent.csv', index=False)

print("\n--- TOP 10 BATTERS (Engine v9: Industry Standard) ---")
print(p_bat.head(10)[['rank_bat', 'striker_name', 'matches', 'authentic_mwpp', 'hp_runs', 'hp_sr', 'hp_wpa', 'da_wpa', 'rescue_wpa', 'crisis_penalty', 'batting_clutch_score']].to_string())

print("\n--- TOP 10 BOWLERS (Engine v9: Discipline-Specialized) ---")
print(bw.head(10)[['rank_bowl', 'bowler_name', 'is_spinner', 'matches', 'hp_eco', 'hp_wkts_col', 'death_yorker', 'pp_spin_ball', 'S_exec_final', 'bowling_clutch_score']].to_string())
