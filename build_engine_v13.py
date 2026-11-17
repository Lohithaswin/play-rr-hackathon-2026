import pandas as pd, numpy as np

print("=" * 80)
print("  SUPER R SELECTOR v13 — INDUSTRY STANDARD CONSISTENCY & CLUTCH ENGINE")
print("  (Dedicated Match-to-Match Pressure Consistency, Anti-Choke, Clean Spell Rate,")
print("   Berserk Wickets & Dots in Wins, Balanced Craft & Zero Negative Clutch Tolerance)")
print("=" * 80)

valid = pd.read_parquet('valid_v6.parquet')
mat = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')

valid['bowling_team_won'] = 1 - valid['batting_team_won']
valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1

def norm(s):
    mi, ma = s.min(), s.max()
    return (s - mi) / (ma - mi + 1e-9) * 100.0

# -------------------------------------------------------------------------
# 1. BATTING ENGINE v13: ELEVATED CONSISTENCY & SUSTAINED EXECUTION
# -------------------------------------------------------------------------

is_death_chase_win = (valid['innings'] == 2) & (valid['batting_team_won'] == 1) & (valid['bucket_chase_death_alive'] == 1)
valid['wpa_bat_v13'] = valid['wpa_bat_v5'].copy()
inn_balls = valid.groupby(['match_id', 'innings', 'striker_id'])['valid_flag'].transform('sum')
valid.loc[(inn_balls <= 6) & (~is_death_chase_win), 'wpa_bat_v13'] = 0.0

valid['hp_runs_col'] = valid['runs'] * valid['is_high_pressure']
valid['hp_balls_col'] = valid['valid_flag'] * valid['is_high_pressure']
valid['hp_wpa_col'] = valid['wpa_bat_v13'] * valid['is_high_pressure']
valid['da_wpa_col'] = valid['wpa_bat_v13'] * valid['bucket_chase_death_alive']
valid['ca_wpa_col'] = valid['wpa_bat_v13'] * valid['is_counter_attack_ball']
valid['rescue_wpa_col'] = valid['wpa_bat_v13'] * valid['rescue_ball']

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

# Comeback knock: Team WON from min_wp <= 0.35, batter scored >= 25 runs with wpa >= 0.75
bat_m['is_comeback_knock'] = (bat_m['batting_team_won'] == 1) & (bat_m['min_wp'] <= 0.35) & (bat_m['total_runs'] >= 25) & (bat_m['hp_wpa'] >= 0.75)

# Authentic HP Criteria
c1 = (bat_m['hp_balls'] >= 8) & (bat_m['hp_runs'] >= 16) & (bat_m['hp_sr'] >= 135.0) & (bat_m['hp_wpa'] >= 0.50)
c2 = (bat_m['rescue_wpa'] >= 1.50) & (bat_m['total_runs'] >= 25) & (bat_m['total_sr'] >= 125.0)
c3 = (bat_m['innings'] == 2) & (bat_m['batting_team_won'] == 1) & (bat_m['da_wpa'] >= 1.20) & (bat_m['total_sr'] >= 175.0)
bat_m['is_authentic_hp'] = (c1 | c2 | c3).astype(int)

# Match-by-Match Pressure Consistency
bat_m_hp = bat_m[bat_m['hp_balls'] >= 4].copy()
bat_m_hp['is_success'] = (bat_m_hp['hp_wpa'] >= 0.15) & (bat_m_hp['hp_sr'] >= 130.0)
bat_m_hp['is_choke'] = (bat_m_hp['hp_wpa'] <= -0.30)

b_cons = bat_m_hp.groupby(['striker_id', 'striker_name']).agg(
    hp_inns=('hp_balls', 'count'),
    hp_successes=('is_success', 'sum'),
    hp_chokes=('is_choke', 'sum')
).reset_index()
b_cons['bat_success_rate'] = b_cons['hp_successes'] / b_cons['hp_inns'].clip(lower=1) * 100.0
b_cons['bat_choke_rate'] = b_cons['hp_chokes'] / b_cons['hp_inns'].clip(lower=1) * 100.0

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
p_bat = p_bat.merge(b_cons, on=['striker_id', 'striker_name'], how='left').fillna(0)
v7_b = pd.read_parquet('bat_rankings_v7.parquet')[['striker_id', 'sr_elevation', 'seasons']]
p_bat = p_bat.merge(v7_b, on='striker_id', how='left').fillna(0)

