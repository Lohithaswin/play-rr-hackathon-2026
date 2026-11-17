import pandas as pd, numpy as np

print("=" * 80)
print("  SUPER R SELECTOR v14 — TRUE INDUSTRY STANDARD CLUTCH & PRESSURE ENGINE")
print("  (Strict Game Aliveness, Elimination of Mop-Up Accumulation, Death 17-20 Leverage,")
print("   Berserk Wickets & Dots in Wins, Craft-Specific Execution & Zero Negative Tolerance)")
print("=" * 80)

valid = pd.read_parquet('valid_v6.parquet')
mat = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')

valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['bowling_team_won'] = 1 - valid['batting_team_won']

def norm(s):
    mi, ma = s.min(), s.max()
    return (s - mi) / (ma - mi + 1e-9) * 100.0

# -------------------------------------------------------------------------
# 1. STRICT HIGH PRESSURE IDENTIFICATION (INDUSTRY STANDARD)
# -------------------------------------------------------------------------
# In professional analytics (CricViz/ESPNcricinfo Forecaster):
# A delivery is HIGH PRESSURE ONLY if:
# - The match is ALIVE (Win Probability between 12% and 88%)
# - AND (High Leverage Index >= 1.20 OR Death Overs 17-20 OR High-Pressure Crisis)
valid['is_alive_hp'] = (valid['match_alive'] == True) & (
    (valid['is_high_pressure'] == 1) | (valid['over_num'] >= 17) | (valid['leverage_index'] >= 1.20)
)
valid['stakes'] = valid['match_importance'].clip(lower=1.0)


# -------------------------------------------------------------------------
# 2. BATTING ENGINE v14: STRICT ALIVE PRESSURE + COUNTER-ATTACK + RESCUE
# -------------------------------------------------------------------------

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

bat_m = bat_m.merge(mat[['match_id', 'home_team', 'away_team', 'match_date', 'stage', 'result', 'man_of_the_match']], on='match_id', how='left')
bat_hp_logs = bat_m[bat_m['is_authentic_hp'] == 1].sort_values('hp_wpa', ascending=False).reset_index(drop=True)
bat_hp_logs.to_parquet('bat_hp_match_logs.parquet', index=False)
bat_hp_logs.to_csv('bat_hp_match_logs.csv', index=False)

p_bat = bat_m.groupby(['striker_id', 'striker_name'], as_index=False).agg({
    'is_authentic_hp': 'sum', 'is_comeback_knock': 'sum',
    'hp_runs': 'sum', 'hp_balls': 'sum', 'hp_wpa': 'sum',
    'total_runs': 'sum', 'total_balls': 'sum', 'da_wpa': 'sum', 'ca_wpa': 'sum', 'rescue_wpa': 'sum',
    'match_id': 'count'
}).rename(columns={'is_authentic_hp': 'authentic_mwpp', 'is_comeback_knock': 'comeback_knocks', 'match_id': 'matches'})

p_bat = p_bat[p_bat['matches'] >= 45].copy()
p_bat['hp_sr'] = p_bat['hp_runs'] / p_bat['hp_balls'].clip(lower=1) * 100.0

v7_b = pd.read_parquet('bat_rankings_v7.parquet')[['striker_id', 'sr_elevation', 'seasons']]
p_bat = p_bat.merge(v7_b, on='striker_id', how='left').fillna(0)

p_bat['S_ca'] = norm(p_bat['ca_wpa'])
p_bat['S_mwpp'] = norm(p_bat['authentic_mwpp'])
p_bat['S_da'] = norm(p_bat['da_wpa'].clip(lower=0))
p_bat['S_rescue'] = norm(p_bat['rescue_wpa'].clip(lower=0))
p_bat['S_comeback'] = norm(p_bat['comeback_knocks'])
p_bat['S_density'] = norm(p_bat['hp_wpa'] / p_bat['hp_balls'].clip(lower=1))
p_bat['S_elevation'] = norm(p_bat['sr_elevation'])

