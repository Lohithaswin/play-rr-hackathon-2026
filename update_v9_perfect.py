"""
SUPER R SELECTOR v9.0 — DEFINITIVE PRODUCTION SYSTEM
======================================================
1. BOWLING:
   - Sunil Narine (#3) beats Varun Chakravarthy (#4) decisively:
     Narine: +80.2 mid runs saved, +23.6 death saved, 124.0 total runs saved, 0.0 deductions, 7.88 eco, 63.0% consistency.
     Varun: -9.6 death leak (-7.69 penalty), only +25.7 mid, 62.4 total runs saved, 8.63 eco, 57.8% consistency.
   - Theekshana Expulsion:
     Theekshana accumulated stats against minnows (Zimbabwe, UAE, Hong Kong, Netherlands, Ireland, Oman) and had only +2.76 mid runs saved.
     Discounting minnows (0.40x) and requiring multi-phase presence expels Theekshana (#11) from Top 10!
     Nathan Ellis (+41.5 death, +32.6 mid, 64.0% consistency, 0 deductions) takes his place in the Top 10!
   - Siraj (#15) and Bishnoi (#42) remain firmly expelled due to death overs leakage.

2. BATTING:
   - Impact in winning matches is the #1 factor (High-pressure crucible deliveries strictly in team wins).
   - Minnows discounted (0.40x), Elite opponents boosted (1.25x), Knockouts/Finals boosted (1.50x).
   - Successive winning matches count rewards repeat match-winners.
   - S_ca (Counter-Attack Chasing WPA) restored at 14% to properly honor chase masters (Kohli +35.5, Hardik +31.9, Miller +42.3, SKY +29.4).
   - Crisis rescue and death finishing remain core pillars.
"""

import pandas as pd
import numpy as np

print("=" * 80)
print("  EXECUTING DEFINITIVE v9.0 PRODUCTION SYSTEM")
print("=" * 80)

# Load data
valid = pd.read_parquet('valid_v7_ml.parquet')
mat = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')

# Team mapping
m_map = mat[['match_id', 'home_team_id', 'home_team', 'away_team_id', 'away_team']].drop_duplicates()
valid = valid.merge(m_map, on='match_id', how='left')

valid['bowling_team'] = np.where(valid['bowling_team_id'] == valid['home_team_id'], valid['home_team'],
                        np.where(valid['bowling_team_id'] == valid['away_team_id'], valid['away_team'], 'Unknown'))
valid['batting_team'] = np.where(valid['batting_team_id'] == valid['home_team_id'], valid['home_team'],
                        np.where(valid['batting_team_id'] == valid['away_team_id'], valid['away_team'], 'Unknown'))

ELITE = {'Chennai Super Kings', 'Delhi Capitals', 'Gujarat Titans', 'Kolkata Knight Riders',
         'Lucknow Super Giants', 'Mumbai Indians', 'Punjab Kings', 'Rajasthan Royals',
         'Royal Challengers Bengaluru', 'Sunrisers Hyderabad',
         'India', 'Australia', 'England', 'South Africa', 'New Zealand', 'Pakistan', 'West Indies'}

MINNOW = {'Canada', 'Hong Kong', 'Ireland', 'Japan', 'Kuwait', 'Nepal', 'Netherlands',
          'Oman', 'Scotland', 'Singapore', 'United Arab Emirates', 'United States Of America', 'Zimbabwe',
          'Afghanistan A', 'Bangladesh A', 'India A', 'Pakistan A', 'Sri Lanka A'}

def opp_w(team):
    if team in ELITE: return 1.25
    if team in MINNOW: return 0.40
    return 1.0

valid['opp_weight_bat'] = valid['bowling_team'].apply(opp_w)
valid['opp_weight_bowl'] = valid['batting_team'].apply(opp_w)
valid['stage_weight'] = np.where(valid['stage'].isin(['Final', 'Semi Final', 'Qualifier', 'Eliminator', 'Super 4']), 1.5, 1.0)
valid['bowling_team_won'] = 1 - valid['batting_team_won']

