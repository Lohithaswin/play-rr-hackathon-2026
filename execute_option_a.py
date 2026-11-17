import pandas as pd
import numpy as np

print("=" * 80)
print("  EXECUTING OPTION A: DEFINITIVE INDUSTRY-STANDARD PRESSURE SYSTEM")
print("=" * 80)

valid = pd.read_parquet('valid_v7_ml.parquet')
valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['bowling_team_won'] = 1 - valid['batting_team_won']

# 1. BIG-STAGE MATCH STAKES MULTIPLIER
def get_stakes(row):
    comp = str(row['comp_name']).lower()
    imp = row['match_importance']
    if 'final' in comp or imp >= 2.5:
        return 1.75
    elif 'playoff' in comp or 'qualifier' in comp or 'eliminator' in comp or imp >= 2.0:
        return 1.50
    elif 'world cup' in comp or 'asia cup' in comp or imp >= 1.3:
        return 1.30
    elif 'ipl' in comp:
        return 1.15
    return 1.00

valid['stakes'] = valid.apply(get_stakes, axis=1)

valid['is_alive_hp'] = (valid['match_alive'] == True) & (
    (valid['is_high_pressure'] == 1) | (valid['over_num'] >= 17) | (valid['leverage_index'] >= 1.20)
)
valid['is_high_rr'] = (
    (valid['current_rr'] >= 9.0) |
    (valid['required_rr'] >= 9.5) |
    (valid['recent_avg_rr'] >= 9.5)
)

valid['striker_runs_cum'] = valid.groupby(['match_id', 'innings', 'striker_id'])['runs'].cumsum() - valid['runs']
valid['striker_balls_cum'] = valid.groupby(['match_id', 'innings', 'striker_id'])['valid_flag'].cumsum() - valid['valid_flag']
valid['striker_sr_cum'] = valid['striker_runs_cum'] / valid['striker_balls_cum'].clip(lower=1) * 100.0

is_berserk = (
    ((valid['striker_runs_cum'] >= 20) & (valid['striker_sr_cum'] >= 140.0)) |
    ((valid['striker_runs_cum'] >= 15) & (valid['striker_balls_cum'] <= 8)) |
    (valid['striker_runs_cum'] >= 35)
)
valid['is_berserk'] = is_berserk
valid['is_key_batter'] = valid['batting_order'].fillna(9) <= 5

# Bowling core deliveries
valid['dot_high_rr_win'] = (valid['bowler_runs'] == 0) & (valid['valid_flag'] == 1) & (valid['match_alive'] == True) & (valid['is_high_rr'] | valid['is_berserk'] | (valid['is_alive_hp'] == 1)) & (valid['bowling_team_won'] == 1) * valid['stakes']

valid['wkt_pp_key_win'] = valid['is_valid_wicket'] & valid['is_key_batter'] & (valid['over_num'] <= 6) & (valid['match_alive'] == True) & (valid['bowling_team_won'] == 1) * valid['stakes']
valid['wkt_mid_berserk_win'] = valid['is_valid_wicket'] & (valid['is_berserk'] | valid['is_key_batter']) & valid['over_num'].between(7, 16) & (valid['match_alive'] == True) & (valid['bowling_team_won'] == 1) * valid['stakes']
valid['wkt_death_win'] = valid['is_valid_wicket'] & (valid['over_num'] >= 17) & (valid['match_alive'] == True) & (valid['bowling_team_won'] == 1) * valid['stakes']

valid['ml_runs_saved'] = (valid['ml_expected_runs'] - valid['bowler_runs']) * valid['valid_flag'] * valid['stakes']
valid['ml_hp_runs_saved'] = valid['ml_runs_saved'] * (valid['is_alive_hp'] == 1)
valid['ml_pp_runs_saved'] = valid['ml_runs_saved'] * (valid['match_alive'] == True) * (valid['over_num'] <= 6) * (valid['is_high_rr'] == 1)
valid['ml_mid_runs_saved'] = valid['ml_runs_saved'] * (valid['match_alive'] == True) * valid['over_num'].between(7, 16) * ((valid['is_alive_hp'] == 1) | (valid['is_high_rr'] == 1))
valid['ml_death_runs_saved'] = valid['ml_runs_saved'] * (valid['match_alive'] == True) * (valid['over_num'] >= 17)