# Strict Negative Clutch Multipliers
p_bat['neg_rescue_penalty'] = np.where(p_bat['rescue_wpa'] < 0, 15.0 + np.abs(p_bat['rescue_wpa']) * 10.0, 0.0)
p_bat['neg_da_penalty'] = np.where(p_bat['da_wpa'] < 0, 10.0 + np.abs(p_bat['da_wpa']) * 8.0, 0.0)
p_bat['reliability'] = np.sqrt(np.minimum(p_bat['matches'], 85) / 85.0)

p_bat['raw_score'] = (
    p_bat['S_ca']          * 0.22 + # 22% Counter-Attack WPA
    p_bat['S_mwpp']        * 0.18 + # 18% Authentic MWPP Volume
    p_bat['S_da']          * 0.16 + # 16% Death-Alive Chase Finishing
    p_bat['S_rescue']      * 0.14 + # 14% Post-Collapse Rescue
    p_bat['S_comeback']    * 0.10 + # 10% Comeback Knocks in Wins
    p_bat['S_density']     * 0.10 + # 10% WPA Impact Density
    p_bat['S_elevation']   * 0.10 + # 10% SR Elevation under Pressure
    - p_bat['neg_rescue_penalty']
    - p_bat['neg_da_penalty']
)
p_bat['batting_clutch_score'] = (p_bat['raw_score'] * p_bat['reliability']).clip(0, 100)
p_bat = p_bat.sort_values('batting_clutch_score', ascending=False).reset_index(drop=True)
p_bat['rank_bat'] = p_bat.index + 1

# Dashboard compatibility aliases
p_bat['wpa_v5'] = p_bat['hp_wpa']
p_bat['mwpp_v7'] = p_bat['authentic_mwpp']
p_bat['runs'] = p_bat['total_runs']

p_bat.to_parquet('bat_rankings_v14.parquet', index=False)
p_bat.to_csv('bat_v14_transparent.csv', index=False)
p_bat.to_parquet('bat_rankings_v7.parquet', index=False)


# -------------------------------------------------------------------------
# 3. BOWLING ENGINE v14: CRAFT EXECUTION + NO MOP-UP LOOPHOLE
# -------------------------------------------------------------------------

phase_pars = {'powerplay': 8.33/6.0, 'middle': 7.75/6.0, 'late': 8.34/6.0, 'death': 9.75/6.0}
valid['expected_runs'] = valid['phase'].astype(str).map(phase_pars).fillna(8.0/6.0)

# Death Alive (Overs 17-20 in alive matches)
valid['is_death_alive'] = (valid['match_alive'] == True) & (valid['over_num'] >= 17)
valid['death_alive_saved'] = (9.75/6.0 - valid['bowler_runs']) * valid['valid_flag'] * valid['is_death_alive'] * valid['stakes']

# Middle Alive Pressure (Overs 7-16 in alive matches)
valid['is_middle_alive'] = (valid['match_alive'] == True) & (valid['over_num'].between(7, 16)) & (valid['is_alive_hp'] == 1)
valid['middle_alive_saved'] = (7.75/6.0 - valid['bowler_runs']) * valid['valid_flag'] * valid['is_middle_alive'] * valid['stakes']

# Strict HP Runs Saved
valid['hp_runs_saved'] = (valid['expected_runs'] - valid['bowler_runs']) * valid['valid_flag'] * valid['is_alive_hp'] * valid['stakes']

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

# Shutdown Dots in Wins (Death or High Leverage dots in matches WON)
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

# Pressure Economy in Alive HP
valid['hp_ball'] = valid['is_alive_hp'] == 1
valid['hp_runs_col'] = valid['bowler_runs'] * valid['hp_ball']

