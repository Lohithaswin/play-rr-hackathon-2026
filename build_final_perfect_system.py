import pandas as pd
import numpy as np

print("=" * 80)
print("  SUPER R SELECTOR FINAL — INDUSTRY-STANDARD MULTI-PHASE PRESSURE ENGINE")
print("  (Multi-Phase Balance: PP + Middle Berserk + Death, High RR Dots, Consistency Pillar, Fair Deductions)")
print("=" * 80)

valid = pd.read_parquet('valid_v7_ml.parquet')
mat = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')

valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['bowling_team_won'] = 1 - valid['batting_team_won']
valid['stakes'] = valid['match_importance'].fillna(1.0).clip(lower=1.0)

# True High Pressure Definition across ALL Phases:
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

def norm_s(s):
    mi, ma = s.min(), s.max()
    return (s - mi) / (ma - mi + 1e-9) * 100.0

# -------------------------------------------------------------------------
# 1. BATTING ENGINE
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

# Batting match-by-match consistency
bat_m_cons = valid[valid['is_alive_hp'] == 1].groupby(['match_id', 'striker_id', 'striker_name'], as_index=False).agg({
    'hp_runs_col': 'sum', 'hp_balls_col': 'sum', 'hp_wpa_col': 'sum'
}).rename(columns={'hp_runs_col':'hp_runs', 'hp_balls_col':'hp_balls', 'hp_wpa_col':'hp_wpa'})
bat_m_cons['hp_sr'] = bat_m_cons['hp_runs'] / bat_m_cons['hp_balls'].clip(lower=1) * 100.0
bat_m_cons['is_positive_hp'] = (
    (bat_m_cons['hp_wpa'] > 0) |
    ((bat_m_cons['hp_runs'] >= 15) & (bat_m_cons['hp_sr'] >= 135.0))
).astype(int)
bat_cons = bat_m_cons.groupby(['striker_id', 'striker_name'], as_index=False).agg({
    'match_id': 'count', 'is_positive_hp': 'sum'
}).rename(columns={'match_id': 'hp_matches_faced', 'is_positive_hp': 'hp_matches_positive'})
bat_cons['hp_consistency_rate'] = bat_cons['hp_matches_positive'] / bat_cons['hp_matches_faced'].clip(lower=1)

p_bat = bat_m.groupby(['striker_id', 'striker_name'], as_index=False).agg({
    'is_authentic_hp': 'sum', 'is_comeback_knock': 'sum',
    'hp_runs': 'sum', 'hp_balls': 'sum', 'hp_wpa': 'sum',
    'total_runs': 'sum', 'total_balls': 'sum',
    'da_wpa': 'sum', 'ca_wpa': 'sum', 'rescue_wpa': 'sum',
    'match_id': 'count'
}).rename(columns={'is_authentic_hp': 'authentic_mwpp', 'is_comeback_knock': 'comeback_knocks', 'match_id': 'matches'})

p_bat = p_bat.merge(bat_cons[['striker_id', 'hp_consistency_rate', 'hp_matches_faced']], on='striker_id', how='left').fillna(0)
p_bat = p_bat[p_bat['matches'] >= 45].copy()
p_bat['total_sr'] = p_bat['total_runs'] / p_bat['total_balls'].clip(lower=1) * 100.0
p_bat['hp_sr'] = p_bat['hp_runs'] / p_bat['hp_balls'].clip(lower=1) * 100.0
p_bat['sr_elevation'] = p_bat['hp_sr'] - p_bat['total_sr']

# FAIR NEGATIVE DEDUCTIONS (BATTING):
p_bat['pen_rescue'] = np.where(p_bat['rescue_wpa'] < 0, 15.0 + np.abs(p_bat['rescue_wpa']) * 10.0, 0.0)
p_bat['pen_da'] = np.where(p_bat['da_wpa'] < 0, 15.0 + np.abs(p_bat['da_wpa']) * 10.0, 0.0)
p_bat['pen_ca'] = np.where(p_bat['ca_wpa'] < 0, 15.0 + np.abs(p_bat['ca_wpa']) * 10.0, 0.0)
p_bat['pen_elev'] = np.where(p_bat['sr_elevation'] < 0, 10.0 + np.abs(p_bat['sr_elevation']) * 0.50, 0.0)
p_bat['pen_hp_wpa'] = np.where(p_bat['hp_wpa'] < 0, 20.0 + np.abs(p_bat['hp_wpa']) * 10.0, 0.0)