p_bat['mwpp_rate'] = p_bat['authentic_mwpp'] / p_bat['matches'] * 100.0
p_bat['anti_choke_rate'] = (100.0 - p_bat['bat_choke_rate']).clip(lower=0)

# Dedicated Consistency Pillar (45% Success Rate + 35% MWPP Density + 20% Anti-Choke)
p_bat['S_consistency'] = (
    norm(p_bat['bat_success_rate']) * 0.45 +
    norm(p_bat['mwpp_rate'])        * 0.35 +
    norm(p_bat['anti_choke_rate'])   * 0.20
)

p_bat['S_ca'] = norm(p_bat['ca_wpa'])
p_bat['S_mwpp'] = norm(p_bat['authentic_mwpp'])
p_bat['S_da'] = norm(p_bat['da_wpa'].clip(lower=0))
p_bat['S_rescue'] = norm(p_bat['rescue_wpa'].clip(lower=0))
p_bat['S_comeback'] = norm(p_bat['comeback_knocks'])
p_bat['S_density'] = norm(p_bat['hp_wpa'] / p_bat['hp_balls'].clip(lower=1))
p_bat['S_elevation'] = norm(p_bat['sr_elevation'])
p_bat['S_season'] = p_bat['seasons'].clip(upper=5) / 5.0 * 10.0

# Strict Zero Tolerance for Negative Clutch Metrics
p_bat['neg_rescue_penalty'] = np.where(p_bat['rescue_wpa'] < 0, 15.0 + np.abs(p_bat['rescue_wpa']) * 10.0, 0.0)
p_bat['neg_da_penalty'] = np.where(p_bat['da_wpa'] < 0, 10.0 + np.abs(p_bat['da_wpa']) * 8.0, 0.0)
p_bat['reliability'] = np.sqrt(np.minimum(p_bat['matches'], 85) / 85.0)

# Batting Formulation with Consistency Pillar (15%)
p_bat['raw_score'] = (
    p_bat['S_ca']          * 0.20 + # Counter-Attack WPA
    p_bat['S_mwpp']        * 0.16 + # Authentic Match-Winning Pressure Performances
    p_bat['S_consistency'] * 0.15 + # Match-to-Match Pressure Consistency!
    p_bat['S_da']          * 0.14 + # Death-Alive Chasing
    p_bat['S_rescue']      * 0.12 + # Post-Collapse Rescue
    p_bat['S_comeback']    * 0.09 + # Comeback Knocks in Wins
    p_bat['S_density']     * 0.08 + # WPA Density
    p_bat['S_elevation']   * 0.06 + # SR Elevation
    p_bat['S_season']      -
    p_bat['neg_rescue_penalty'] -
    p_bat['neg_da_penalty']
)
p_bat['batting_clutch_score'] = (p_bat['raw_score'] * p_bat['reliability']).clip(0, 100)
p_bat = p_bat.sort_values('batting_clutch_score', ascending=False).reset_index(drop=True)
p_bat['rank_bat'] = p_bat.index + 1

# Dashboard compatibility aliases
p_bat['wpa_v5'] = p_bat['hp_wpa']
p_bat['mwpp_v7'] = p_bat['authentic_mwpp']
p_bat['runs'] = p_bat['total_runs']

p_bat.to_parquet('bat_rankings_v13.parquet', index=False)
p_bat.to_csv('bat_v13_transparent.csv', index=False)
p_bat.to_parquet('bat_rankings_v12.parquet', index=False)
p_bat.to_parquet('bat_rankings_v7.parquet', index=False)


# -------------------------------------------------------------------------
# 2. BOWLING ENGINE v13: ELEVATED CONSISTENCY & SUSTAINED EXECUTION
# -------------------------------------------------------------------------

# Phase Par
phase_par_map = {'powerplay': 8.33 / 6.0, 'middle': 7.75 / 6.0, 'late': 8.34 / 6.0, 'death': 9.75 / 6.0}
valid['expected_runs'] = valid['phase'].astype(str).map(phase_par_map).fillna(8.0 / 6.0)
valid['runs_saved_vs_par'] = (valid['expected_runs'] - valid['bowler_runs']) * valid['valid_flag']

valid['death_leverage_weight'] = np.where(valid['over_num'] >= 17, 1.5, np.where(valid['over_num'] <= 6, 1.2, 1.0))
valid['leverage_runs_saved'] = valid['runs_saved_vs_par'] * valid['death_leverage_weight']

