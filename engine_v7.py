"""
engine_v7.py — SupeRR Selector v7: Complete Cricket-Sound Analytics
===================================================================
Addresses the "Bumrah Phenomenon" & WPA Volatility Bias:
1. Bowling incorporates:
   - Death Runs Saved vs Phase Par (where Bumrah is #1 in dataset at +208.7 runs saved)
   - Death Yorker Execution Volume & Quality (balls * (10 - eco) + wkts)
   - Shutdown Spells Volume & Quality (shutdown_overs + 1.5 * elite_shutdowns)
   - Economy & Dot Ball Control under pressure
   - WPA & High-Pressure Wickets
   - Knockouts & MoM
2. Batting fixes:
   - Requires min 500 runs & min 6 MWPPs to avoid all-rounder low-sample skew (like Holder)
   - Retains Miller, SKY, Tilak, Gill, Klaasen, Dhoni, Hetmyer, Salt, Phillips, Pooran
3. Complete metrics export and full transparency
"""
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("  SupeRR Selector v7 — Balanced Cricket-Sound Pressure Engine")
print("=" * 70)

# Load base data
print("\n[1/5] Loading valid_v6.parquet and raw matches...")
valid = pd.read_parquet('valid_v6.parquet')
mat_raw = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')

# ----------------- DEATH OVERS MASTERY -----------------
print("\n[2/5] Computing Death Overs Mastery & Yorker Execution...")
death = valid[valid['overid'] >= 16]
d_par_eco = death['bowler_runs'].sum() / len(death) * 6
print(f"      Global Death Overs Par Economy: {d_par_eco:.2f} RPO")

death_bowler = death.groupby('bowler_id').agg(
    d_balls=('bowler_runs', 'count'),
    d_runs=('bowler_runs', 'sum'),
    d_wkts=('is_valid_wicket', 'sum'),
    d_dots=('bowler_runs', lambda x: (x == 0).sum())
).reset_index()

death_bowler['d_runs_saved'] = death_bowler['d_balls'] * (d_par_eco / 6) - death_bowler['d_runs']
death_bowler['d_eco'] = death_bowler['d_runs'] / death_bowler['d_balls'].clip(lower=1) * 6
death_bowler['d_dot_pct'] = death_bowler['d_dots'] / death_bowler['d_balls'].clip(lower=1) * 100

# Death Yorker Execution: volume * margin under 10.0 RPO + wicket bonus
dy_bowler = valid[valid['death_yorker'] == 1].groupby('bowler_id').agg(
    dy_balls=('bowler_runs', 'count'),
    dy_runs=('bowler_runs', 'sum'),
    dy_wkts=('bowler_wicket', 'sum'),
    dy_dots=('bowler_runs', lambda x: (x == 0).sum())
).reset_index()
dy_bowler['dy_eco'] = dy_bowler['dy_runs'] / dy_bowler['dy_balls'].clip(lower=1) * 6
dy_bowler['dy_exec_index'] = (
    dy_bowler['dy_balls'] * (10.0 - dy_bowler['dy_eco']).clip(lower=0) +
    dy_bowler['dy_wkts'] * 12.0
)

# ----------------- BOWLING BASE AGGREGATION -----------------
print("\n[3/5] Aggregating Bowler Metrics...")
bowl_agg = valid.groupby(['bowler_id', 'bowler_name']).agg(
    balls=('valid_flag', 'sum'),
    runs=('bowler_runs', 'sum'),
    wkts=('is_valid_wicket', 'sum'),
    dots=('valid_flag', lambda x: (valid.loc[x.index, 'bowler_runs'] == 0).sum()),
    hp_balls=('valid_flag', lambda x: (valid.loc[x.index, 'is_high_pressure'] == 1).sum()),
    hp_runs=('bowler_runs', lambda x: x[valid.loc[x.index, 'is_high_pressure'] == 1].sum()),
    hp_wkts=('is_valid_wicket', lambda x: x[valid.loc[x.index, 'is_high_pressure'] == 1].sum()),
    wpa_v5=('wpa_bowl_v5', 'sum'),
    da_wpa=('wpa_bowl_v5', lambda x: x[valid.loc[x.index, 'bucket_chase_death_alive'] == 1].sum()),
    shutdown_overs=('is_shutdown_over', 'sum'),
    elite_shutdowns=('is_elite_shutdown', 'sum'),
    cd_wpa=('wpa_bowl_v5', lambda x: x[valid.loc[x.index, 'close_death_ball'] == 1].sum()),
    ko_wpa=('wpa_bowl_v5', lambda x: x[valid.loc[x.index, 'is_knockout'] == 1].sum()),
    choke_wpa=('bowl_choke_wpa', 'sum'),
    seasons=('season', 'nunique'),
    matches=('match_id', 'nunique'),
    mom_bowl=('man_of_the_match', lambda x: (x == valid.loc[x.index, 'bowler_id']).sum())
).reset_index()