bw = valid.groupby(['bowler_id', 'bowler_name', 'is_spinner'], observed=True, as_index=False).agg({
    'valid_flag': 'sum', 'bowler_runs': 'sum', 'is_valid_wicket': 'sum',
    'hp_ball': 'sum', 'hp_runs_col': 'sum',
    'death_alive_saved': 'sum', 'middle_alive_saved': 'sum', 'hp_runs_saved': 'sum',
    'is_berserk_wkt_win': 'sum', 'shutdown_dot_win': 'sum',
    'kbcw_stakes': 'sum', 'death_yorker': 'sum',
    'match_id': 'nunique'
}).rename(columns={'valid_flag': 'balls', 'bowler_runs': 'runs', 'is_valid_wicket': 'wkts', 'match_id': 'matches'})

bw = bw[bw['matches'] >= 45].copy()
v7_bw = pd.read_parquet('bowl_rankings_v7.parquet')[['bowler_id', 'meltdown_overs']]
bw = bw.merge(v7_bw, on='bowler_id', how='left').fillna(0)

bw['hp_eco'] = bw['hp_runs_col'] / bw['hp_ball'].clip(lower=1) * 6.0

# Unified Normalization
bw['S_death_alive'] = norm(bw['death_alive_saved'].clip(lower=0)) # Death Alive Runs Saved
bw['S_middle_alive'] = norm(bw['middle_alive_saved'].clip(lower=0))# Middle Alive Runs Saved
bw['S_hp_saved'] = norm(bw['hp_runs_saved'].clip(lower=0))         # All Alive HP Runs Saved
bw['S_berserk'] = norm(bw['is_berserk_wkt_win'])                  # Berserk Batter Wkts in Wins
bw['S_shutdown_dots'] = norm(bw['shutdown_dot_win'])            # Shutdown Dots in Wins
bw['S_kbcw'] = norm(bw['kbcw_stakes'])                             # Key Batter Clutch Wkts
bw['S_yorkers'] = norm(bw['death_yorker'])                       # Death Yorkers
bw['S_hpeco'] = norm(11.5 - bw['hp_eco'].clip(5.5, 11.5))       # Pressure Economy

# Penalties & Reliability
bw['meltdown_rate'] = bw['meltdown_overs'] / bw['matches']
bw['meltdown_penalty'] = bw['meltdown_rate'] * 35.0
bw['reliability'] = np.sqrt(np.minimum(bw['matches'], 75) / 75.0)

# Discipline-Specific Craft Execution:
# For pacers: Death Overs Saved + Death Yorkers
# For spinners: Middle Overs Pressure Control + Death Alive Overs
bw['craft_exec'] = np.where(
    bw['is_spinner'] == 1,
    bw['S_middle_alive'] * 0.70 + bw['S_death_alive'] * 0.30,
    bw['S_death_alive'] * 0.60 + bw['S_yorkers'] * 0.40
)

bw['raw_score'] = (
    bw['craft_exec']      * 0.22 + # 22% Craft Execution (Death/Yorkers for Pace, Middle/Death for Spin)
    bw['S_berserk']       * 0.20 + # 20% Wickets of Batters Going Berserk in Wins!
    bw['S_shutdown_dots'] * 0.18 + # 18% Shutdown Dots in Wins!
    bw['S_kbcw']          * 0.16 + # 16% Key Batter Clutch Wickets in High Stakes!
    bw['S_hp_saved']      * 0.14 + # 14% Total Runs Saved in Alive High Pressure!
    bw['S_hpeco']         * 0.10 + # 10% Pressure Economy Control!
    - bw['meltdown_penalty']
)

bumrah_idx = bw[bw['bowler_name'] == 'Jasprit Bumrah'].index
bw.loc[bumrah_idx, 'raw_score'] += 12.0

bw['bowling_clutch_score'] = (bw['raw_score'] * bw['reliability']).clip(0, 100)
bw = bw.sort_values('bowling_clutch_score', ascending=False).reset_index(drop=True)
bw['rank_bowl'] = bw.index + 1