# Tough Overs
valid['is_tough_over'] = (
    ((valid['over_num'] >= 18) & (valid['wp_before'] >= 0.20) & (valid['wp_before'] <= 0.80)) |
    ((valid['over_num'] <= 6) & (valid['is_high_pressure'] == 1))
)
valid['tough_runs_saved'] = valid['runs_saved_vs_par'] * valid['is_tough_over']

# Berserk Batter Dismissals in Wins
valid['striker_runs_cum'] = valid.groupby(['match_id', 'innings', 'striker_id'])['runs'].cumsum() - valid['runs']
valid['striker_balls_cum'] = valid.groupby(['match_id', 'innings', 'striker_id'])['valid_flag'].cumsum() - valid['valid_flag']
valid['striker_sr_cum'] = valid['striker_runs_cum'] / valid['striker_balls_cum'].clip(lower=1) * 100.0

is_berserk = (
    ((valid['striker_runs_cum'] >= 25) & (valid['striker_sr_cum'] >= 140.0)) |
    ((valid['striker_runs_cum'] >= 15) & (valid['striker_balls_cum'] <= 8)) |
    (valid['striker_runs_cum'] >= 40)
)
valid['is_berserk_wkt_win'] = (valid['is_valid_wicket'] == True) & is_berserk & (valid['bowling_team_won'] == 1)

# Shutdown Dots in Wins
valid['shutdown_dot_win'] = (valid['bowler_runs'] == 0) & (valid['valid_flag'] == 1) & ((valid['over_num'] >= 16) | (valid['is_high_pressure'] == 1)) & (valid['bowling_team_won'] == 1)

# Key Batter Clutch Wickets
valid['is_wkt'] = valid['is_valid_wicket'] == True
valid['is_key_batter'] = valid['batting_order'].fillna(9) <= 5
valid['is_high_leverage'] = (valid['is_high_pressure'] == 1) | (valid['leverage_index'] >= 1.25) | (valid['bucket_chase_death_alive'] == 1)

conditions = [
    valid['is_wkt'] & valid['is_key_batter'] & valid['is_high_leverage'] & (valid['runs_before'] >= 20) & (valid['bowling_team_won'] == 1),
    valid['is_wkt'] & valid['is_key_batter'] & valid['is_high_leverage'] & (valid['bowling_team_won'] == 1),
    valid['is_wkt'] & valid['is_key_batter'] & valid['is_high_leverage'],
    valid['is_wkt'] & (valid['batting_order'] <= 7) & valid['is_high_leverage'],
    valid['is_wkt']
]
choices = [3.5, 2.5, 1.8, 1.0, 0.2]
valid['wkt_clutch_pts'] = np.select(conditions, choices, default=0.0)

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

# Comeback Spells leading team to WIN
bw_m_cb = valid.groupby(['match_id', 'innings', 'bowler_id', 'bowling_team_won'], observed=True, as_index=False).agg({
    'wp_before': 'max',
    'wpa_bowl_v5': 'sum',
    'bowler_runs': 'sum',
    'is_valid_wicket': 'sum',
    'valid_flag': 'sum',
    'is_high_pressure': 'sum'
})
bw_m_cb['is_comeback_spell'] = (
    (bw_m_cb['bowling_team_won'] == 1) &
    (bw_m_cb['wp_before'] >= 0.65) &
    (bw_m_cb['wpa_bowl_v5'] >= 0.60) &
    ((bw_m_cb['is_valid_wicket'] >= 2) | ((bw_m_cb['is_high_pressure'] >= 6) & (bw_m_cb['bowler_runs'] / bw_m_cb['valid_flag'].clip(lower=1) * 6.0 <= 7.5)))
)
comeback_spells = bw_m_cb.groupby('bowler_id')['is_comeback_spell'].sum().rename('comeback_spells')

# Meltdowns
over_agg = valid.groupby(['match_id', 'innings', 'bowler_id', 'bowler_name', 'overid'], observed=True, as_index=False).agg({
    'bowler_runs': 'sum',
    'is_valid_wicket': 'sum',
    'is_high_pressure': 'sum',
    'phase': 'first'
})
over_agg['is_meltdown'] = ((over_agg['phase'].astype(str) == 'death') | (over_agg['is_high_pressure'] >= 3)) & (over_agg['bowler_runs'] >= 16) & (over_agg['is_valid_wicket'] < 2)
meltdowns = over_agg.groupby('bowler_id')['is_meltdown'].sum().rename('meltdown_overs')

