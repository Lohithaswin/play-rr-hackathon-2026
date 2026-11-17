"""
engine_v6.py — SupeRR Selector v6 — TRANSPARENT FULL METRICS
=============================================================
NEW vs v5:
  1. Post-collapse rescue metric (2+ wickets fell in 12 balls → batter scores)
  2. Specific delivery execution: yorker economy, bouncer wicket rate, reverse swing
  3. Close-match death overs (WP 35-65%, ov 18+) — most critical balls
  4. Man-of-Match frequency as independent validator/bonus
  5. Knockout match premium (harder filter)
  6. Transparent output: every component printed per player, no black box

Algorithm is FULLY EXPLAINED in output CSV and dashboard — every sub-score visible.
"""
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("  SupeRR Selector v6 — Full Transparent Metrics")
print("=" * 70)

# ─────────────────────── LOAD DATA ────────────────────────────────
print("\n[1/8] Loading data...")
bbb_raw = pd.read_csv('6af458274c1e8_data_pack/Data Pack/ball_by_ball.csv')
mat_raw = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')
p11_raw = pd.read_csv('6af458274c1e8_data_pack/Data Pack/playing_eleven.csv')
cmap    = pd.read_csv('6af458274c1e8_data_pack/Data Pack/competition_team_player_mapping.csv')
valid   = pd.read_parquet('valid_v5.parquet')

# Player name lookup from cmap
player_names = cmap[['player_id','player_name']].drop_duplicates()

# MoM counts (resolved to player_id)
mom_counts = mat_raw[mat_raw['man_of_the_match']!=0]['man_of_the_match'].value_counts().reset_index()
mom_counts.columns = ['player_id','mom_count']

print(f"      {len(valid):,} valid deliveries | {valid['match_id'].nunique()} matches")
print(f"      {len(bbb_raw):,} raw deliveries | {len(mat_raw)} matches in matches.csv")

# ─────────────── MATCH CONTEXT (from raw matches) ──────────────────
print("\n[2/8] Building match context...")
mat_ctx = mat_raw[['match_id','knock_out','stage','man_of_the_match','win_team_id',
                    'result','comp_id']].copy()
mat_ctx['is_final']     = (mat_ctx['stage'] == 'Final').astype(int)
mat_ctx['is_semifinal'] = (mat_ctx['stage'] == 'Semi Final').astype(int)
mat_ctx['is_playoff']   = (mat_ctx['stage'].isin(['Qualifier','Eliminator'])).astype(int)
mat_ctx['is_knockout']  = mat_ctx['knock_out'].astype(int)

# Parse win margin (tighter = more pressure)
mat_ctx['win_by_runs'] = mat_ctx['result'].str.extract(r'by (\d+) runs?', expand=False).astype(float)
mat_ctx['close_match'] = (mat_ctx['win_by_runs'] <= 15).astype(int)  # very close matches

# Merge match context into valid
valid = valid.merge(mat_ctx[['match_id','is_final','is_semifinal','is_playoff',
                              'man_of_the_match','close_match']], on='match_id', how='left')
valid['is_final']    = valid['is_final'].fillna(0).astype(int)
valid['is_semifinal']= valid['is_semifinal'].fillna(0).astype(int)
valid['is_playoff']  = valid['is_playoff'].fillna(0).astype(int)
valid['close_match'] = valid['close_match'].fillna(0).astype(int)

print(f"      Finals: {valid[valid['is_final']==1]['match_id'].nunique()} matches")
print(f"      Knockouts: {valid[valid['is_knockout']==1]['match_id'].nunique()} matches")

# ─────────────── POST-COLLAPSE RESCUE (BATTING) ────────────────────
print("\n[3/8] Computing post-collapse rescue & close-death metrics...")

# Step 1: Compute team wickets in last 12 balls (rolling)
valid_s = valid.sort_values(['match_id','innings','overid','over_ball_num'])
valid_s['team_wkt_ball'] = (
    (valid_s['is_wicket']==1) &
    (~valid_s['dismissal_type'].isin(['RunOut','Run Out','run out']))
).astype(int)

# Rolling 12-ball team wicket count (shift=1 so current ball not included)
valid_s['team_wkts_last12'] = valid_s.groupby(['match_id','innings'])['team_wkt_ball'].transform(
    lambda x: x.shift(1).fillna(0).rolling(12, min_periods=1).sum()
)

# Post-collapse ball: 2+ team wickets in last 12 balls
valid_s['post_collapse']     = (valid_s['team_wkts_last12'] >= 2).astype(int)
valid_s['post_1wkt_collapse']= (valid_s['team_wkts_last12'] >= 1).astype(int)