p_bat['fair_deductions'] = (
    p_bat['pen_rescue'] + p_bat['pen_da'] + p_bat['pen_ca'] +
    p_bat['pen_elev'] + p_bat['pen_hp_wpa']
)

p_bat['S_ca'] = norm_s(p_bat['ca_wpa'].clip(lower=0))
p_bat['S_mwpp'] = norm_s(p_bat['authentic_mwpp'])
p_bat['S_da'] = norm_s(p_bat['da_wpa'].clip(lower=0))
p_bat['S_rescue'] = norm_s(p_bat['rescue_wpa'].clip(lower=0))
p_bat['S_comeback'] = norm_s(p_bat['comeback_knocks'])
p_bat['S_consistency'] = norm_s(p_bat['hp_consistency_rate'])
p_bat['S_elevation'] = norm_s(p_bat['sr_elevation'].clip(lower=0))

p_bat['reliability'] = np.sqrt(np.minimum(p_bat['matches'], 80) / 80.0)

p_bat['raw_positive'] = (
    p_bat['S_ca']          * 0.20 + # 20% Counter-Attack WPA
    p_bat['S_mwpp']        * 0.16 + # 16% Authentic MWPP Volume
    p_bat['S_consistency'] * 0.16 + # 16% Match-to-Match Pressure Consistency
    p_bat['S_da']          * 0.14 + # 14% Death-Alive Chase Finishing
    p_bat['S_rescue']      * 0.13 + # 13% Post-Collapse Rescue
    p_bat['S_elevation']   * 0.11 + # 11% SR Elevation under Pressure
    p_bat['S_comeback']    * 0.10   # 10% Comeback Knocks in Wins
)

p_bat['batting_clutch_score'] = ((p_bat['raw_positive'] - p_bat['fair_deductions']) * p_bat['reliability']).clip(0, 100)
p_bat['has_flaw'] = (p_bat['fair_deductions'] > 0).astype(int)
p_bat = p_bat.sort_values(['has_flaw', 'batting_clutch_score'], ascending=[True, False]).reset_index(drop=True)
p_bat['rank_bat'] = p_bat.index + 1

# Aliases
p_bat['wpa_v5'] = p_bat['hp_wpa']
p_bat['mwpp_v7'] = p_bat['authentic_mwpp']
p_bat['runs'] = p_bat['total_runs']
p_bat['total_penalties'] = p_bat['fair_deductions']
p_bat['seasons'] = "2022-2026"

p_bat.to_parquet('bat_rankings_final.parquet', index=False)
p_bat.to_csv('bat_final_transparent.csv', index=False)
p_bat.to_parquet('bat_rankings_v15.parquet', index=False)
p_bat.to_parquet('bat_rankings_v7.parquet', index=False)

bat_m = bat_m.merge(mat[['match_id', 'home_team', 'away_team', 'match_date', 'stage', 'result', 'man_of_the_match']], on='match_id', how='left')
bat_hp_logs = bat_m[bat_m['is_authentic_hp'] == 1].sort_values('hp_wpa', ascending=False).reset_index(drop=True)
bat_hp_logs.to_parquet('bat_hp_match_logs.parquet', index=False)
bat_hp_logs.to_csv('bat_hp_match_logs.csv', index=False)


# -------------------------------------------------------------------------
# 2. BOWLING ENGINE (MULTI-PHASE + HIGH RR DOTS + PP/MID WKTS + CONSISTENCY)
# -------------------------------------------------------------------------
# Dot balls halting high RR / berserk momentum in wins
valid['dot_high_rr_win'] = (valid['bowler_runs'] == 0) & (valid['valid_flag'] == 1) & (valid['match_alive'] == True) & (valid['is_high_rr'] | valid['is_berserk'] | (valid['is_alive_hp'] == 1)) & (valid['bowling_team_won'] == 1) * valid['stakes']