bowl_agg['economy'] = bowl_agg['runs'] / bowl_agg['balls'].clip(lower=1) * 6
bowl_agg['hp_economy'] = bowl_agg['hp_runs'] / bowl_agg['hp_balls'].clip(lower=1) * 6
bowl_agg['dot_rate'] = bowl_agg['dots'] / bowl_agg['balls'].clip(lower=1)
bowl_agg['hp_wkt_rate'] = bowl_agg['hp_wkts'] / bowl_agg['hp_balls'].clip(lower=1) * 6
bowl_agg['wpa_per_match'] = bowl_agg['wpa_v5'] / bowl_agg['matches'].clip(lower=1)

# Merge death stats
bowl_agg = bowl_agg.merge(death_bowler[['bowler_id', 'd_balls', 'd_runs_saved', 'd_eco', 'd_wkts']], on='bowler_id', how='left')
bowl_agg['d_balls'] = bowl_agg['d_balls'].fillna(0)
bowl_agg['d_runs_saved'] = bowl_agg['d_runs_saved'].fillna(0)
bowl_agg['d_eco'] = bowl_agg['d_eco'].fillna(12.0)
bowl_agg['d_wkts'] = bowl_agg['d_wkts'].fillna(0)

# Merge yorker stats
bowl_agg = bowl_agg.merge(dy_bowler[['bowler_id', 'dy_balls', 'dy_eco', 'dy_wkts', 'dy_exec_index']], on='bowler_id', how='left')
bowl_agg['dy_balls'] = bowl_agg['dy_balls'].fillna(0)
bowl_agg['dy_eco'] = bowl_agg['dy_eco'].fillna(12.0)
bowl_agg['dy_wkts'] = bowl_agg['dy_wkts'].fillna(0)
bowl_agg['dy_exec_index'] = bowl_agg['dy_exec_index'].fillna(0)

# Shutdown volume index
bowl_agg['shutdown_volume_index'] = bowl_agg['shutdown_overs'] + bowl_agg['elite_shutdowns'] * 1.5

# Calculate MWPP (Match-Winning Pressure Performance)
hp_match_bowl = valid[valid['is_high_pressure'] == 1].groupby(
    ['match_id', 'bowler_id', 'batting_team_won']
).agg(
    hp_b=('bowler_runs', 'count'),
    hp_w=('wpa_bowl_v5', 'sum')
).reset_index()
hp_match_bowl['bowl_won'] = 1 - hp_match_bowl['batting_team_won']
hp_match_bowl['is_mwpp'] = (
    (hp_match_bowl['bowl_won'] == 1) &
    (hp_match_bowl['hp_w'] > 0.005) &
    (hp_match_bowl['hp_b'] >= 3)
).astype(int)
mwpp_b = hp_match_bowl.groupby('bowler_id')['is_mwpp'].sum().reset_index()
mwpp_b.columns = ['bowler_id', 'mwpp_v7']
bowl_agg = bowl_agg.merge(mwpp_b, on='bowler_id', how='left')
bowl_agg['mwpp_v7'] = bowl_agg['mwpp_v7'].fillna(0)

# Eligibility filter for bowlers:
# Min 150 HP balls, min 4 MWPPs, min 2 seasons or 15 matches
bowl_elig = bowl_agg[
    (bowl_agg['hp_balls'] >= 150) &
    (bowl_agg['mwpp_v7'] >= 4) &
    ((bowl_agg['seasons'] >= 2) | (bowl_agg['matches'] >= 15))
].copy()
print(f"      Eligible bowlers: {len(bowl_elig)}")

# Normalization function
def norm(s):
    lo, hi = s.min(), s.max()
    return ((s - lo) / (hi - lo + 1e-9)).clip(0, 1) * 100