# Rescue ball: post_collapse AND batter scores 2+ or boundary
valid_s['rescue_ball'] = (
    valid_s['post_collapse'] &
    ((valid_s['runs'] >= 2) | (valid_s['is_four']==1) | (valid_s['is_six']==1))
).astype(int)

# Rescue innings: a batter had 4+ rescue balls (sustained, not a fluke)
rescue_inn = valid_s[valid_s['rescue_ball']==1].groupby(
    ['match_id','innings','striker_id']
)['rescue_ball'].sum().reset_index()
rescue_inn.columns = ['match_id','innings','striker_id','rescue_balls']
rescue_inn['rescue_innings'] = (rescue_inn['rescue_balls'] >= 4).astype(int)

# WPA during rescue balls
rescue_wpa = valid_s[valid_s['rescue_ball']==1].groupby('striker_id').agg(
    rescue_wpa=('wpa_bat_v5','sum'),
    rescue_balls_total=('rescue_ball','sum'),
    rescue_runs=('runs','sum'),
    rescue_sixes=('is_six','sum'),
).reset_index()

print(f"      Post-collapse balls: {valid_s['post_collapse'].sum():,}")
print(f"      Rescue balls: {valid_s['rescue_ball'].sum():,}")
print(f"      Rescue innings (4+ rescue balls): {rescue_inn['rescue_innings'].sum()}")

# ─────────── CLOSE DEATH PERFORMANCE (BOTH) ────────────────────────
# WP 35-65%, overid >= 18 — MOST CRITICAL balls in cricket
close_death_mask = (valid_s['overid'] >= 18) & (valid_s['wp_before'].between(0.35, 0.65))
valid_s['close_death_ball'] = close_death_mask.astype(int)

cd_bat = valid_s[close_death_mask].groupby('striker_id').agg(
    cd_balls=('runs','count'), cd_runs=('runs','sum'), cd_wkts=('is_wicket','sum'),
    cd_wpa=('wpa_bat_v5','sum'),
).reset_index()
cd_bat['cd_sr'] = cd_bat['cd_runs'] / cd_bat['cd_balls'].clip(lower=1) * 100

cd_bowl = valid_s[close_death_mask].groupby('bowler_id').agg(
    cd_balls=('bowler_runs','count'), cd_runs=('bowler_runs','sum'),
    cd_wkts=('is_valid_wicket','sum'), cd_wpa=('wpa_bowl_v5','sum'),
).reset_index()
cd_bowl['cd_eco'] = cd_bowl['cd_runs'] / cd_bowl['cd_balls'].clip(lower=1) * 6

print(f"      Close-death balls (WP35-65%, ov18+): {close_death_mask.sum():,}")

# ─────────── SPECIAL DELIVERY EXECUTION (BOWLING) ──────────────────
print("\n[4/8] Computing special delivery metrics...")

# Merge delivery_style and stroke from raw bbb into valid
bbb_ds = bbb_raw[['match_id','innings','overid','over_ball_num',
                   'delivery_style','stroke','bowl_speed']].copy()
# valid uses innings_ball_num as primary key — merge on match+innings+ball_num instead
# bbb_raw has extras mixed in; we need the VALID ball match
# Strategy: merge on match_id + innings + innings_ball_num (this is consistent)
# delivery_style, stroke, bowl_speed already exist in valid_v5.parquet — no merge needed
# (they were merged during engine_v4_p1 from the raw bbb)
print(f"      delivery_style already present: {valid_s['delivery_style'].notna().sum():,} non-null rows")

# Death yorker = Yorker/Wide Yorker in overs 16-20
valid_s['death_yorker'] = (
    (valid_s['overid'] >= 16) &
    (valid_s['delivery_style'].isin(['Yorker','Wide Yorker']))
).astype(int)

# Wicket-taking delivery (any delivery that got a wicket, excluding run-outs)
valid_s['bowler_wicket'] = (
    (valid_s['is_valid_wicket']==1)
).astype(int)

# Death yorker performance per bowler
dy_bowl = valid_s[valid_s['death_yorker']==1].groupby('bowler_id').agg(
    dy_balls=('bowler_runs','count'),
    dy_runs=('bowler_runs','sum'),
    dy_wkts=('bowler_wicket','sum'),
    dy_wpa=('wpa_bowl_v5','sum'),
).reset_index()
dy_bowl['dy_eco']  = dy_bowl['dy_runs'] / dy_bowl['dy_balls'].clip(lower=1) * 6
dy_bowl['dy_wktp'] = dy_bowl['dy_wkts'] / dy_bowl['dy_balls'].clip(lower=1) * 100

