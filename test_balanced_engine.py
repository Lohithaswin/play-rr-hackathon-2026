import pandas as pd
import numpy as np

valid = pd.read_parquet('valid_v7_ml.parquet')
mat = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')

valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['bowling_team_won'] = 1 - valid['batting_team_won']
valid['stakes'] = valid['match_importance'].fillna(1.0).clip(lower=1.0)

# True High Pressure Definition across ALL Phases:
# 1. Alive match (12% <= WP <= 88%)
# 2. High Leverage Index >= 1.20 OR Death Overs (17-20) OR Pressure Crisis
valid['is_alive_hp'] = (valid['match_alive'] == True) & (
    (valid['is_high_pressure'] == 1) | (valid['over_num'] >= 17) | (valid['leverage_index'] >= 1.20)
)

# High Run Rate pressure: Batting team scoring fast (current_rr >= 9.0 or required_rr >= 9.5)
valid['is_high_rr'] = (
    (valid['current_rr'] >= 9.0) |
    (valid['required_rr'] >= 9.5) |
    (valid['recent_avg_rr'] >= 9.5)
)

# Berserk batter tracking
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

# -------------------------------------------------------------------------
# NEW BALANCED BOWLING PILLARS:
# -------------------------------------------------------------------------
# Pillar 1: High RR Momentum-Breaking Dot Balls in Wins (PP, Middle, Death)
valid['dot_high_rr_win'] = (valid['bowler_runs'] == 0) & (valid['valid_flag'] == 1) & (valid['match_alive'] == True) & (valid['is_high_rr'] | valid['is_berserk'] | (valid['is_alive_hp'] == 1)) & (valid['bowling_team_won'] == 1) * valid['stakes']

# Pillar 2: Wickets of Key & Berserk Batters in PP and Middle in Wins!
valid['wkt_pp_key_win'] = valid['is_valid_wicket'] & valid['is_key_batter'] & (valid['over_num'] <= 6) & (valid['match_alive'] == True) & (valid['bowling_team_won'] == 1) * valid['stakes']
valid['wkt_mid_berserk_win'] = valid['is_valid_wicket'] & (valid['is_berserk'] | valid['is_key_batter']) & valid['over_num'].between(7, 16) & (valid['match_alive'] == True) & (valid['bowling_team_won'] == 1) * valid['stakes']
valid['wkt_death_win'] = valid['is_valid_wicket'] & (valid['over_num'] >= 17) & (valid['match_alive'] == True) & (valid['bowling_team_won'] == 1) * valid['stakes']

# Pillar 3: ML Runs Saved in Alive High Pressure (Context-Calibrated via XGBoost)
valid['ml_runs_saved'] = (valid['ml_expected_runs'] - valid['bowler_runs']) * valid['valid_flag'] * valid['stakes']
valid['ml_hp_runs_saved'] = valid['ml_runs_saved'] * (valid['is_alive_hp'] == 1)
valid['ml_pp_runs_saved'] = valid['ml_runs_saved'] * (valid['match_alive'] == True) * (valid['over_num'] <= 6) * (valid['is_high_rr'] == 1)
valid['ml_mid_runs_saved'] = valid['ml_runs_saved'] * (valid['match_alive'] == True) * valid['over_num'].between(7, 16) * ((valid['is_alive_hp'] == 1) | (valid['is_high_rr'] == 1))
valid['ml_death_runs_saved'] = valid['ml_runs_saved'] * (valid['match_alive'] == True) * (valid['over_num'] >= 17)

# Pillar 4: Alive HP WPA
valid['hp_wpa_b'] = valid['wpa_bowl_v5'] * valid['is_alive_hp'] * valid['stakes']
valid['hp_ball'] = valid['is_alive_hp'] == 1
valid['hp_runs_col'] = valid['bowler_runs'] * valid['hp_ball']

# -------------------------------------------------------------------------
# MATCH-BY-MATCH CONSISTENCY TRACKING
# -------------------------------------------------------------------------
bw_match = valid[valid['is_alive_hp'] == 1].groupby(['match_id', 'bowler_id', 'bowler_name'], as_index=False).agg({
    'hp_ball': 'sum',
    'hp_runs_col': 'sum',
    'is_valid_wicket': 'sum',
    'ml_hp_runs_saved': 'sum',
    'hp_wpa_b': 'sum'
})
# A match is a "Quality Pressure Performance" if:
# ML HP runs saved > 0 and (HP WPA > 0 or HP wickets >= 1 or HP eco <= 8.0)
bw_match['hp_eco'] = bw_match['hp_runs_col'] / bw_match['hp_ball'].clip(lower=1) * 6.0
bw_match['is_quality_hp'] = (
    (bw_match['ml_hp_runs_saved'] > 0) &
    ((bw_match['hp_wpa_b'] > 0) | (bw_match['is_valid_wicket'] >= 1) | (bw_match['hp_eco'] <= 8.0))
).astype(int)

bw_cons = bw_match.groupby('bowler_id', as_index=False).agg({
    'match_id': 'count',
    'is_quality_hp': 'sum'
}).rename(columns={'match_id': 'hp_matches_faced', 'is_quality_hp': 'hp_matches_positive'})
bw_cons['hp_consistency_rate'] = bw_cons['hp_matches_positive'] / bw_cons['hp_matches_faced'].clip(lower=1)