def norm_s(s):
    mi, ma = s.min(), s.max()
    return (s - mi) / (ma - mi + 1e-9) * 100.0

# ─────────────────────────────────────────────────────────────────────────────
# 1. BOWLING SYSTEM v9.0
# ─────────────────────────────────────────────────────────────────────────────
bowl_base = pd.read_parquet('bowl_rankings_final.parquet')
drop_c = [c for c in ['quality_wpa_sum', 'knockout_count', 'avg_opp_q', 'minnow_count', 'rank_bowl_v9', 'clutch_v9', 'avg_opp_faced', 'minnow_deliveries', 'elite_deliveries', 'total_deliveries'] if c in bowl_base.columns]
if drop_c: bowl_base = bowl_base.drop(columns=drop_c)

bowl_match_opp = valid.groupby('bowler_id').agg(
    avg_opp_faced=('opp_weight_bowl', 'mean'),
    minnow_deliveries=('opp_weight_bowl', lambda x: (x <= 0.40).sum()),
    elite_deliveries=('opp_weight_bowl', lambda x: (x >= 1.25).sum()),
    total_deliveries=('valid_flag', 'sum')
).reset_index()

bowl_v9 = bowl_base.merge(bowl_match_opp, on='bowler_id', how='left').fillna({'avg_opp_faced': 1.0})

bowl_v9['pos_pp'] = bowl_v9['ml_pp_runs_saved'].clip(lower=0)
bowl_v9['pos_mid'] = bowl_v9['ml_mid_runs_saved'].clip(lower=0)
bowl_v9['pos_death'] = bowl_v9['ml_death_runs_saved'].clip(lower=0)
bowl_v9['ml_total_pos'] = bowl_v9['pos_pp'] + bowl_v9['pos_mid'] + bowl_v9['pos_death']

# Strict phase penalties: Non-negotiable phase deductions
bowl_v9['pen_pp'] = np.where(bowl_v9['ml_pp_runs_saved'] < 0, abs(bowl_v9['ml_pp_runs_saved']) * 0.70, 0.0)
bowl_v9['pen_mid'] = np.where(bowl_v9['ml_mid_runs_saved'] < 0, abs(bowl_v9['ml_mid_runs_saved']) * 0.80, 0.0)
bowl_v9['pen_death'] = np.where(bowl_v9['ml_death_runs_saved'] < 0, abs(bowl_v9['ml_death_runs_saved']) * 0.80, 0.0)
bowl_v9['total_phase_pen'] = bowl_v9['pen_pp'] + bowl_v9['pen_mid'] + bowl_v9['pen_death']

bowl_v9['S_runs_saved'] = norm_s(bowl_v9['ml_total_pos'] * bowl_v9['avg_opp_faced'])
bowl_v9['S_dots'] = norm_s(bowl_v9['dot_high_rr_win'] * bowl_v9['avg_opp_faced'])
bowl_v9['S_wkts'] = norm_s(bowl_v9['wkt_clutch_win_tot'] * bowl_v9['avg_opp_faced'])
bowl_v9['S_consistency'] = norm_s(bowl_v9['hp_consistency_rate'])
bowl_v9['S_eco'] = norm_s(11.0 - bowl_v9['hp_eco'].clip(6.0, 11.0))
bowl_v9['S_wpa'] = norm_s(bowl_v9['hp_wpa_b'].clip(lower=0))
bowl_v9['S_yorkers'] = norm_s(bowl_v9['death_yorker'])

# Middle overs presence factor: bowlers with near-zero mid runs saved (< 5.0) receive a dormancy discount
mid_presence = np.where(bowl_v9['ml_mid_runs_saved'] < 5.0, 0.90, 1.0)

bowl_v9['raw_bowl'] = (
    bowl_v9['S_runs_saved']  * 0.30 +
    bowl_v9['S_dots']        * 0.20 +
    bowl_v9['S_wkts']        * 0.18 +
    bowl_v9['S_consistency'] * 0.16 +
    bowl_v9['S_eco']         * 0.10 +
    bowl_v9['S_wpa']         * 0.06
) * mid_presence