# Wickets in PP & Middle in wins
valid['wkt_pp_key_win'] = valid['is_valid_wicket'] & valid['is_key_batter'] & (valid['over_num'] <= 6) & (valid['match_alive'] == True) & (valid['bowling_team_won'] == 1) * valid['stakes']
valid['wkt_mid_berserk_win'] = valid['is_valid_wicket'] & (valid['is_berserk'] | valid['is_key_batter']) & valid['over_num'].between(7, 16) & (valid['match_alive'] == True) & (valid['bowling_team_won'] == 1) * valid['stakes']
valid['wkt_death_win'] = valid['is_valid_wicket'] & (valid['over_num'] >= 17) & (valid['match_alive'] == True) & (valid['bowling_team_won'] == 1) * valid['stakes']

# ML Runs saved by phase
valid['ml_runs_saved'] = (valid['ml_expected_runs'] - valid['bowler_runs']) * valid['valid_flag'] * valid['stakes']
valid['ml_hp_runs_saved'] = valid['ml_runs_saved'] * (valid['is_alive_hp'] == 1)
valid['ml_pp_runs_saved'] = valid['ml_runs_saved'] * (valid['match_alive'] == True) * (valid['over_num'] <= 6) * (valid['is_high_rr'] == 1)
valid['ml_mid_runs_saved'] = valid['ml_runs_saved'] * (valid['match_alive'] == True) * valid['over_num'].between(7, 16) * ((valid['is_alive_hp'] == 1) | (valid['is_high_rr'] == 1))
valid['ml_death_runs_saved'] = valid['ml_runs_saved'] * (valid['match_alive'] == True) * (valid['over_num'] >= 17)

valid['hp_wpa_b'] = valid['wpa_bowl_v5'] * valid['is_alive_hp'] * valid['stakes']
valid['hp_ball'] = valid['is_alive_hp'] == 1
valid['hp_runs_col'] = valid['bowler_runs'] * valid['hp_ball']

# Bowler Match-to-Match Consistency
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

v7_bw = pd.read_parquet('bowl_rankings_v7.parquet')[['bowler_id', 'meltdown_overs']]
bw_tot = bw_tot.merge(v7_bw, on='bowler_id', how='left').fillna(0)
bw_tot['meltdown_rate'] = bw_tot['meltdown_overs'] / bw_tot['matches']

# FAIR DEDUCTIONS FOR GENUINE NEGATIVE VALUES:
bw_tot['deduct_hp_runs'] = np.where(bw_tot['ml_hp_runs_saved'] < 0, np.abs(bw_tot['ml_hp_runs_saved']) * 0.80 + 15.0, 0.0)
bw_tot['deduct_hp_wpa'] = np.where(bw_tot['hp_wpa_b'] < 0, np.abs(bw_tot['hp_wpa_b']) * 8.0 + 20.0, 0.0)
bw_tot['deduct_eco'] = np.where(bw_tot['hp_eco'] > 9.30, (bw_tot['hp_eco'] - 9.30) * 20.0, 0.0)
bw_tot['fair_deductions'] = bw_tot['deduct_hp_runs'] + bw_tot['deduct_hp_wpa'] + bw_tot['deduct_eco']

# Balanced Wickets in valid: PP key wickets + Middle berserk wickets + Death wickets
valid['wkt_clutch_win_tot'] = (
    valid['wkt_pp_key_win'] * 1.25 +
    valid['wkt_mid_berserk_win'] * 1.25 +
    valid['wkt_death_win'] * 1.0
)
bw_tot['wkt_clutch_win_tot'] = (
    bw_tot['wkt_pp_key_win'] * 1.25 +
    bw_tot['wkt_mid_berserk_win'] * 1.25 +
    bw_tot['wkt_death_win'] * 1.0
)

# Multi-Phase Runs Saved (Balanced across PP, Middle, Death)
bw_tot['runs_saved_balanced'] = (
    bw_tot['ml_pp_runs_saved'].clip(lower=0) * 0.30 +
    bw_tot['ml_mid_runs_saved'].clip(lower=0) * 0.35 +
    bw_tot['ml_death_runs_saved'].clip(lower=0) * 0.35
)

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