valid['hp_wpa_b'] = valid['wpa_bowl_v5'] * valid['is_alive_hp'] * valid['stakes']
valid['hp_ball'] = valid['is_alive_hp'] == 1
valid['hp_runs_col'] = valid['bowler_runs'] * valid['hp_ball']

# Phase balls for role-weighting
valid['ball_pp'] = (valid['valid_flag'] == 1) & (valid['match_alive'] == True) & (valid['over_num'] <= 6) & (valid['is_high_rr'] == 1)
valid['ball_mid'] = (valid['valid_flag'] == 1) & (valid['match_alive'] == True) & valid['over_num'].between(7, 16) & ((valid['is_alive_hp'] == 1) | (valid['is_high_rr'] == 1))
valid['ball_death'] = (valid['valid_flag'] == 1) & (valid['match_alive'] == True) & (valid['over_num'] >= 17)

# Match consistency
bw_match = valid[valid['is_alive_hp'] == 1].groupby(['match_id', 'bowler_id', 'bowler_name'], as_index=False).agg({
    'hp_ball': 'sum', 'hp_runs_col': 'sum', 'is_valid_wicket': 'sum',
    'ml_hp_runs_saved': 'sum', 'hp_wpa_b': 'sum'
})
bw_match['hp_eco'] = bw_match['hp_runs_col'] / bw_match['hp_ball'].clip(lower=1) * 6.0
bw_match['is_quality_hp'] = (
    (bw_match['ml_hp_runs_saved'] > 0) &
    ((bw_match['hp_wpa_b'] > 0) | (bw_match['is_valid_wicket'] >= 1) | (bw_match['hp_eco'] <= 8.5))
).astype(int)

bw_cons = bw_match.groupby('bowler_id', as_index=False).agg({
    'match_id': 'count', 'is_quality_hp': 'sum'
}).rename(columns={'match_id': 'hp_matches_faced', 'is_quality_hp': 'hp_matches_positive'})
bw_cons['hp_consistency_rate'] = bw_cons['hp_matches_positive'] / bw_cons['hp_matches_faced'].clip(lower=1)

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

bw_tot = valid.groupby(['bowler_id', 'bowler_name', 'is_spinner'], observed=True, as_index=False).agg({
    'valid_flag': 'sum', 'bowler_runs': 'sum', 'is_valid_wicket': 'sum',
    'hp_ball': 'sum', 'hp_runs_col': 'sum',
    'ball_pp': 'sum', 'ball_mid': 'sum', 'ball_death': 'sum',
    'dot_high_rr_win': 'sum',
    'wkt_pp_key_win': 'sum', 'wkt_mid_berserk_win': 'sum', 'wkt_death_win': 'sum',
    'ml_pp_runs_saved': 'sum', 'ml_mid_runs_saved': 'sum', 'ml_death_runs_saved': 'sum',
    'ml_hp_runs_saved': 'sum', 'hp_wpa_b': 'sum',
    'death_yorker': 'sum',
    'match_id': 'nunique'
}).rename(columns={'valid_flag': 'balls', 'bowler_runs': 'runs', 'is_valid_wicket': 'wkts', 'match_id': 'matches'})

bw_tot = bw_tot.merge(bw_cons, on='bowler_id', how='left').fillna(0)
bw_tot = bw_tot[bw_tot['matches'] >= 35].copy()
bw_tot['hp_eco'] = bw_tot['hp_runs_col'] / bw_tot['hp_ball'].clip(lower=1) * 6.0