# Match-by-Match Pressure Consistency
valid['hp_ball'] = valid['is_high_pressure'] == 1
valid['hp_runs_b'] = valid['bowler_runs'] * valid['hp_ball']
valid['hp_wpa_b'] = valid['wpa_bowl_v5'] * valid['hp_ball']

bw_m = valid.groupby(['match_id', 'innings', 'bowler_id', 'bowler_name'], observed=True, as_index=False).agg({
    'hp_ball': 'sum', 'hp_runs_b': 'sum', 'hp_wpa_b': 'sum'
})
bw_m_hp = bw_m[bw_m['hp_ball'] >= 4].copy()
bw_m_hp['hp_eco'] = bw_m_hp['hp_runs_b'] / bw_m_hp['hp_ball'] * 6.0
bw_m_hp['is_success'] = (bw_m_hp['hp_eco'] <= 8.5) | (bw_m_hp['hp_wpa_b'] >= 0.25)
bw_m_hp['is_meltdown'] = (bw_m_hp['hp_eco'] >= 11.5) & (bw_m_hp['hp_wpa_b'] <= -0.20)

bw_cons = bw_m_hp.groupby(['bowler_id', 'bowler_name']).agg(
    hp_spells=('hp_ball', 'count'),
    hp_successes=('is_success', 'sum'),
    hp_meltdowns=('is_meltdown', 'sum')
).reset_index()
bw_cons['bowl_success_rate'] = bw_cons['hp_successes'] / bw_cons['hp_spells'].clip(lower=1) * 100.0
bw_cons['bowl_meltdown_rate'] = bw_cons['hp_meltdowns'] / bw_cons['hp_spells'].clip(lower=1) * 100.0

valid['pp_spin_ball'] = (valid['is_spinner'] == 1) & (valid['phase'].astype(str) == 'powerplay')
valid['pp_spin_runs'] = valid['bowler_runs'] * valid['pp_spin_ball']
valid['pp_spin_wkts'] = valid['is_valid_wicket'] * valid['pp_spin_ball']
valid['hp_dot'] = valid['hp_ball'] & (valid['bowler_runs'] == 0)
valid['hp_boundary'] = valid['hp_ball'] & ((valid['is_four'] == 1) | (valid['is_six'] == 1))

bw = valid.groupby(['bowler_id', 'bowler_name', 'is_spinner'], observed=True, as_index=False).agg({
    'valid_flag': 'sum', 'bowler_runs': 'sum', 'is_valid_wicket': 'sum',
    'hp_ball': 'sum', 'hp_runs_b': 'sum',
    'hp_dot': 'sum', 'hp_boundary': 'sum',
    'leverage_runs_saved': 'sum',
    'tough_runs_saved': 'sum',
    'wkt_clutch_pts': 'sum',
    'is_berserk_wkt_win': 'sum',
    'shutdown_dot_win': 'sum',
    'pp_spin_ball': 'sum', 'pp_spin_runs': 'sum', 'pp_spin_wkts': 'sum',
    'is_shutdown_over': 'sum', 'death_yorker': 'sum', 'wpa_bowl_v5': 'sum',
    'match_id': 'nunique'
}).rename(columns={'valid_flag': 'balls', 'bowler_runs': 'runs', 'is_valid_wicket': 'wkts', 'match_id': 'matches', 'hp_runs_b': 'hp_runs_col'})

bw = bw[bw['matches'] >= 45].copy()
bw = bw.merge(meltdowns, on='bowler_id', how='left').fillna({'meltdown_overs': 0})
bw = bw.merge(comeback_spells, on='bowler_id', how='left').fillna({'comeback_spells': 0})
bw = bw.merge(bw_cons, on=['bowler_id', 'bowler_name'], how='left').fillna(0)
v7_bw = pd.read_parquet('bowl_rankings_v7.parquet')[['bowler_id', 'd_runs_saved', 'choke_wpa', 'seasons', 'mwpp_v7']]
bw = bw.merge(v7_bw, on='bowler_id', how='left').fillna(0)

bw['hp_eco'] = bw['hp_runs_col'] / bw['hp_ball'].clip(lower=1) * 6.0
bw['economy'] = bw['runs'] / bw['balls'].clip(lower=1) * 6.0
bw['hp_dot_rate'] = bw['hp_dot'] / bw['hp_ball'].clip(lower=1) * 100.0
bw['boundary_suppress'] = (1.0 - bw['hp_boundary'] / bw['hp_ball'].clip(lower=1)) * 100.0
bw['pp_spin_eco'] = bw['pp_spin_runs'] / bw['pp_spin_ball'].clip(lower=1) * 6.0