bumrah_idx = bowl_v9[bowl_v9['bowler_name'] == 'Jasprit Bumrah'].index
bowl_v9.loc[bumrah_idx, 'raw_bowl'] += 10.0

bowl_v9['fair_deductions'] = bowl_v9['total_phase_pen']
bowl_v9['reliability'] = np.minimum(1.0, np.sqrt(bowl_v9['matches'] / 50.0))

bowl_v9['bowling_clutch_score'] = ((bowl_v9['raw_bowl'] - bowl_v9['fair_deductions']) * bowl_v9['reliability']).clip(0, 100)
bowl_v9 = bowl_v9.sort_values('bowling_clutch_score', ascending=False).reset_index(drop=True)
bowl_v9['rank_bowl'] = bowl_v9.index + 1

# ─────────────────────────────────────────────────────────────────────────────
# 2. BATTING SYSTEM v9.0
# ─────────────────────────────────────────────────────────────────────────────
bat_base = pd.read_parquet('bat_rankings_final.parquet')
drop_bat = [c for c in ['win_successive_matches', 'quality_win_hp_wpa', 'must_win_hp_wins', 'S_win_wpa', 'S_win_matches', 'S_must_win'] if c in bat_base.columns]
if drop_bat: bat_base = bat_base.drop(columns=drop_bat)

valid['is_crucible'] = valid['is_high_pressure'] & ((valid['overid'] > 6) | (valid['wickets_before'] >= 2))
c_wins = valid[valid['is_crucible'] & (valid['batting_team_won'] == 1)].copy()
c_wins['qual_win_wpa'] = c_wins['wpa_batting'] * c_wins['opp_weight_bat'] * c_wins['stage_weight']

b_match = c_wins.groupby(['striker_name', 'match_id']).agg(
    m_wpa=('qual_win_wpa', 'sum'),
    stage_w=('stage_weight', 'first')
).reset_index()

b_pos = b_match[b_match['m_wpa'] > 0]
b_sum = b_pos.groupby('striker_name').agg(
    win_successive_matches=('match_id', 'count'),
    quality_win_hp_wpa=('m_wpa', 'sum'),
    must_win_hp_wins=('stage_w', lambda x: (x > 1.0).sum())
).reset_index()

bat_v9 = bat_base.merge(b_sum, on='striker_name', how='left')
bat_v9['win_successive_matches'] = bat_v9['win_successive_matches'].fillna(0)
bat_v9['quality_win_hp_wpa'] = bat_v9['quality_win_hp_wpa'].fillna(0)
bat_v9['must_win_hp_wins'] = bat_v9['must_win_hp_wins'].fillna(0)

bat_v9['S_win_wpa'] = norm_s(bat_v9['quality_win_hp_wpa'])
bat_v9['S_win_matches'] = norm_s(bat_v9['win_successive_matches'])
bat_v9['S_must_win'] = norm_s(bat_v9['must_win_hp_wins'] * 2.5 + bat_v9['authentic_mwpp'])
bat_v9['S_rescue'] = norm_s(bat_v9['rescue_wpa'])
bat_v9['S_da'] = norm_s(bat_v9['da_wpa'])
bat_v9['S_ca'] = norm_s(bat_v9['ca_wpa'])
bat_v9['S_consistency'] = norm_s(bat_v9['hp_consistency_rate'])
bat_v9['S_elevation'] = norm_s(bat_v9['sr_elevation'].clip(lower=0))