bowl_elig['S_wpa'] = norm(bowl_elig['wpa_v5'])
bowl_elig['S_death_saved'] = norm(bowl_elig['d_runs_saved'])
bowl_elig['S_dy_exec'] = norm(bowl_elig['dy_exec_index'])
bowl_elig['S_shutdown_vol'] = norm(bowl_elig['shutdown_volume_index'])
bowl_elig['S_hp_eco'] = norm(-bowl_elig['hp_economy'])
bowl_elig['S_dot_rate'] = norm(bowl_elig['dot_rate'])
bowl_elig['S_hp_wkt'] = norm(bowl_elig['hp_wkt_rate'])
bowl_elig['S_ko'] = norm(bowl_elig['ko_wpa'])
bowl_elig['S_mwpp'] = norm(bowl_elig['mwpp_v7'])
bowl_elig['S_mom'] = norm(bowl_elig['mom_bowl'])
bowl_elig['S_choke'] = norm(-bowl_elig['choke_wpa'].clip(upper=0))
bowl_elig['S_season'] = bowl_elig['seasons'].clip(upper=5) / 5 * 15

# BOWLING CLUTCH SCORE FORMULA:
# High-pressure execution + run suppression + yorker mastery + shutdown spells + WPA + big matches
bowl_elig['bowling_clutch_score'] = (
    bowl_elig['S_wpa']          * 0.20 +
    bowl_elig['S_death_saved']  * 0.16 +
    bowl_elig['S_dy_exec']      * 0.12 +
    bowl_elig['S_shutdown_vol'] * 0.12 +
    bowl_elig['S_hp_eco']       * 0.10 +
    bowl_elig['S_dot_rate']     * 0.08 +
    bowl_elig['S_hp_wkt']       * 0.08 +
    bowl_elig['S_ko']           * 0.06 +
    bowl_elig['S_mwpp']         * 0.05 +
    bowl_elig['S_mom']          * 0.03 -
    bowl_elig['S_choke']        * 0.06 +
    bowl_elig['S_season']
).clip(0, 100)

bowl_elig = bowl_elig.sort_values('bowling_clutch_score', ascending=False).reset_index(drop=True)
bowl_elig['rank_bowl'] = bowl_elig.index + 1

# ----------------- BATTING METRICS (with anti-anomaly filter) -----------------
print("\n[4/5] Aggregating Batting Metrics...")
bat_agg = valid.groupby(['striker_id', 'striker_name']).agg(
    balls=('valid_flag', 'sum'),
    runs=('runs', 'sum'),
    wkts_lost=('is_wicket', 'sum'),
    fours=('is_four', 'sum'),
    sixes=('is_six', 'sum'),
    dots=('valid_flag', lambda x: (valid.loc[x.index, 'runs'] == 0).sum()),
    hp_balls=('valid_flag', lambda x: (valid.loc[x.index, 'is_high_pressure'] == 1).sum()),
    hp_runs=('runs', lambda x: x[valid.loc[x.index, 'is_high_pressure'] == 1].sum()),
    wpa_v5=('wpa_bat_v5', 'sum'),
    da_wpa=('wpa_bat_v5', lambda x: x[valid.loc[x.index, 'bucket_chase_death_alive'] == 1].sum()),
    ca_wpa=('wpa_bat_v5', lambda x: x[valid.loc[x.index, 'is_counter_attack_ball'] == 1].sum()),
    rescue_wpa=('wpa_bat_v5', lambda x: x[valid.loc[x.index, 'rescue_ball'] == 1].sum()),
    cd_wpa=('wpa_bat_v5', lambda x: x[valid.loc[x.index, 'close_death_ball'] == 1].sum()),
    ko_wpa=('wpa_bat_v5', lambda x: x[valid.loc[x.index, 'is_knockout'] == 1].sum()),
    choke_wpa=('bat_choke_wpa', 'sum'),
    seasons=('season', 'nunique'),
    matches=('match_id', 'nunique'),
    mom_bat=('man_of_the_match', lambda x: (x == valid.loc[x.index, 'striker_id']).sum())
).reset_index()

bat_agg['sr'] = bat_agg['runs'] / bat_agg['balls'].clip(lower=1) * 100
bat_agg['hp_sr'] = bat_agg['hp_runs'] / bat_agg['hp_balls'].clip(lower=1) * 100
bat_agg['wpa_per_match'] = bat_agg['wpa_v5'] / bat_agg['matches'].clip(lower=1)

# Calculate MWPP for batting
hp_match_bat = valid[valid['is_high_pressure'] == 1].groupby(
    ['match_id', 'striker_id', 'batting_team_won']
).agg(
    hp_b=('runs', 'count'),
    hp_w=('wpa_bat_v5', 'sum')
).reset_index()
hp_match_bat['is_mwpp'] = (
    (hp_match_bat['batting_team_won'] == 1) &
    (hp_match_bat['hp_w'] > 0.005) &
    (hp_match_bat['hp_b'] >= 3)
).astype(int)
mwpp_bat = hp_match_bat.groupby('striker_id')['is_mwpp'].sum().reset_index()
mwpp_bat.columns = ['striker_id', 'mwpp_v7']
bat_agg = bat_agg.merge(mwpp_bat, on='striker_id', how='left')
bat_agg['mwpp_v7'] = bat_agg['mwpp_v7'].fillna(0)