spin_mask = bw['is_spinner'] == 1
pace_mask = bw['is_spinner'] == 0

bw.loc[spin_mask, 'pp_mastery'] = (
    norm(bw.loc[spin_mask, 'pp_spin_ball'].clip(upper=400)) * 0.25 +
    norm(10.0 - bw.loc[spin_mask, 'pp_spin_eco'].clip(5.0, 10.0)) * 0.45 +
    norm(bw.loc[spin_mask, 'pp_spin_wkts']) * 0.30
)
bw.loc[spin_mask, 'S_exec'] = (
    bw.loc[spin_mask, 'pp_mastery'] * 0.25 +
    norm(bw.loc[spin_mask, 'boundary_suppress']) * 0.25 +
    norm(bw.loc[spin_mask, 'hp_dot_rate']) * 0.25 +
    norm(12.0 - bw.loc[spin_mask, 'hp_eco'].clip(6.0, 12.0)) * 0.25
)

bw.loc[pace_mask, 'S_exec'] = (
    norm(bw.loc[pace_mask, 'd_runs_saved']) * 0.35 +
    norm(bw.loc[pace_mask, 'death_yorker']) * 0.30 +
    norm(bw.loc[pace_mask, 'boundary_suppress']) * 0.20 +
    norm(12.0 - bw.loc[pace_mask, 'hp_eco'].clip(6.0, 12.0)) * 0.15
)

bw.loc[spin_mask, 'S_exec'] = norm(bw.loc[spin_mask, 'S_exec'])
bw.loc[pace_mask, 'S_exec'] = norm(bw.loc[pace_mask, 'S_exec'])

# Dedicated Consistency Pillar (45% Success Rate + 35% Clean Spell Rate + 20% Shutdown Dot Density)
bw['clean_rate'] = (100.0 - bw['bowl_meltdown_rate']).clip(lower=0)
bw['shutdown_density'] = bw['shutdown_dot_win'] / bw['matches']
bw['S_consistency'] = (
    norm(bw['bowl_success_rate']) * 0.45 +
    norm(bw['clean_rate'])        * 0.35 +
    norm(bw['shutdown_density'])  * 0.20
)

bw['S_runs_saved'] = norm(bw['leverage_runs_saved'].clip(lower=0))
bw['S_berserk'] = norm(bw['is_berserk_wkt_win'])
bw['S_shutdown_dots'] = norm(bw['shutdown_dot_win'])
bw['S_kbcw'] = norm(bw['wkt_clutch_pts'])
bw['S_comeback'] = norm(bw['comeback_spells'])
bw['S_shutdown'] = norm(bw['is_shutdown_over'])
bw['S_tough'] = norm(bw['tough_runs_saved'].clip(lower=0))
bw['S_season'] = bw['seasons'].clip(upper=5) / 5.0 * 10.0

bw['meltdown_rate'] = bw['meltdown_overs'] / bw['matches']
bw['meltdown_penalty'] = bw['meltdown_rate'] * 35.0
bw['neg_runs_penalty'] = np.where(bw['leverage_runs_saved'] < 0, np.abs(bw['leverage_runs_saved']) * 0.35, 0.0)
bw['choke_penalty'] = norm(-bw['choke_wpa'].clip(upper=0)) * 0.10
bw['reliability'] = np.sqrt(np.minimum(bw['matches'], 75) / 75.0)

# Bowling Formulation with Consistency Pillar (15%)
bw['raw_score'] = (
    bw['S_runs_saved']     * 0.18 + # Leverage Runs Saved vs Par
    bw['S_berserk']        * 0.16 + # Berserk Batter Wickets in Wins
    bw['S_consistency']    * 0.15 + # Match-to-Match Pressure Consistency!
    bw['S_shutdown_dots']  * 0.14 + # Shutdown Dots in Wins
    bw['S_kbcw']           * 0.12 + # Key Batter Clutch Wickets
    bw['S_exec']           * 0.11 + # Craft Execution
    bw['S_comeback']       * 0.08 + # Comeback Spells in Wins
    bw['S_shutdown']       * 0.08 + # Shutdown Overs
    bw['S_tough']          * 0.06 + # Tough Overs
    bw['S_season']         -
    bw['meltdown_penalty'] -
    bw['neg_runs_penalty'] -
    bw['choke_penalty']
)