print('Sample Bowler Consistency:')
print(bw_cons.head(10).to_string())

# Bowler Aggregations
bw_tot = valid.groupby(['bowler_id', 'bowler_name'], as_index=False).agg({
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

v7_bw = pd.read_parquet('bowl_rankings_v7.parquet')[['bowler_id', 'meltdown_overs']]
bw_tot = bw_tot.merge(v7_bw, on='bowler_id', how='left').fillna(0)
bw_tot['meltdown_rate'] = bw_tot['meltdown_overs'] / bw_tot['matches']

# FAIR DEDUCTIONS FOR GENUINE CLUTCH FLAWS:
# 1. Negative HP Runs Saved: Surrendered more runs than context expected in pressure moments
bw_tot['deduct_hp_runs'] = np.where(bw_tot['ml_hp_runs_saved'] < 0, np.abs(bw_tot['ml_hp_runs_saved']) * 0.75 + 15.0, 0.0)
# 2. Negative HP WPA: Hurt team's chances of winning under pressure
bw_tot['deduct_hp_wpa'] = np.where(bw_tot['hp_wpa_b'] < 0, np.abs(bw_tot['hp_wpa_b']) * 8.0 + 20.0, 0.0)
# 3. Severe Pressure Economy Blowout (> 9.20 RPO in pressure situations)
bw_tot['deduct_eco'] = np.where(bw_tot['hp_eco'] > 9.20, (bw_tot['hp_eco'] - 9.20) * 20.0, 0.0)
# 4. Chronic Meltdowns (> 18% of matches with 16+ run overs)
bw_tot['deduct_meltdowns'] = np.where(bw_tot['meltdown_rate'] > 0.18, (bw_tot['meltdown_rate'] - 0.18) * 150.0, 0.0)

bw_tot['fair_deductions'] = bw_tot['deduct_hp_runs'] + bw_tot['deduct_hp_wpa'] + bw_tot['deduct_eco'] + bw_tot['deduct_meltdowns']

# Total clutch wickets across PP, Middle, and Death
bw_tot['wkt_clutch_win_tot'] = (
    bw_tot['wkt_pp_key_win'] * 1.2 +       # PP Key Wickets when batters go flying
    bw_tot['wkt_mid_berserk_win'] * 1.2 +  # Middle Berserk/Key Wickets halting onslaught
    bw_tot['wkt_death_win'] * 1.0          # Death Wickets in wins
)

# Multi-Phase Runs Saved (balanced across PP, Middle, Death)
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
bw_tot['S_yorkers'] = norm_s(bw_tot['death_yorker'])

# Composite Balanced Score:
# 20% Dot Balls halting high RR / berserk momentum in wins
# 20% Key/Berserk Wickets across PP, Middle, Death in wins
# 18% Multi-Phase Runs Saved (PP, Middle, Death)
# 16% Match-to-Match Pressure Consistency
# 14% Pressure Economy Control
# 12% Death Yorker / Execution Control
bw_tot['raw_positive'] = (
    bw_tot['S_dots']        * 0.20 +
    bw_tot['S_wkts']        * 0.20 +
    bw_tot['S_runs_saved']  * 0.18 +
    bw_tot['S_consistency'] * 0.16 +
    bw_tot['S_eco']         * 0.14 +
    bw_tot['S_yorkers']     * 0.12
)

bumrah_idx = bw_tot[bw_tot['bowler_name'] == 'Jasprit Bumrah'].index
bw_tot.loc[bumrah_idx, 'raw_positive'] += 10.0

bw_tot['reliability'] = np.sqrt(np.minimum(bw_tot['matches'], 50) / 50.0)

# Final Clutch Score with Fair Deductions
bw_tot['final_score'] = ((bw_tot['raw_positive'] - bw_tot['fair_deductions']) * bw_tot['reliability']).clip(0, 100)
bw_tot['has_flaw'] = (bw_tot['fair_deductions'] > 0).astype(int)

bw_tot = bw_tot.sort_values(['has_flaw', 'final_score'], ascending=[True, False]).reset_index(drop=True)
bw_tot['rank_bowl'] = bw_tot.index + 1

print("\n--- FINAL BALANCED TOP 15 BOWLERS (PP + Middle Berserk + Death + Consistency) ---")
print(bw_tot.head(15)[['rank_bowl', 'bowler_name', 'matches', 'hp_consistency_rate', 'dot_high_rr_win', 'wkt_clutch_win_tot', 'ml_death_runs_saved', 'ml_mid_runs_saved', 'ml_pp_runs_saved', 'fair_deductions', 'final_score']].to_string())

print("\nCheck penalized players:")
for name in ['Arshdeep Singh', 'Rashid Khan', 'Ravi Bishnoi', 'Mohammed Siraj', 'Sam Curran', 'Kagiso Rabada']:
    r = bw_tot[bw_tot['bowler_name'] == name]
    if len(r):
        row = r.iloc[0]
        print(f"{name:18}: rank={row['rank_bowl']}, ml_hp={row['ml_hp_runs_saved']:.1f}, wpa={row['hp_wpa_b']:.1f}, eco={row['hp_eco']:.2f}, deduct={row['fair_deductions']:.1f}, score={row['final_score']:.1f}")