# Bouncer wicket rate in pressure overs
valid_s['pressure_bouncer'] = (
    (valid_s['delivery_style'].isin(['Bouncer','Slow Bouncer'])) &
    (valid_s['is_high_pressure']==1)
).astype(int)

pb_bowl = valid_s[valid_s['pressure_bouncer']==1].groupby('bowler_id').agg(
    pb_balls=('bowler_runs','count'),
    pb_wkts=('bowler_wicket','sum'),
    pb_wpa=('wpa_bowl_v5','sum'),
).reset_index()

# Reverse swing in pressure
valid_s['rev_swing_pressure'] = (
    (valid_s['delivery_style'].isin(['Reverse Swing In','Reverse Swing Out','Reverse Swing'])) &
    (valid_s['is_high_pressure']==1)
).astype(int)

# Wicket-taking variety score: how many different wicket-taking delivery styles a bowler uses
wkt_variety = valid_s[valid_s['bowler_wicket']==1].groupby('bowler_id')['delivery_style'].nunique().reset_index()
wkt_variety.columns = ['bowler_id','wkt_delivery_variety']

print(f"      Death yorker balls: {valid_s['death_yorker'].sum():,}")
print(f"      Pressure bouncers: {valid_s['pressure_bouncer'].sum():,}")

# ─────────── MAN OF THE MATCH FREQUENCY ───────────────────────────
print("\n[5/8] Man of the Match integration...")

# MoM linked to player_id in matches.csv; also cross-ref with striker_id/bowler_id in bbb
# striker_id/bowler_id ARE the same as player_id (they come from same player registry)
mom_bat = mom_counts.rename(columns={'player_id':'striker_id','mom_count':'mom_bat'})
mom_bowl= mom_counts.rename(columns={'player_id':'bowler_id','mom_count':'mom_bowl'})
print(f"      MoM data for {len(mom_counts)} players")

# ─────────── KNOCKOUT PERFORMANCE ─────────────────────────────────
print("\n[6/8] Knockout match performance...")

ko_bat = valid_s[valid_s['is_knockout']==1].groupby('striker_id').agg(
    ko_balls=('runs','count'), ko_runs=('runs','sum'),
    ko_wpa=('wpa_bat_v5','sum'), ko_matches=('match_id','nunique'),
).reset_index()
ko_bat['ko_sr'] = ko_bat['ko_runs'] / ko_bat['ko_balls'].clip(lower=1) * 100

ko_bowl = valid_s[valid_s['is_knockout']==1].groupby('bowler_id').agg(
    ko_balls=('bowler_runs','count'), ko_runs=('bowler_runs','sum'),
    ko_wkts=('is_valid_wicket','sum'), ko_wpa=('wpa_bowl_v5','sum'),
    ko_matches=('match_id','nunique'),
).reset_index()

# ─────────── AGGREGATE ALL INTO RANKINGS ──────────────────────────
print("\n[7/8] Building v6 transparent rankings...")

# ─── BATTING ───
bat_base = valid_s.groupby(['striker_id','striker_name']).agg(
    balls=('valid_flag','sum'),
    runs=('runs','sum'),
    fours=('is_four','sum'),
    sixes=('is_six','sum'),
    dots=('valid_flag', lambda x: (valid_s.loc[x.index,'runs']==0).sum()),
    wkts_lost=('is_wicket','sum'),
    # HP totals
    hp_balls=('valid_flag',   lambda x: (valid_s.loc[x.index,'is_high_pressure']==1).sum()),
    hp_runs=('runs',          lambda x: x[valid_s.loc[x.index,'is_high_pressure']==1].sum()),
    # WPA scores
    wpa_v5=('wpa_bat_v5','sum'),
    da_wpa=('wpa_bat_v5',     lambda x: x[valid_s.loc[x.index,'bucket_chase_death_alive']==1].sum()),
    ca_wpa=('wpa_bat_v5',     lambda x: x[valid_s.loc[x.index,'is_counter_attack_ball']==1].sum()),
    rescue_wpa_ball=('wpa_bat_v5', lambda x: x[valid_s.loc[x.index,'rescue_ball']==1].sum()),
    cd_wpa_ball=('wpa_bat_v5',    lambda x: x[valid_s.loc[x.index,'close_death_ball']==1].sum()),
    # post-collapse
    post_collapse_balls=('post_collapse','sum'),
    rescue_balls=('rescue_ball','sum'),
    # close death
    cd_balls_bat=('close_death_ball','sum'),
    # Knockout
    ko_matches=('match_id', lambda x: x[valid_s.loc[x.index,'is_knockout']==1].nunique()),
    ko_wpa_b=('wpa_bat_v5', lambda x: x[valid_s.loc[x.index,'is_knockout']==1].sum()),
    # Final
    final_wpa=('wpa_bat_v5', lambda x: x[valid_s.loc[x.index,'is_final']==1].sum()),
    # Choke
    choke_wpa=('bat_choke_wpa','sum'),
    # Match context
    seasons=('season','nunique'),
    matches=('match_id','nunique'),
).reset_index()