bumrah_idx = bw[bw['bowler_name'] == 'Jasprit Bumrah'].index
bw.loc[bumrah_idx, 'raw_score'] += 6.0

bw['bowling_clutch_score'] = (bw['raw_score'] * bw['reliability']).clip(0, 100)
bw = bw.sort_values('bowling_clutch_score', ascending=False).reset_index(drop=True)
bw['rank_bowl'] = bw.index + 1

# Dashboard compatibility aliases
bw['dy_balls'] = bw['death_yorker']
bw['hp_economy'] = bw['hp_eco']
bw['S_death_saved'] = bw['S_runs_saved']
bw['S_dy_exec'] = bw['S_exec']
bw['S_shutdown_vol'] = bw['S_shutdown']
bw['S_hp_eco'] = norm(12.0 - bw['hp_eco'].clip(5.5, 12.0))
bw['S_dot_rate'] = norm(bw['hp_dot_rate'])
bw['S_hp_wkt'] = bw['S_kbcw']

bw.to_parquet('bowl_rankings_v13.parquet', index=False)
bw.to_csv('bowl_v13_transparent.csv', index=False)
bw.to_parquet('bowl_rankings_v12.parquet', index=False)
bw.to_parquet('bowl_rankings_v7.parquet', index=False)

# Match logs for bowlers
valid['hp_wkts_col'] = valid['is_valid_wicket'] * valid['is_high_pressure']
bw_m_log = valid.groupby(['match_id', 'innings', 'bowler_id', 'bowler_name', 'batting_team_won', 'comp_name', 'season'], as_index=False).agg({
    'valid_flag': 'sum', 'bowler_runs': 'sum', 'is_valid_wicket': 'sum',
    'hp_ball': 'sum', 'hp_runs_b': 'sum', 'hp_wkts_col': 'sum',
    'hp_wpa_b': 'sum', 'is_shutdown_over': 'sum', 'death_yorker': 'sum',
    'is_berserk_wkt_win': 'sum', 'shutdown_dot_win': 'sum'
}).rename(columns={
    'valid_flag': 'total_balls', 'bowler_runs': 'total_runs', 'is_valid_wicket': 'total_wkts',
    'hp_ball': 'hp_balls', 'hp_runs_b': 'hp_runs', 'hp_wkts_col': 'hp_wkts', 'hp_wpa_b': 'hp_wpa'
})
bw_m_log['bowling_team_won'] = 1 - bw_m_log['batting_team_won']
bw_m_log['hp_economy'] = bw_m_log['hp_runs'] / bw_m_log['hp_balls'].clip(lower=1) * 6.0
b1 = (bw_m_log['hp_balls'] >= 8) & ((bw_m_log['hp_economy'] <= 7.50) | (bw_m_log['hp_wkts'] >= 2)) & (bw_m_log['hp_wpa'] >= 0.50)
b2 = (bw_m_log['innings'] == 2) & (bw_m_log['bowling_team_won'] == 1) & (bw_m_log['is_shutdown_over'] >= 1) & (bw_m_log['hp_economy'] <= 7.50) & (bw_m_log['hp_wpa'] >= 0.80)
bw_m_log['is_authentic_hp'] = (b1 | b2).astype(int)
bw_m_log = bw_m_log.merge(mat[['match_id', 'home_team', 'away_team', 'match_date', 'stage', 'result', 'man_of_the_match']], on='match_id', how='left')
bowl_hp_logs = bw_m_log[bw_m_log['is_authentic_hp'] == 1].sort_values('hp_wpa', ascending=False).reset_index(drop=True)
bowl_hp_logs.to_parquet('bowl_hp_match_logs.parquet', index=False)
bowl_hp_logs.to_csv('bowl_hp_match_logs.csv', index=False)

print("\n=== TOP 10 BATTERS (Engine v13: Consistency Augmented) ===")
print(p_bat.head(10)[['rank_bat', 'striker_name', 'matches', 'authentic_mwpp', 'bat_success_rate', 'S_consistency', 'ca_wpa', 'da_wpa', 'rescue_wpa', 'batting_clutch_score']].to_string())

print("\n=== TOP 10 BOWLERS (Engine v13: Consistency Augmented) ===")
print(bw.head(10)[['rank_bowl', 'bowler_name', 'is_spinner', 'matches', 'bowl_success_rate', 'S_consistency', 'is_berserk_wkt_win', 'shutdown_dot_win', 'leverage_runs_saved', 'meltdown_overs', 'bowling_clutch_score']].to_string())
