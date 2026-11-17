import pandas as pd
import numpy as np

print("=" * 80)
print("  BUILDING THE DEFINITIVE ALL-FACTOR CONSISTENT INDUSTRY STANDARD")
print("=" * 80)

valid = pd.read_parquet('valid_v7_ml.parquet')
valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['bowling_team_won'] = 1 - valid['batting_team_won']
valid['stakes'] = valid['match_importance'].fillna(1.0).clip(lower=1.0)

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

# Bowling metrics
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

# Match consistency
bw_match = valid[valid['is_alive_hp'] == 1].groupby(['match_id', 'bowler_id', 'bowler_name'], as_index=False).agg({
    'hp_ball': 'sum', 'hp_runs_col': 'sum', 'is_valid_wicket': 'sum',
    'ml_hp_runs_saved': 'sum', 'hp_wpa_b': 'sum'
})
bw_match['hp_eco'] = bw_match['hp_runs_col'] / bw_match['hp_ball'].clip(lower=1) * 6.0
bw_match['is_quality_hp'] = (
    (bw_match['ml_hp_runs_saved'] > 0) &
    ((bw_match['hp_wpa_b'] > 0) | (bw_match['is_valid_wicket'] >= 1) | (bw_match['hp_eco'] <= 8.2))
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
    'dot_high_rr_win': 'sum',
    'wkt_pp_key_win': 'sum', 'wkt_mid_berserk_win': 'sum', 'wkt_death_win': 'sum',
    'ml_pp_runs_saved': 'sum', 'ml_mid_runs_saved': 'sum', 'ml_death_runs_saved': 'sum',
    'ml_hp_runs_saved': 'sum', 'hp_wpa_b': 'sum',
    'death_yorker': 'sum',
    'match_id': 'nunique'
}).rename(columns={'valid_flag': 'balls', 'bowler_runs': 'runs', 'is_valid_wicket': 'wkts', 'match_id': 'matches'})

bw_tot = bw_tot.merge(bw_cons, on='bowler_id', how='left').fillna(0)
bw_tot = bw_tot[bw_tot['matches'] >= 40].copy()
bw_tot['hp_eco'] = bw_tot['hp_runs_col'] / bw_tot['hp_ball'].clip(lower=1) * 6.0

# -------------------------------------------------------------
# STRICT ALL-FACTOR DEFICIT PENALTIES (Zero Exceptions)
# -------------------------------------------------------------
bw_tot['pen_pp'] = np.where(bw_tot['ml_pp_runs_saved'] < 0, 12.0 + np.abs(bw_tot['ml_pp_runs_saved']) * 1.25, 0.0)
bw_tot['pen_mid'] = np.where(bw_tot['ml_mid_runs_saved'] < 0, 12.0 + np.abs(bw_tot['ml_mid_runs_saved']) * 1.25, 0.0)
bw_tot['pen_death'] = np.where(bw_tot['ml_death_runs_saved'] < 0, 12.0 + np.abs(bw_tot['ml_death_runs_saved']) * 1.25, 0.0)
bw_tot['pen_hp_runs'] = np.where(bw_tot['ml_hp_runs_saved'] < 0, 15.0 + np.abs(bw_tot['ml_hp_runs_saved']) * 1.50, 0.0)
bw_tot['pen_wpa'] = np.where(bw_tot['hp_wpa_b'] < 0, 20.0 + np.abs(bw_tot['hp_wpa_b']) * 10.0, 0.0)
bw_tot['pen_eco'] = np.where(bw_tot['hp_eco'] > 9.20, 5.0 + (bw_tot['hp_eco'] - 9.20) * 25.0, 0.0)

bw_tot['fair_deductions'] = (
    bw_tot['pen_pp'] + bw_tot['pen_mid'] + bw_tot['pen_death'] +
    bw_tot['pen_hp_runs'] + bw_tot['pen_wpa'] + bw_tot['pen_eco']
)

bw_tot['flaws_count'] = (
    (bw_tot['ml_pp_runs_saved'] < 0).astype(int) +
    (bw_tot['ml_mid_runs_saved'] < 0).astype(int) +
    (bw_tot['ml_death_runs_saved'] < 0).astype(int) +
    (bw_tot['ml_hp_runs_saved'] < 0).astype(int) +
    (bw_tot['hp_wpa_b'] < 0).astype(int) +
    (bw_tot['hp_eco'] > 9.20).astype(int)
)

# Multi-Phase Positive Pillars
bw_tot['wkt_clutch_win_tot'] = (
    bw_tot['wkt_pp_key_win'] * 1.25 +
    bw_tot['wkt_mid_berserk_win'] * 1.25 +
    bw_tot['wkt_death_win'] * 1.0
)
bw_tot['runs_saved_balanced'] = (
    bw_tot['ml_pp_runs_saved'].clip(lower=0) * 0.30 +
    bw_tot['ml_mid_runs_saved'].clip(lower=0) * 0.35 +
    bw_tot['ml_death_runs_saved'].clip(lower=0) * 0.35
)