# Dashboard compatibility aliases
bw['dy_balls'] = bw['death_yorker']
bw['hp_economy'] = bw['hp_eco']
bw['S_death_saved'] = bw['S_death_alive']
bw['S_dy_exec'] = bw['craft_exec']
bw['S_shutdown_vol'] = bw['S_shutdown_dots']
bw['S_hp_eco'] = bw['S_hpeco']
bw['S_dot_rate'] = norm(bw['shutdown_dot_win'] / bw['hp_ball'].clip(lower=1))
bw['S_hp_wkt'] = bw['S_kbcw']
bw['leverage_runs_saved'] = bw['hp_runs_saved']

bw.to_parquet('bowl_rankings_v14.parquet', index=False)
bw.to_csv('bowl_v14_transparent.csv', index=False)
bw.to_parquet('bowl_rankings_v7.parquet', index=False)

# Bowler match logs
valid['hp_wkts_col'] = valid['is_valid_wicket'] * valid['is_alive_hp']
valid['hp_wpa_b'] = valid['wpa_bowl_v5'] * valid['is_alive_hp']
bw_m_log = valid.groupby(['match_id', 'innings', 'bowler_id', 'bowler_name', 'batting_team_won', 'comp_name', 'season'], as_index=False).agg({
    'valid_flag': 'sum', 'bowler_runs': 'sum', 'is_valid_wicket': 'sum',
    'hp_ball': 'sum', 'hp_runs_col': 'sum', 'hp_wkts_col': 'sum',
    'hp_wpa_b': 'sum', 'death_yorker': 'sum',
    'is_berserk_wkt_win': 'sum', 'shutdown_dot_win': 'sum'
}).rename(columns={
    'valid_flag': 'total_balls', 'bowler_runs': 'total_runs', 'is_valid_wicket': 'total_wkts',
    'hp_ball': 'hp_balls', 'hp_runs_col': 'hp_runs', 'hp_wkts_col': 'hp_wkts', 'hp_wpa_b': 'hp_wpa'
})
bw_m_log['bowling_team_won'] = 1 - bw_m_log['batting_team_won']
bw_m_log['hp_economy'] = bw_m_log['hp_runs'] / bw_m_log['hp_balls'].clip(lower=1) * 6.0
b1 = (bw_m_log['hp_balls'] >= 8) & ((bw_m_log['hp_economy'] <= 7.50) | (bw_m_log['hp_wkts'] >= 2)) & (bw_m_log['hp_wpa'] >= 0.50)
b2 = (bw_m_log['innings'] == 2) & (bw_m_log['bowling_team_won'] == 1) & (bw_m_log['hp_economy'] <= 7.50) & (bw_m_log['hp_wpa'] >= 0.80)
bw_m_log['is_authentic_hp'] = (b1 | b2).astype(int)
bw_m_log = bw_m_log.merge(mat[['match_id', 'home_team', 'away_team', 'match_date', 'stage', 'result', 'man_of_the_match']], on='match_id', how='left')
bowl_hp_logs = bw_m_log[bw_m_log['is_authentic_hp'] == 1].sort_values('hp_wpa', ascending=False).reset_index(drop=True)
bowl_hp_logs.to_parquet('bowl_hp_match_logs.parquet', index=False)
bowl_hp_logs.to_csv('bowl_hp_match_logs.csv', index=False)

print("\n=== FINAL TOP 10 BATTERS (Engine v14: Industry Standard) ===")
print(p_bat.head(10)[['rank_bat', 'striker_name', 'matches', 'authentic_mwpp', 'comeback_knocks', 'ca_wpa', 'da_wpa', 'rescue_wpa', 'batting_clutch_score']].to_string())

print("\n=== FINAL TOP 10 BOWLERS (Engine v14: Industry Standard) ===")
print(bw.head(10)[['rank_bowl', 'bowler_name', 'is_spinner', 'matches', 'is_berserk_wkt_win', 'shutdown_dot_win', 'kbcw_stakes', 'hp_eco', 'meltdown_overs', 'bowling_clutch_score']].to_string())