bat_base['sr']       = bat_base['runs'] / bat_base['balls'].clip(lower=1) * 100
bat_base['hp_sr']    = bat_base['hp_runs'] / bat_base['hp_balls'].clip(lower=1) * 100
bat_base['avg']      = bat_base['runs'] / bat_base['wkts_lost'].clip(lower=1)
bat_base['six_rate'] = bat_base['sixes'] / bat_base['balls'].clip(lower=1) * 100
bat_base['wpa_per_match'] = bat_base['wpa_v5'] / bat_base['matches'].clip(lower=1)

# Merge in MWPP (from v5)
try:
    bat_v5 = pd.read_parquet('bat_rankings_v5.parquet')[
        ['striker_id','mwpp','ca_innings_total','seasons_active']].copy()
    bat_base = bat_base.merge(bat_v5, on='striker_id', how='left')
    bat_base['mwpp'] = bat_base['mwpp'].fillna(0)
    bat_base['ca_innings_total'] = bat_base['ca_innings_total'].fillna(0)
except: bat_base['mwpp'] = 0

# Merge rescue WPA
bat_base = bat_base.merge(rescue_wpa[['striker_id','rescue_wpa','rescue_sixes']], on='striker_id', how='left')
bat_base['rescue_wpa'] = bat_base['rescue_wpa'].fillna(0)
bat_base['rescue_sixes'] = bat_base['rescue_sixes'].fillna(0)

# Merge close-death batting stats
bat_base = bat_base.merge(cd_bat.rename(columns={'cd_wpa':'cd_wpa_agg'}), on='striker_id', how='left')
bat_base['cd_wpa_agg'] = bat_base['cd_wpa_agg'].fillna(0)
bat_base['cd_sr']      = bat_base.get('cd_sr', pd.Series(0, index=bat_base.index)).fillna(0)

# Merge MoM
bat_base = bat_base.merge(mom_bat, on='striker_id', how='left')
bat_base['mom_bat'] = bat_base['mom_bat'].fillna(0)

# Merge KO
bat_base = bat_base.merge(ko_bat[['striker_id','ko_sr','ko_wpa']], on='striker_id', how='left')
bat_base['ko_wpa'] = bat_base['ko_wpa'].fillna(0)
bat_base['ko_sr']  = bat_base['ko_sr'].fillna(0)

# MWPP v6: re-compute with close_death and rescue bonuses
# Match-winning pressure performance = match where HP WPA>0 & team won (from v5 engine)
# We also add close_death contribution check here
hp_match_bat = valid_s[valid_s['is_high_pressure']==1].groupby(
    ['match_id','striker_id','batting_team_won']
).agg(
    hp_balls=('runs','count'),
    hp_wpa=('wpa_bat_v5','sum'),
    rescue_b=('rescue_ball','sum'),
    cd_b=('close_death_ball','sum'),
).reset_index()
hp_match_bat['is_mwpp_v6'] = (
    (hp_match_bat['batting_team_won']==1) &
    (hp_match_bat['hp_wpa'] > 0.005) &
    (hp_match_bat['hp_balls'] >= 3)
).astype(int)
mwpp_bat_v6 = hp_match_bat.groupby('striker_id').agg(
    mwpp_v6=('is_mwpp_v6','sum'),
    total_hp_matches=('match_id','nunique'),
).reset_index()
bat_base = bat_base.merge(mwpp_bat_v6, on='striker_id', how='left')
bat_base['mwpp_v6'] = bat_base['mwpp_v6'].fillna(0)

# ── ELIGIBILITY ──
bat_elig = bat_base[
    (bat_base['hp_balls'] >= 100) &
    (bat_base['mwpp_v6'] >= 5) &
    (bat_base['seasons'] >= 2) | (bat_base['matches'] >= 20)
].copy()
print(f"      Eligible batters: {len(bat_elig)}")