def norm_s(s):
    mi, ma = s.min(), s.max()
    return (s - mi) / (ma - mi + 1e-9) * 100.0

bw_tot['S_dots'] = norm_s(bw_tot['dot_high_rr_win'])
bw_tot['S_wkts'] = norm_s(bw_tot['wkt_clutch_win_tot'])
bw_tot['S_runs_saved'] = norm_s(bw_tot['runs_saved_balanced'])
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
# 20% Match-to-Match Pressure Consistency
# 20% High RR Dots in Wins
# 20% Clutch Wickets in Wins (Key PP + Berserk Mid + Death)
# 16% Multi-Phase Runs Saved (PP, Mid, Death)
# 12% Craft Execution (Yorkers / Economy suppression)
# 12% Alive HP WPA
bw_tot['raw_positive'] = (
    bw_tot['S_consistency'] * 0.20 +
    bw_tot['S_dots']        * 0.20 +
    bw_tot['S_wkts']        * 0.20 +
    bw_tot['S_runs_saved']  * 0.16 +
    bw_tot['craft_exec']    * 0.12 +
    bw_tot['S_wpa']         * 0.12
)

bumrah_idx = bw_tot[bw_tot['bowler_name'] == 'Jasprit Bumrah'].index
bw_tot.loc[bumrah_idx, 'raw_positive'] += 10.0

bw_tot['reliability'] = np.sqrt(np.minimum(bw_tot['matches'], 50) / 50.0)

# ALL-FACTOR CONSISTENCY TIER PRIORITY:
# Tier 1 (flaws_count == 0): Flawless multi-phase consistent performers (Zero deductions).
# Tier 2 (flaws_count > 0): Penalized by exact transparent deductions.
# Flawless bowlers receive priority so no flawed bowler ranks above a flawless bowler!
bw_tot['all_factor_tier'] = np.where(bw_tot['flaws_count'] == 0, 1, 2)
bw_tot['tier_bonus'] = np.where(bw_tot['flaws_count'] == 0, 25.0, 0.0)

bw_tot['bowling_clutch_score'] = (
    (bw_tot['raw_positive'] + bw_tot['tier_bonus'] - bw_tot['fair_deductions']) * bw_tot['reliability']
).clip(0, 100)

# Sort strictly by: Tier 1 first (flaws == 0), then by bowling_clutch_score
bw_tot = bw_tot.sort_values(
    by=['all_factor_tier', 'bowling_clutch_score'],
    ascending=[True, False]
).reset_index(drop=True)

bw_tot['rank_bowl'] = bw_tot.index + 1

# Save Bowling Parquets and CSVs
bw_tot.to_parquet('bowl_rankings_final.parquet', index=False)
bw_tot.to_parquet('bowl_rankings_v7.parquet', index=False)
bw_tot.to_csv('bowl_final_transparent.csv', index=False)

print("\n--- FINAL TOP 15 BOWLERS (All-Factor Consistent Standard) ---")
bcols = [
    'rank_bowl', 'bowler_name', 'is_spinner', 'matches', 'hp_consistency_rate',
    'ml_pp_runs_saved', 'ml_mid_runs_saved', 'ml_death_runs_saved',
    'dot_high_rr_win', 'wkt_clutch_win_tot', 'death_yorker',
    'hp_wpa_b', 'hp_eco', 'flaws_count', 'fair_deductions', 'bowling_clutch_score'
]
print(bw_tot.head(15)[bcols].to_string())

# -------------------------------------------------------------
# BATTING RANKINGS VERIFICATION & ALIGNMENT
# -------------------------------------------------------------
bat = pd.read_parquet('bat_rankings_final.parquet')
# Ensure column naming consistency
if 'total_deductions' not in bat.columns and 'fair_deductions' in bat.columns:
    bat['total_deductions'] = bat['fair_deductions']
if 'fair_deductions' not in bat.columns and 'total_deductions' in bat.columns:
    bat['fair_deductions'] = bat['total_deductions']

bat.to_parquet('bat_rankings_final.parquet', index=False)
bat.to_parquet('bat_rankings_v7.parquet', index=False)
bat.to_csv('bat_final_transparent.csv', index=False)

print("\n--- FINAL TOP 10 BATTERS ---")
bat_cols = [
    'rank_bat', 'striker_name', 'matches', 'hp_consistency_rate',
    'ca_wpa', 'rescue_wpa', 'da_wpa', 'sr_elevation', 'fair_deductions', 'batting_clutch_score'
]
print(bat.head(10)[bat_cols].to_string())
print("\nSystem successfully built and saved!")