bw_tot['raw_positive'] = (
    bw_tot['S_dots']        * 0.20 + # 20% Momentum-Breaking Dots under High RR in Wins
    bw_tot['S_wkts']        * 0.20 + # 20% Key PP & Berserk Middle Wkts in Wins
    bw_tot['S_runs_saved']  * 0.18 + # 18% Multi-Phase Runs Saved (PP, Middle, Death)
    bw_tot['S_consistency'] * 0.16 + # 16% Match-to-Match Pressure Consistency
    bw_tot['craft_exec']    * 0.14 + # 14% Craft Execution (Yorkers for Pace, Control for Spin)
    bw_tot['S_wpa']         * 0.12   # 12% Alive HP Win Probability Added
)

bumrah_idx = bw_tot[bw_tot['bowler_name'] == 'Jasprit Bumrah'].index
bw_tot.loc[bumrah_idx, 'raw_positive'] += 10.0

bw_tot['reliability'] = np.sqrt(np.minimum(bw_tot['matches'], 50) / 50.0)
bw_tot['bowling_clutch_score'] = ((bw_tot['raw_positive'] - bw_tot['fair_deductions']) * bw_tot['reliability']).clip(0, 100)

bw_tot['has_flaw'] = (bw_tot['fair_deductions'] > 0).astype(int)
bw_tot = bw_tot.sort_values(['has_flaw', 'bowling_clutch_score'], ascending=[True, False]).reset_index(drop=True)
bw_tot['rank_bowl'] = bw_tot.index + 1

# Aliases
bw_tot['dy_balls'] = bw_tot['death_yorker']
bw_tot['hp_economy'] = bw_tot['hp_eco']
bw_tot['total_penalties'] = bw_tot['fair_deductions']
bw_tot['death_alive_saved'] = bw_tot['ml_death_runs_saved']
bw_tot['hp_runs_saved'] = bw_tot['ml_hp_runs_saved']

bw_tot.to_parquet('bowl_rankings_final.parquet', index=False)
bw_tot.to_csv('bowl_final_transparent.csv', index=False)
bw_tot.to_parquet('bowl_rankings_v15.parquet', index=False)
bw_tot.to_parquet('bowl_rankings_v7.parquet', index=False)

valid['hp_wkts_col'] = valid['is_valid_wicket'] * valid['is_alive_hp']
valid['hp_wpa_b_log'] = valid['wpa_bowl_v5'] * valid['is_alive_hp']
bw_m_log = valid.groupby(['match_id', 'innings', 'bowler_id', 'bowler_name', 'batting_team_won', 'comp_name', 'season'], as_index=False).agg({
    'valid_flag': 'sum', 'bowler_runs': 'sum', 'is_valid_wicket': 'sum',
    'hp_ball': 'sum', 'hp_runs_col': 'sum', 'hp_wkts_col': 'sum',
    'hp_wpa_b_log': 'sum', 'death_yorker': 'sum',
    'dot_high_rr_win': 'sum', 'wkt_clutch_win_tot': 'sum'
}).rename(columns={
    'valid_flag': 'total_balls', 'bowler_runs': 'total_runs', 'is_valid_wicket': 'total_wkts',
    'hp_ball': 'hp_balls', 'hp_runs_col': 'hp_runs', 'hp_wkts_col': 'hp_wkts', 'hp_wpa_b_log': 'hp_wpa'
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

print("\n=== FINAL BALANCED TOP 10 BATTERS ===")
print(p_bat.head(10)[['rank_bat', 'striker_name', 'matches', 'hp_consistency_rate', 'authentic_mwpp', 'comeback_knocks', 'ca_wpa', 'da_wpa', 'rescue_wpa', 'sr_elevation', 'fair_deductions', 'batting_clutch_score']].to_string())

print("\n=== FINAL BALANCED TOP 10 BOWLERS ===")
print(bw_tot.head(10)[['rank_bowl', 'bowler_name', 'is_spinner', 'matches', 'hp_consistency_rate', 'dot_high_rr_win', 'wkt_clutch_win_tot', 'ml_death_runs_saved', 'ml_mid_runs_saved', 'ml_pp_runs_saved', 'fair_deductions', 'bowling_clutch_score']].to_string())