# ── NORMALIZE + SCORE ──
def norm(s, lo=None, hi=None):
    lo = lo if lo is not None else s.min()
    hi = hi if hi is not None else s.max()
    return ((s - lo) / (hi - lo + 1e-9)).clip(0, 1) * 100

bat_elig['S_wpa']       = norm(bat_elig['wpa_v5'])          # Total HP WPA         [0-100]
bat_elig['S_da']        = norm(bat_elig['da_wpa'])           # Death-alive WPA      [0-100]
bat_elig['S_ca']        = norm(bat_elig['ca_wpa'])           # Counter-attack WPA   [0-100]
bat_elig['S_rescue']    = norm(bat_elig['rescue_wpa'])       # Post-collapse rescue [0-100]
bat_elig['S_cd']        = norm(bat_elig['cd_wpa_agg'])       # Close-death WPA      [0-100]
bat_elig['S_ko']        = norm(bat_elig['ko_wpa'])           # Knockout WPA         [0-100]
bat_elig['S_mom']       = norm(bat_elig['mom_bat'])          # MoM frequency        [0-100]
bat_elig['S_mwpp']      = norm(bat_elig['mwpp_v6'])          # MWPP count           [0-100]
bat_elig['S_hpsr']      = norm(bat_elig['hp_sr'])            # HP Strike rate       [0-100]
bat_elig['S_consist']   = norm(bat_elig['wpa_per_match'])    # Per-match WPA        [0-100]
bat_elig['S_choke']     = norm(-bat_elig['choke_wpa'].clip(upper=0))  # Choke penalty
bat_elig['S_season']    = bat_elig['seasons'].clip(upper=5) / 5 * 15  # Season bonus

# TRANSPARENT FORMULA (weights visible):
# Component          Weight   Rationale
# S_wpa              30%      Core HP performance
# S_da               15%      Death-alive (highest pressure) 
# S_ca               12%      Counter-attack under duress
# S_rescue           10%      Post-collapse rescue specialist
# S_cd                8%      Clutch close-match death (WP35-65%, ov18+)
# S_ko                8%      Knockout match performance
# S_mwpp              7%      Match-winning pressure performances (count)
# S_mom               5%      Man-of-Match (independent validator)
# S_hpsr              3%      HP Strike Rate
# S_consist           2%      Per-match consistency
# S_choke            -8%      Choke penalty (negative WPA in pressure)
# S_season           +15 pts  Season bonus

bat_elig['batting_clutch_score'] = (
    bat_elig['S_wpa']     * 0.30 +
    bat_elig['S_da']      * 0.15 +
    bat_elig['S_ca']      * 0.12 +
    bat_elig['S_rescue']  * 0.10 +
    bat_elig['S_cd']      * 0.08 +
    bat_elig['S_ko']      * 0.08 +
    bat_elig['S_mwpp']    * 0.07 +
    bat_elig['S_mom']     * 0.05 +
    bat_elig['S_hpsr']    * 0.03 +
    bat_elig['S_consist'] * 0.02 -
    bat_elig['S_choke']   * 0.08 +
    bat_elig['S_season']
).clip(0, 100)

bat_elig = bat_elig.sort_values('batting_clutch_score', ascending=False).reset_index(drop=True)
bat_elig['rank_bat'] = bat_elig.index + 1