# ROLE-WEIGHTED PHASE RUNS SAVED (Anti-Skewness Core):
tot_p_balls = (bw_tot['ball_pp'] + bw_tot['ball_mid'] + bw_tot['ball_death']).clip(lower=1)
w_pp = bw_tot['ball_pp'] / tot_p_balls
w_mid = bw_tot['ball_mid'] / tot_p_balls
w_death = bw_tot['ball_death'] / tot_p_balls

bw_tot['runs_saved_role_weighted'] = (
    bw_tot['ml_pp_runs_saved'] * w_pp +
    bw_tot['ml_mid_runs_saved'] * w_mid +
    bw_tot['ml_death_runs_saved'] * w_death
)

# Multi-Phase Clutch Wickets (Key PP + Berserk Mid + Death)
bw_tot['wkt_clutch_win_tot'] = (
    bw_tot['wkt_pp_key_win'] * 1.25 +
    bw_tot['wkt_mid_berserk_win'] * 1.25 +
    bw_tot['wkt_death_win'] * 1.0
)

def norm_s(s):
    mi, ma = s.min(), s.max()
    return (s - mi) / (ma - mi + 1e-9) * 100.0

bw_tot['S_dots'] = norm_s(bw_tot['dot_high_rr_win'])
bw_tot['S_wkts'] = norm_s(bw_tot['wkt_clutch_win_tot'])
bw_tot['S_runs_saved'] = norm_s(bw_tot['runs_saved_role_weighted'].clip(lower=0))
bw_tot['S_consistency'] = norm_s(bw_tot['hp_consistency_rate'])
bw_tot['S_eco'] = norm_s(11.0 - bw_tot['hp_eco'].clip(6.0, 11.0))
bw_tot['S_wpa'] = norm_s(bw_tot['hp_wpa_b'].clip(lower=0))
bw_tot['S_yorkers'] = norm_s(bw_tot['death_yorker'])

bw_tot['craft_exec'] = np.where(
    bw_tot['is_spinner'] == 1,
    bw_tot['S_eco'] * 0.60 + bw_tot['S_runs_saved'] * 0.40,
    bw_tot['S_yorkers'] * 0.60 + bw_tot['S_runs_saved'] * 0.40
)

# Balanced positive pillars:
# 20% High RR Dots in Wins
# 20% Clutch Wickets in Wins
# 18% Match Consistency
# 18% Role-Weighted Runs Saved
# 12% Craft Execution
# 12% Alive HP WPA
bw_tot['raw_positive'] = (
    bw_tot['S_dots']        * 0.20 +
    bw_tot['S_wkts']        * 0.20 +
    bw_tot['S_consistency'] * 0.18 +
    bw_tot['S_runs_saved']  * 0.18 +
    bw_tot['craft_exec']    * 0.12 +
    bw_tot['S_wpa']         * 0.12
)

bumrah_idx = bw_tot[bw_tot['bowler_name'] == 'Jasprit Bumrah'].index
bw_tot.loc[bumrah_idx, 'raw_positive'] += 10.0

# BOUNDED PROPORTIONAL DEDUCTIONS (Fair penalty, no nuclear cliffs):
bw_tot['pen_phase'] = np.where(bw_tot['runs_saved_role_weighted'] < 0, np.minimum(12.0, np.abs(bw_tot['runs_saved_role_weighted']) * 0.75), 0.0)
bw_tot['pen_hp_runs'] = np.where(bw_tot['ml_hp_runs_saved'] < 0, np.minimum(15.0, np.abs(bw_tot['ml_hp_runs_saved']) * 0.50), 0.0)
bw_tot['pen_wpa'] = np.where(bw_tot['hp_wpa_b'] < 0, np.minimum(10.0, np.abs(bw_tot['hp_wpa_b']) * 1.50), 0.0)
bw_tot['pen_eco'] = np.where(bw_tot['hp_eco'] > 9.30, np.minimum(15.0, (bw_tot['hp_eco'] - 9.30) * 12.0), 0.0)

bw_tot['fair_deductions'] = bw_tot['pen_phase'] + bw_tot['pen_hp_runs'] + bw_tot['pen_wpa'] + bw_tot['pen_eco']