# Eligibility filter for batters:
# Min 500 total runs, min 6 MWPPs, min 100 HP balls, min 2 seasons
bat_elig = bat_agg[
    (bat_agg['runs'] >= 500) &
    (bat_agg['hp_balls'] >= 100) &
    (bat_agg['mwpp_v7'] >= 6) &
    ((bat_agg['seasons'] >= 2) | (bat_agg['matches'] >= 20))
].copy()
print(f"      Eligible batters: {len(bat_elig)}")

bat_elig['S_wpa'] = norm(bat_elig['wpa_v5'])
bat_elig['S_da'] = norm(bat_elig['da_wpa'])
bat_elig['S_ca'] = norm(bat_elig['ca_wpa'])
bat_elig['S_rescue'] = norm(bat_elig['rescue_wpa'])
bat_elig['S_cd'] = norm(bat_elig['cd_wpa'])
bat_elig['S_ko'] = norm(bat_elig['ko_wpa'])
bat_elig['S_mwpp'] = norm(bat_elig['mwpp_v7'])
bat_elig['S_mom'] = norm(bat_elig['mom_bat'])
bat_elig['S_hpsr'] = norm(bat_elig['hp_sr'])
bat_elig['S_consist'] = norm(bat_agg['wpa_per_match'])
bat_elig['S_choke'] = norm(-bat_elig['choke_wpa'].clip(upper=0))
bat_elig['S_season'] = bat_elig['seasons'].clip(upper=5) / 5 * 15

# BATTING CLUTCH SCORE FORMULA:
bat_elig['batting_clutch_score'] = (
    bat_elig['S_wpa']     * 0.28 +
    bat_elig['S_da']      * 0.16 +
    bat_elig['S_ca']      * 0.14 +
    bat_elig['S_rescue']  * 0.12 +
    bat_elig['S_cd']      * 0.08 +
    bat_elig['S_ko']      * 0.08 +
    bat_elig['S_mwpp']    * 0.06 +
    bat_elig['S_mom']     * 0.04 +
    bat_elig['S_hpsr']    * 0.04 -
    bat_elig['S_choke']   * 0.06 +
    bat_elig['S_season']
).clip(0, 100)

bat_elig = bat_elig.sort_values('batting_clutch_score', ascending=False).reset_index(drop=True)
bat_elig['rank_bat'] = bat_elig.index + 1

# ----------------- DISPLAY AND EXPORT -----------------
print("\n" + "=" * 70)
print("  TOP 10 BATTERS UNDER PRESSURE (v7)")
print("=" * 70)
bat10 = bat_elig.head(10)
for i, r in bat10.iterrows():
    print(f"  {i+1:2d}. {r['striker_name']:<24} Score={r['batting_clutch_score']:.1f} | Runs={int(r['runs'])} | SR={r['sr']:.1f} | HP-SR={r['hp_sr']:.1f} | WPA={r['wpa_v5']:.2f} | DA={r['da_wpa']:.2f} | CA={r['ca_wpa']:.2f} | Rescue={r['rescue_wpa']:.2f} | MWPP={int(r['mwpp_v7'])}")

print("\n" + "=" * 70)
print("  TOP 10 BOWLERS UNDER PRESSURE (v7)")
print("=" * 70)
bowl10 = bowl_elig.head(10)
for i, r in bowl10.iterrows():
    print(f"  {i+1:2d}. {r['bowler_name']:<24} Score={r['bowling_clutch_score']:.1f} | Eco={r['economy']:.2f} | HP-Eco={r['hp_economy']:.2f} | Saved={r['d_runs_saved']:+.1f} | DY-Balls={int(r['dy_balls'])} (Eco {r['dy_eco']:.1f}) | SD-Overs={int(r['shutdown_overs'])} | HP-Wkts={int(r['hp_wkts'])} | MWPP={int(r['mwpp_v7'])}")

# Save parquets & CSVs
print("\n[5/5] Saving v7 files...")
bat_elig.to_parquet('bat_rankings_v7.parquet', index=False)
bowl_elig.to_parquet('bowl_rankings_v7.parquet', index=False)
bat_elig.to_csv('bat_v7_transparent.csv', index=False)
bowl_elig.to_csv('bowl_v7_transparent.csv', index=False)
print("Saved bat_rankings_v7.parquet, bowl_rankings_v7.parquet, bat_v7_transparent.csv, bowl_v7_transparent.csv!")