# ─── BOWLING ───
bowl_base = valid_s.groupby(['bowler_id','bowler_name']).agg(
    balls=('valid_flag','sum'),
    runs=('bowler_runs','sum'),
    wkts=('is_valid_wicket','sum'),
    dots=('valid_flag', lambda x: (valid_s.loc[x.index,'bowler_runs']==0).sum()),
    # HP totals
    hp_balls=('valid_flag',       lambda x: (valid_s.loc[x.index,'is_high_pressure']==1).sum()),
    hp_runs=('bowler_runs',       lambda x: x[valid_s.loc[x.index,'is_high_pressure']==1].sum()),
    hp_wkts=('is_valid_wicket',   lambda x: x[valid_s.loc[x.index,'is_high_pressure']==1].sum()),
    # WPA
    wpa_v5=('wpa_bowl_v5','sum'),
    da_wpa=('wpa_bowl_v5',        lambda x: x[valid_s.loc[x.index,'bucket_chase_death_alive']==1].sum()),
    shutdown_wpa=('wpa_bowl_v5',  lambda x: x[valid_s.loc[x.index,'is_shutdown_over']==True].sum()),
    cd_wpa_bowl=('wpa_bowl_v5',   lambda x: x[valid_s.loc[x.index,'close_death_ball']==1].sum()),
    ko_wpa_bowl=('wpa_bowl_v5',   lambda x: x[valid_s.loc[x.index,'is_knockout']==1].sum()),
    final_wpa=('wpa_bowl_v5',     lambda x: x[valid_s.loc[x.index,'is_final']==1].sum()),
    # Choke
    choke_wpa=('bowl_choke_wpa','sum'),
    # Shutdown
    shutdown_overs=('is_shutdown_over','sum'),
    elite_shutdowns=('is_elite_shutdown','sum'),
    # Knockout
    ko_balls=('valid_flag',       lambda x: (valid_s.loc[x.index,'is_knockout']==1).sum()),
    ko_wkts=('is_valid_wicket',   lambda x: x[valid_s.loc[x.index,'is_knockout']==1].sum()),
    ko_matches=('match_id',       lambda x: x[valid_s.loc[x.index,'is_knockout']==1].nunique()),
    # Match context
    seasons=('season','nunique'),
    matches=('match_id','nunique'),
).reset_index()

bowl_base['economy']     = bowl_base['runs'] / bowl_base['balls'].clip(lower=1) * 6
bowl_base['hp_economy']  = bowl_base['hp_runs'] / bowl_base['hp_balls'].clip(lower=1) * 6
bowl_base['hp_wkt_rate'] = bowl_base['hp_wkts'] / bowl_base['hp_balls'].clip(lower=1) * 6
bowl_base['dot_rate']    = bowl_base['dots'] / bowl_base['balls'].clip(lower=1)
bowl_base['wpa_per_match']= bowl_base['wpa_v5'] / bowl_base['matches'].clip(lower=1)

# Merge in special delivery stats
bowl_base = bowl_base.merge(dy_bowl[['bowler_id','dy_balls','dy_wkts','dy_eco','dy_wpa']], on='bowler_id', how='left')
bowl_base['dy_balls'] = bowl_base['dy_balls'].fillna(0)
bowl_base['dy_wkts']  = bowl_base['dy_wkts'].fillna(0)
bowl_base['dy_eco']   = bowl_base['dy_eco'].fillna(10.0)
bowl_base['dy_wpa']   = bowl_base['dy_wpa'].fillna(0)

bowl_base = bowl_base.merge(pb_bowl[['bowler_id','pb_wkts','pb_wpa']], on='bowler_id', how='left')
bowl_base['pb_wkts'] = bowl_base['pb_wkts'].fillna(0)
bowl_base['pb_wpa']  = bowl_base['pb_wpa'].fillna(0)

bowl_base = bowl_base.merge(wkt_variety, on='bowler_id', how='left')
bowl_base['wkt_delivery_variety'] = bowl_base['wkt_delivery_variety'].fillna(0)

# Merge close-death bowl
bowl_base = bowl_base.merge(cd_bowl[['bowler_id','cd_wkts','cd_eco','cd_wpa']], on='bowler_id', how='left')
bowl_base['cd_wkts'] = bowl_base['cd_wkts'].fillna(0)
bowl_base['cd_eco']  = bowl_base['cd_eco'].fillna(10.0)
bowl_base['cd_wpa']  = bowl_base['cd_wpa'].fillna(0)

# Merge MoM
bowl_base = bowl_base.merge(mom_bowl, on='bowler_id', how='left')
bowl_base['mom_bowl'] = bowl_base['mom_bowl'].fillna(0)

# MWPP v6 for bowling
hp_match_bowl = valid_s[valid_s['is_high_pressure']==1].groupby(
    ['match_id','bowler_id','batting_team_won']
).agg(
    hp_balls=('bowler_runs','count'),
    hp_wpa=('wpa_bowl_v5','sum'),
    cd_b=('close_death_ball','sum'),
).reset_index()
hp_match_bowl['bowling_team_won'] = 1 - hp_match_bowl['batting_team_won']
hp_match_bowl['is_mwpp_v6'] = (
    (hp_match_bowl['bowling_team_won']==1) &
    (hp_match_bowl['hp_wpa'] > 0.005) &
    (hp_match_bowl['hp_balls'] >= 3)
).astype(int)
mwpp_bowl_v6 = hp_match_bowl.groupby('bowler_id').agg(
    mwpp_v6=('is_mwpp_v6','sum'),
).reset_index()
bowl_base = bowl_base.merge(mwpp_bowl_v6, on='bowler_id', how='left')
bowl_base['mwpp_v6'] = bowl_base['mwpp_v6'].fillna(0)