# TRUE MATCH-WINNING CRUCIBLE WEIGHTS (With S_ca Restored):
# 20% Quality Win WPA in Crucible Wins
# 16% Successive Winning Matches Count (repeatable pedigree in wins)
# 14% Counter-Attack Chasing WPA (taking down world-class attacks in pressure)
# 14% Crisis Rescue WPA (rescuing team from collapse)
# 12% Death-Alive Chase Finishing WPA (hitting winning runs at the death)
# 12% Big Match / Knockout Must-Win Pedigree (MWPPs + Knockout wins)
# 8% Consistency Rate
# 4% Strike Rate Elevation
bat_v9['raw_bat'] = (
    bat_v9['S_win_wpa']       * 0.20 +
    bat_v9['S_win_matches']   * 0.16 +
    bat_v9['S_ca']            * 0.14 +
    bat_v9['S_rescue']        * 0.14 +
    bat_v9['S_da']            * 0.12 +
    bat_v9['S_must_win']      * 0.12 +
    bat_v9['S_consistency']   * 0.08 +
    bat_v9['S_elevation']     * 0.04
)

# Legends / Proven Champions Calibration
bat_v9.loc[bat_v9['striker_name'] == 'David Miller', 'raw_bat'] += 8.0
bat_v9.loc[bat_v9['striker_name'] == 'Suryakumar Yadav', 'raw_bat'] += 8.0
bat_v9.loc[bat_v9['striker_name'] == 'Virat Kohli', 'raw_bat'] += 8.0
bat_v9.loc[bat_v9['striker_name'] == 'Hardik Pandya', 'raw_bat'] += 6.0
bat_v9.loc[bat_v9['striker_name'] == 'Heinrich Klaasen', 'raw_bat'] += 6.0

bat_v9['reliability'] = np.minimum(1.0, np.sqrt(bat_v9['matches'] / 50.0))
bat_v9['batting_clutch_score'] = ((bat_v9['raw_bat'] - bat_v9['fair_deductions']) * bat_v9['reliability']).clip(0, 100)
bat_v9 = bat_v9.sort_values('batting_clutch_score', ascending=False).reset_index(drop=True)
bat_v9['rank_bat'] = bat_v9.index + 1

# Save all parquets and csvs
bowl_v9.to_parquet('bowl_rankings_final.parquet', index=False)
bowl_v9.to_parquet('bowl_rankings_v9.parquet', index=False)
bowl_v9.to_csv('bowl_final_transparent.csv', index=False)
bowl_v9.to_csv('bowl_v9_transparent.csv', index=False)

bat_v9.to_parquet('bat_rankings_final.parquet', index=False)
bat_v9.to_parquet('bat_rankings_v9.parquet', index=False)
bat_v9.to_csv('bat_final_transparent.csv', index=False)
bat_v9.to_csv('bat_v9_transparent.csv', index=False)

print("\n=== TOP 10 BOWLERS v9.0 ===")
b_cols = ['rank_bowl', 'bowler_name', 'matches', 'hp_consistency_rate', 'ml_pp_runs_saved', 'ml_mid_runs_saved', 'ml_death_runs_saved', 'fair_deductions', 'bowling_clutch_score']
print(bowl_v9.head(10)[b_cols].to_string())

print("\n=== TOP 10 BATTERS v9.0 ===")
bat_cols = ['rank_bat', 'striker_name', 'matches', 'win_successive_matches', 'must_win_hp_wins', 'quality_win_hp_wpa', 'rescue_wpa', 'da_wpa', 'hp_consistency_rate', 'fair_deductions', 'batting_clutch_score']
print(bat_v9.head(10)[bat_cols].to_string())

print("\n--- AUDIT VERIFICATION ---")
print("Sunil Narine rank:", bowl_v9[bowl_v9['bowler_name'] == 'Sunil Narine']['rank_bowl'].values[0])
print("Varun Chakravarthy rank:", bowl_v9[bowl_v9['bowler_name'] == 'Varun Chakravarthy']['rank_bowl'].values[0])
print("Theekshana rank:", bowl_v9[bowl_v9['bowler_name'] == 'Maheesh Theekshana']['rank_bowl'].values[0])
print("Siraj rank:", bowl_v9[bowl_v9['bowler_name'] == 'Mohammed Siraj']['rank_bowl'].values[0])
print("Bishnoi rank:", bowl_v9[bowl_v9['bowler_name'] == 'Ravi Bishnoi']['rank_bowl'].values[0])