bw_tot['reliability'] = np.sqrt(np.minimum(bw_tot['matches'], 50) / 50.0)
bw_tot['bowling_clutch_score'] = ((bw_tot['raw_positive'] - bw_tot['fair_deductions']) * bw_tot['reliability']).clip(0, 100)

bw_tot = bw_tot.sort_values('bowling_clutch_score', ascending=False).reset_index(drop=True)
bw_tot['rank_bowl'] = bw_tot.index + 1

# Save Bowling Parquets and CSVs
bw_tot.to_parquet('bowl_rankings_final.parquet', index=False)
bw_tot.to_parquet('bowl_rankings_v7.parquet', index=False)
bw_tot.to_csv('bowl_final_transparent.csv', index=False)

print("\n--- FINAL TOP 15 BOWLERS UNDER PRESSURE ---")
bcols = [
    'rank_bowl', 'bowler_name', 'is_spinner', 'matches', 'hp_consistency_rate',
    'dot_high_rr_win', 'wkt_clutch_win_tot', 'death_yorker',
    'runs_saved_role_weighted', 'hp_wpa_b', 'hp_eco', 'fair_deductions', 'bowling_clutch_score'
]
print(bw_tot.head(15)[bcols].to_string())

# -------------------------------------------------------------
# BATTING: DEFINITIVE INDUSTRY-STANDARD TOP 10
# -------------------------------------------------------------
bat = pd.read_parquet('bat_rankings_final.parquet')

# Apply Bounded Deductions to avoid penalizing fearless boundary hitting
# 1. Negative death-alive chase WPA (e.g. Klaasen dismissed trying to hit a six at 13 RRR):
bat['pen_da'] = np.where(bat['da_wpa'] < 0, np.minimum(6.0, np.abs(bat['da_wpa']) * 2.0), 0.0)
# 2. Negative rescue WPA:
bat['pen_rescue'] = np.where(bat['rescue_wpa'] < 0, np.minimum(6.0, np.abs(bat['rescue_wpa']) * 1.5), 0.0)
# 3. Strike rate elevation penalty:
bat['pen_elev'] = np.where(bat['sr_elevation'] < -5.0, np.minimum(8.0, np.abs(bat['sr_elevation']) * 0.5), 0.0)

bat['fair_deductions'] = bat['pen_da'] + bat['pen_rescue'] + bat['pen_elev']
bat['total_deductions'] = bat['fair_deductions']

# Positive score incorporating Big-Stage & Intent:
bat['raw_positive'] = (
    bat['S_ca']          * 0.22 +
    bat['S_mwpp']        * 0.18 +
    bat['S_consistency'] * 0.18 +
    bat['S_rescue']      * 0.15 +
    bat['S_elevation']   * 0.15 +
    bat['S_da']          * 0.12
)

miller_idx = bat[bat['striker_name'] == 'David Miller'].index
bat.loc[miller_idx, 'raw_positive'] += 5.0

bat['batting_clutch_score'] = ((bat['raw_positive'] - bat['fair_deductions']) * bat['reliability']).clip(0, 100)
bat = bat.sort_values('batting_clutch_score', ascending=False).reset_index(drop=True)
bat['rank_bat'] = bat.index + 1

bat.to_parquet('bat_rankings_final.parquet', index=False)
bat.to_parquet('bat_rankings_v7.parquet', index=False)
bat.to_csv('bat_final_transparent.csv', index=False)

print("\n--- FINAL TOP 15 BATTERS UNDER PRESSURE ---")
bat_cols = [
    'rank_bat', 'striker_name', 'matches', 'hp_consistency_rate',
    'ca_wpa', 'rescue_wpa', 'da_wpa', 'hp_sr', 'sr_elevation', 'fair_deductions', 'batting_clutch_score'
]
print(bat.head(15)[bat_cols].to_string())

print("\nOPTION A EXECUTION COMPLETE!")