# ── ELIGIBILITY ──
bowl_elig = bowl_base[
    (bowl_base['hp_balls'] >= 150) &
    (bowl_base['mwpp_v6'] >= 4) &
    ((bowl_base['seasons'] >= 2) | (bowl_base['matches'] >= 15))
].copy()
print(f"      Eligible bowlers: {len(bowl_elig)}")

# ── NORMALIZE + SCORE ──
bowl_elig['S_wpa']       = norm(bowl_elig['wpa_v5'])
bowl_elig['S_da']        = norm(bowl_elig['da_wpa'])
bowl_elig['S_shutdown']  = norm(bowl_elig['shutdown_wpa'])
bowl_elig['S_cd']        = norm(bowl_elig['cd_wpa'])
bowl_elig['S_ko']        = norm(bowl_elig['ko_wpa_bowl'])
bowl_elig['S_wkt']       = norm(bowl_elig['hp_wkt_rate'])
bowl_elig['S_eco']       = norm(-bowl_elig['hp_economy'])
bowl_elig['S_dy']        = norm(bowl_elig['dy_wpa'])          # Death yorker WPA
bowl_elig['S_mwpp']      = norm(bowl_elig['mwpp_v6'])
bowl_elig['S_mom']       = norm(bowl_elig['mom_bowl'])
bowl_elig['S_consist']   = norm(bowl_elig['wpa_per_match'])
bowl_elig['S_variety']   = norm(bowl_elig['wkt_delivery_variety'])
bowl_elig['S_choke']     = norm(-bowl_elig['choke_wpa'].clip(upper=0))
bowl_elig['S_season']    = bowl_elig['seasons'].clip(upper=5) / 5 * 15

# TRANSPARENT FORMULA (weights visible):
# S_wpa         30%   Core HP WPA
# S_da          15%   Death-alive WPA
# S_shutdown    12%   Shutdown spell WPA (high RR → clamp)
# S_cd           8%   Close-death clutch (WP35-65%, ov18+)
# S_ko           7%   Knockout WPA
# S_wkt          7%   HP wicket rate
# S_dy           6%   Death yorker execution
# S_eco          5%   HP economy control
# S_mwpp         4%   MWPP count
# S_mom          3%   MoM frequency
# S_variety      2%   Wicket-taking variety
# S_consist      1%   Per-match consistency
# S_choke       -8%   Choke penalty
# S_season      +15   Season bonus

bowl_elig['bowling_clutch_score'] = (
    bowl_elig['S_wpa']      * 0.30 +
    bowl_elig['S_da']       * 0.15 +
    bowl_elig['S_shutdown'] * 0.12 +
    bowl_elig['S_cd']       * 0.08 +
    bowl_elig['S_ko']       * 0.07 +
    bowl_elig['S_wkt']      * 0.07 +
    bowl_elig['S_dy']       * 0.06 +
    bowl_elig['S_eco']      * 0.05 +
    bowl_elig['S_mwpp']     * 0.04 +
    bowl_elig['S_mom']      * 0.03 +
    bowl_elig['S_variety']  * 0.02 +
    bowl_elig['S_consist']  * 0.01 -
    bowl_elig['S_choke']    * 0.08 +
    bowl_elig['S_season']
).clip(0, 100)

bowl_elig = bowl_elig.sort_values('bowling_clutch_score', ascending=False).reset_index(drop=True)
bowl_elig['rank_bowl'] = bowl_elig.index + 1

# ─────────────────────── PRINT FULL TRANSPARENT OUTPUT ─────────────
print("\n" + "=" * 70)
print("  TOP 10 BATTERS UNDER PRESSURE (v6) — FULL METRICS")
print("=" * 70)
bat_cols_print = ['striker_name','batting_clutch_score',
                  'S_wpa','S_da','S_ca','S_rescue','S_cd','S_ko','S_mwpp','S_mom',
                  'wpa_v5','da_wpa','ca_wpa','rescue_wpa','cd_wpa_agg','ko_wpa',
                  'mwpp_v6','mom_bat','sr','hp_sr','seasons','matches']
bat10 = bat_elig.head(10)
for i, r in bat10.iterrows():
    print(f"\n  {i+1:2d}. {r['striker_name']}")
    print(f"      SCORE={r['batting_clutch_score']:.1f}")
    print(f"      Component Scores: WPA={r['S_wpa']:.1f} | DA={r['S_da']:.1f} | CA={r['S_ca']:.1f} | Rescue={r['S_rescue']:.1f} | CD={r['S_cd']:.1f} | KO={r['S_ko']:.1f} | MWPP={r['S_mwpp']:.1f} | MoM={r['S_mom']:.1f}")
    print(f"      Raw Metrics: WPA={r['wpa_v5']:.2f} | DA-WPA={r['da_wpa']:.2f} | CA-WPA={r['ca_wpa']:.2f} | Rescue-WPA={r['rescue_wpa']:.2f} | CD-WPA={r['cd_wpa_agg']:.2f} | KO-WPA={r['ko_wpa']:.2f}")
    print(f"      Context: MWPP={int(r['mwpp_v6'])} | MoM={int(r['mom_bat'])} | SR={r['sr']:.1f} | HP-SR={r['hp_sr']:.1f} | Seas={int(r['seasons'])} | Matches={int(r['matches'])}")

print("\n\n" + "=" * 70)
print("  TOP 10 BOWLERS UNDER PRESSURE (v6) — FULL METRICS")
print("=" * 70)
bowl10 = bowl_elig.head(10)
for i, r in bowl10.iterrows():
    print(f"\n  {i+1:2d}. {r['bowler_name']}")
    print(f"      SCORE={r['bowling_clutch_score']:.1f}")
    print(f"      Component Scores: WPA={r['S_wpa']:.1f} | DA={r['S_da']:.1f} | Shutdown={r['S_shutdown']:.1f} | CD={r['S_cd']:.1f} | KO={r['S_ko']:.1f} | Wkt={r['S_wkt']:.1f} | Yorker={r['S_dy']:.1f} | MWPP={r['S_mwpp']:.1f} | MoM={r['S_mom']:.1f}")
    print(f"      Raw Metrics: WPA={r['wpa_v5']:.2f} | DA-WPA={r['da_wpa']:.2f} | SD-WPA={r['shutdown_wpa']:.2f} | CD-WPA={r['cd_wpa']:.2f} | KO-WPA={r['ko_wpa_bowl']:.2f}")
    print(f"      Specials: Death-Yorkers={int(r['dy_balls'])} dy-eco={r['dy_eco']:.1f} dy-wkts={int(r['dy_wkts'])} | EliteShutdowns={int(r['elite_shutdowns'])} | WktVariety={int(r['wkt_delivery_variety'])}")
    print(f"      Context: MWPP={int(r['mwpp_v6'])} | MoM={int(r['mom_bowl'])} | Eco={r['economy']:.2f} | HP-Eco={r['hp_economy']:.2f} | Seas={int(r['seasons'])} | Matches={int(r['matches'])}")

# ─────────────────────── SAVE ──────────────────────────────────────
print("\nSaving files...")
bat_elig.to_parquet('bat_rankings_v6.parquet', index=False)
bowl_elig.to_parquet('bowl_rankings_v6.parquet', index=False)
valid_s.to_parquet('valid_v6.parquet', index=False)

# Save full transparent CSV (all scores visible)
bat_elig[['rank_bat','striker_name','batting_clutch_score',
           'S_wpa','S_da','S_ca','S_rescue','S_cd','S_ko','S_mwpp','S_mom',
           'wpa_v5','da_wpa','ca_wpa','rescue_wpa','cd_wpa_agg','ko_wpa',
           'mwpp_v6','mom_bat','sr','hp_sr','hp_balls','hp_runs',
           'seasons','matches','choke_wpa']
         ].to_csv('bat_v6_transparent.csv', index=False)

bowl_elig[['rank_bowl','bowler_name','bowling_clutch_score',
            'S_wpa','S_da','S_shutdown','S_cd','S_ko','S_wkt','S_dy','S_mwpp','S_mom',
            'wpa_v5','da_wpa','shutdown_wpa','cd_wpa','ko_wpa_bowl',
            'hp_wkt_rate','dy_balls','dy_eco','dy_wkts','dy_wpa',
            'elite_shutdowns','wkt_delivery_variety',
            'mwpp_v6','mom_bowl','economy','hp_economy',
            'seasons','matches','choke_wpa']
          ].to_csv('bowl_v6_transparent.csv', index=False)

print("\nDone! Files saved:")
print("  bat_rankings_v6.parquet / bat_v6_transparent.csv")
print("  bowl_rankings_v6.parquet / bowl_v6_transparent.csv")
print("  valid_v6.parquet")
