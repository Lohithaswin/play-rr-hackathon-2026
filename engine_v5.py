"""
engine_v5.py — SupeRR Selector v5
Enhancements over v4:
  1. Counter-attack bonus: dots pile / wickets fall → batter scores → boosted WPA
  2. Shutdown spell bonus: high run-rate phase → bowler clamps it → boosted WPA
  3. Min match-winning pressure performances filter (no one-match wonders)
  4. Consistency multiplier across seasons
"""
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("SupeRR Selector v5 — Counter-attack + Shutdown + Min-Perf")
print("=" * 60)

# ─────────────────────────── LOAD DATA ────────────────────────────
print("\n[1/6] Loading valid_v4.parquet...")
df = pd.read_parquet('valid_v4.parquet')
print(f"      {len(df):,} valid deliveries, {df['match_id'].nunique()} matches")

# Sort chronologically within each innings
df = df.sort_values(['match_id', 'innings', 'overid', 'over_ball_num']).reset_index(drop=True)

# ─────────────────── COUNTER-ATTACK DETECTION ─────────────────────
print("\n[2/6] Detecting counter-attack events...")

# Pressure build-up indicators (already computed in v4):
#   recent_dots_5  = dot balls in last 5 delivered balls (0-5)
#   recent_wickets_5 = wickets in last 5 balls (team level)
# Trigger: dots >= 3 in last 5  OR  wickets >= 1 in last 5 AND dots >= 2

df['dot_pressure_trigger']  = df['recent_dots_5'] >= 3
df['wicket_pressure_trigger'] = (df['recent_wickets_5'] >= 1) & (df['recent_dots_5'] >= 2)
df['pressure_trigger']      = df['dot_pressure_trigger'] | df['wicket_pressure_trigger']

# Counter-attack ball: pressure was building AND batter responds with 2+ runs or boundary
df['is_counter_attack_ball'] = (
    df['pressure_trigger'] &
    ((df['runs'] >= 2) | (df['is_four'] == 1) | (df['is_six'] == 1))
)

# Counter-attack BONUS multiplier applied to batting WPA for those balls
# Base 1.8x; +0.4 extra if it's a six (maximum aggression)
df['counter_attack_mult'] = np.where(
    df['is_counter_attack_ball'],
    np.where(df['is_six'] == 1, 2.2, 1.8),
    1.0
)

# Counter-attack innings flag: batter had 3+ counter-attack balls in a single innings (sustained, not lucky)
ca_innings = df[df['is_counter_attack_ball']].groupby(
    ['match_id', 'innings', 'striker_id']
)['is_counter_attack_ball'].sum().reset_index()
ca_innings.columns = ['match_id', 'innings', 'striker_id', 'ca_balls']
ca_innings['ca_innings'] = (ca_innings['ca_balls'] >= 3).astype(int)
df = df.merge(ca_innings[['match_id', 'innings', 'striker_id', 'ca_innings']],
              on=['match_id', 'innings', 'striker_id'], how='left')
df['ca_innings'] = df['ca_innings'].fillna(0).astype(int)

n_ca = df['is_counter_attack_ball'].sum()
n_ca_inn = ca_innings[ca_innings['ca_innings']==1].shape[0]
print(f"      Counter-attack balls: {n_ca:,} | Sustained CA innings: {n_ca_inn:,}")

# ─────────────────── SHUTDOWN SPELL DETECTION ─────────────────────
print("\n[3/6] Detecting shutdown spells...")

# A shutdown over: team was scoring at >= 10 rr in RECENT 2 overs,
# and this bowler concedes <= 7 runs (or takes a wicket conceding <= 9)
# We already have:  recent_avg_rr = avg run rate of previous 2 overs
#                   over_rr       = current over run rate (computed per over)

# Compute over-level bowler economy for each over
over_grp = df.groupby(['match_id', 'innings', 'overid', 'bowler_id', 'bowler_name']).agg(
    over_runs_conceded=('bowler_runs', 'sum'),
    over_valid_balls=('valid_flag', 'sum'),
    over_wickets=('is_valid_wicket', 'sum'),
    recent_avg_rr_over=('recent_avg_rr', 'first'),  # run rate before this over started
    match_alive_over=('match_alive', 'any'),
    phase_over=('phase', 'first'),
    innings_num=('innings', 'first'),
    batting_team_won_over=('batting_team_won', 'first'),
    match_importance_over=('match_importance', 'first'),
).reset_index()

# Shutdown condition
over_grp['bowler_economy_over'] = np.where(
    over_grp['over_valid_balls'] > 0,
    over_grp['over_runs_conceded'] / over_grp['over_valid_balls'] * 6,
    99.0
)

# Shutdown = previous 2 overs avg rr >= 10 AND this bowler's economy <= 7
# or previous rr >= 9 and economy <= 6 (tighter)
over_grp['is_shutdown_over'] = (
    (over_grp['recent_avg_rr_over'] >= 10) &
    (over_grp['bowler_economy_over'] <= 7)
) | (
    (over_grp['recent_avg_rr_over'] >= 9) &
    (over_grp['bowler_economy_over'] <= 6)
)

# Wicket in a shutdown over = elite shutdown
over_grp['is_elite_shutdown'] = over_grp['is_shutdown_over'] & (over_grp['over_wickets'] >= 1)

# Extra bonus if match was alive during the shutdown
over_grp['shutdown_alive'] = over_grp['is_shutdown_over'] & over_grp['match_alive_over']

n_shutdown   = over_grp['is_shutdown_over'].sum()
n_elite_sd   = over_grp['is_elite_shutdown'].sum()
n_sd_alive   = over_grp['shutdown_alive'].sum()
print(f"      Shutdown overs: {n_shutdown:,} | Elite (w/ wkt): {n_elite_sd:,} | Match-alive: {n_sd_alive:,}")

# Merge shutdown flags back onto ball-level
df = df.merge(
    over_grp[['match_id', 'innings', 'overid', 'bowler_id',
               'is_shutdown_over', 'is_elite_shutdown', 'shutdown_alive']],
    on=['match_id', 'innings', 'overid', 'bowler_id'], how='left'
)
df['is_shutdown_over']  = df['is_shutdown_over'].fillna(False)
df['is_elite_shutdown'] = df['is_elite_shutdown'].fillna(False)
df['shutdown_alive']    = df['shutdown_alive'].fillna(False)

# Shutdown multiplier for bowling WPA
# Base 1.6x, elite 2.0x, alive extra ×1.2
df['shutdown_mult'] = np.where(
    df['is_elite_shutdown'] & df['shutdown_alive'], 2.4,
    np.where(df['is_elite_shutdown'],               2.0,
    np.where(df['shutdown_alive'],                  1.8,
    np.where(df['is_shutdown_over'],                1.6,
    1.0))))

# ────────────────── ENHANCED V5 WPA SCORES ────────────────────────
print("\n[4/6] Computing v5 enhanced WPA scores...")

# V4 had: wpa_bat_v4, wpa_bowl_v4 (already includes phase_weight, bonus_mult, match_importance, win_mult)
# V5 adds: counter_attack_mult (bat), shutdown_mult (bowl)
# We'll apply these multiplicatively on top of v4 scores

df['wpa_bat_v5']  = df['wpa_bat_v4']  * df['counter_attack_mult']
df['wpa_bowl_v5'] = df['wpa_bowl_v4'] * df['shutdown_mult']

# ─────────── PER-PLAYER MATCH-WINNING PRESSURE PERFORMANCES ───────
print("\n[5/6] Computing match-winning pressure performance counts...")

hp = df[df['is_high_pressure'] == 1].copy()

# BATTING: match-winning pressure performance = 
#   match where batter had net positive wpa_bat_v5 in HP balls AND team won
bat_match = hp.groupby(['match_id', 'striker_id', 'striker_name', 'batting_team_won']).agg(
    hp_balls=('wpa_bat_v5', 'count'),
    hp_wpa=('wpa_bat_v5', 'sum'),
    hp_runs=('runs', 'sum'),
    ca_innings=('ca_innings', 'max'),
    seasons_played=('season', 'nunique'),
).reset_index()

bat_match['is_mwpp'] = (
    (bat_match['batting_team_won'] == 1) &
    (bat_match['hp_wpa'] > 0.005) &
    (bat_match['hp_balls'] >= 3)       # at least 3 HP balls in the match
).astype(int)

bat_mwpp = bat_match.groupby(['striker_id', 'striker_name']).agg(
    mwpp=('is_mwpp', 'sum'),
    total_hp_matches=('match_id', 'nunique'),
    seasons_active=('seasons_played', 'max'),
    ca_innings_total=('ca_innings', 'sum'),
).reset_index()

# BOWLING: match-winning pressure performance =
#   match where bowler had net positive wpa_bowl_v5 in HP balls AND bowling team won
bowl_match = hp.groupby(['match_id', 'bowler_id', 'bowler_name', 'batting_team_won']).agg(
    hp_balls=('wpa_bowl_v5', 'count'),
    hp_wpa=('wpa_bowl_v5', 'sum'),
    hp_wkts=('is_valid_wicket', 'sum'),
    shutdown_overs=('is_shutdown_over', 'sum'),
    seasons_played=('season', 'nunique'),
).reset_index()

bowl_match['bowling_team_won'] = 1 - bowl_match['batting_team_won']
bowl_match['is_mwpp'] = (
    (bowl_match['bowling_team_won'] == 1) &
    (bowl_match['hp_wpa'] > 0.005) &
    (bowl_match['hp_balls'] >= 3)
).astype(int)

bowl_mwpp = bowl_match.groupby(['bowler_id', 'bowler_name']).agg(
    mwpp=('is_mwpp', 'sum'),
    total_hp_matches=('match_id', 'nunique'),
    seasons_active=('seasons_played', 'max'),
    shutdown_match_total=('shutdown_overs', 'sum'),
).reset_index()

print(f"      Bat MWPP distribution: {bat_mwpp['mwpp'].describe().to_dict()}")
print(f"      Bowl MWPP distribution: {bowl_mwpp['mwpp'].describe().to_dict()}")

# ──────────────────── AGGREGATE RANKINGS ──────────────────────────
print("\n[6/6] Building v5 rankings...")

# ── BATTING RANKINGS ──
bat_agg = df.groupby(['striker_id', 'striker_name']).agg(
    balls=('valid_flag', 'sum'),
    runs=('runs', 'sum'),
    wkts_lost=('is_wicket', 'sum'),
    fours=('is_four', 'sum'),
    sixes=('is_six', 'sum'),
    dots=('valid_flag', lambda x: (df.loc[x.index, 'runs'] == 0).sum()),
    # HP-only stats
    hp_balls=('wpa_bat_v5', lambda x: (df.loc[x.index, 'is_high_pressure']==1).sum()),
    hp_runs=('runs', lambda x: x[df.loc[x.index,'is_high_pressure']==1].sum()),
    # WPA
    wpa_v5=('wpa_bat_v5', 'sum'),
    wpa_v4=('wpa_bat_v4', 'sum'),
    wpa_bat_raw=('wpa_batting', 'sum'),
    # Death-alive specifically
    da_wpa=('wpa_bat_v5', lambda x: x[(df.loc[x.index,'bucket_chase_death_alive']==1)].sum()),
    # Counter-attack
    ca_balls=('is_counter_attack_ball', 'sum'),
    ca_wpa=('wpa_bat_v5', lambda x: x[df.loc[x.index,'is_counter_attack_ball']].sum()),
    # Match importance
    imp_matches=('match_importance', lambda x: (x >= 1.4).sum()),
    seasons=('season', 'nunique'),
    matches=('match_id', 'nunique'),
).reset_index()

bat_agg['sr']           = bat_agg['runs'] / bat_agg['balls'] * 100
bat_agg['avg']          = bat_agg['runs'] / bat_agg['wkts_lost'].clip(lower=1)
bat_agg['hp_sr']        = bat_agg['hp_runs'] / bat_agg['hp_balls'].clip(lower=1) * 100
bat_agg['wpa_per_match']= bat_agg['wpa_v5'] / bat_agg['matches'].clip(lower=1)
bat_agg['dot_rate']     = bat_agg['dots'] / bat_agg['balls'].clip(lower=1)
bat_agg['boundary_rate']= (bat_agg['fours'] + bat_agg['sixes']) / bat_agg['balls'].clip(lower=1)

# Merge in MWPP and CA innings data
bat_agg = bat_agg.merge(bat_mwpp, on=['striker_id', 'striker_name'], how='left')
bat_agg['mwpp']           = bat_agg['mwpp'].fillna(0)
bat_agg['seasons_active'] = bat_agg['seasons_active'].fillna(bat_agg['seasons'])
bat_agg['ca_innings_total'] = bat_agg['ca_innings_total'].fillna(0)

# ── MIN ELIGIBILITY (batting) ──
# Minimum: 100+ HP balls, 5+ MWPP, 2+ seasons OR 20+ matches
bat_elig = bat_agg[
    (bat_agg['hp_balls'] >= 100) &
    (bat_agg['mwpp'] >= 5) &
    ((bat_agg['seasons'] >= 2) | (bat_agg['matches'] >= 20))
].copy()
print(f"      Eligible batters (hp>=100, mwpp>=5, 2+seasons): {len(bat_elig)}")

# ── BATTING SCORE ──
# Components (all min-max normalised within eligible pool):
def norm(s, lo=None, hi=None):
    lo = lo if lo is not None else s.min()
    hi = hi if hi is not None else s.max()
    return ((s - lo) / (hi - lo + 1e-9)).clip(0, 1) * 100

bat_elig['wpa_score']      = norm(bat_elig['wpa_v5'])          # overall HP WPA
bat_elig['sr_score']       = norm(bat_elig['hp_sr'])            # HP strike rate
bat_elig['da_score']       = norm(bat_elig['da_wpa'])           # death alive WPA
bat_elig['ca_score']       = norm(bat_elig['ca_wpa'])           # counter-attack WPA
bat_elig['mwpp_score']     = norm(bat_elig['mwpp'])             # match-winning perf count
bat_elig['consistency_score'] = norm(bat_elig['wpa_per_match']) # per-match contribution
bat_elig['boundary_score'] = norm(bat_elig['boundary_rate'])    # boundary hitting ability

# Choke penalty (from v4 carry-through — bat_choke columns in df)
bat_choke_agg = df.groupby('striker_id').agg(
    choke_events=('bat_choke_event', 'sum'),
    choke_wpa_total=('bat_choke_wpa', 'sum'),
).reset_index()
bat_elig = bat_elig.merge(bat_choke_agg, on='striker_id', how='left')
bat_elig['choke_events'] = bat_elig['choke_events'].fillna(0)
bat_elig['choke_wpa_total'] = bat_elig['choke_wpa_total'].fillna(0)
bat_elig['choke_penalty'] = norm(-bat_elig['choke_wpa_total'].clip(upper=0))  # higher choke → lower score

# Seasons consistency bonus: 3+ seasons → bonus
bat_elig['season_bonus'] = bat_elig['seasons'].clip(upper=5) / 5 * 15  # up to 15 pts

# FINAL BATTING CLUTCH SCORE
# Weights:
#   wpa_score        40% — primary performance metric
#   da_score         18% — death-alive (highest pressure)
#   ca_score         15% — counter-attack ability
#   mwpp_score       12% — match-winning consistency
#   sr_score          8% — HP strike rate
#   consistency_score 7% — per-match contribution
# Choke penalty: subtract up to 15 pts
# Season bonus: add up to 15 pts
bat_elig['batting_clutch_score'] = (
    bat_elig['wpa_score']        * 0.40 +
    bat_elig['da_score']         * 0.18 +
    bat_elig['ca_score']         * 0.15 +
    bat_elig['mwpp_score']       * 0.12 +
    bat_elig['sr_score']         * 0.08 +
    bat_elig['consistency_score']* 0.07 -
    bat_elig['choke_penalty']    * 0.10 +  # choke deducts up to 10 pts
    bat_elig['season_bonus']             # season consistency bonus
).clip(0, 100)

bat_elig = bat_elig.sort_values('batting_clutch_score', ascending=False).reset_index(drop=True)

# ── BOWLING RANKINGS ──
bowl_agg = df.groupby(['bowler_id', 'bowler_name']).agg(
    balls=('valid_flag', 'sum'),
    runs=('bowler_runs', 'sum'),
    wkts=('is_valid_wicket', 'sum'),
    dots=('valid_flag', lambda x: (df.loc[x.index, 'bowler_runs'] == 0).sum()),
    fours_con=('is_four', 'sum'),
    sixes_con=('is_six', 'sum'),
    # HP stats
    hp_balls=('wpa_bowl_v5', lambda x: (df.loc[x.index,'is_high_pressure']==1).sum()),
    hp_runs=('bowler_runs', lambda x: x[df.loc[x.index,'is_high_pressure']==1].sum()),
    hp_wkts=('is_valid_wicket', lambda x: x[df.loc[x.index,'is_high_pressure']==1].sum()),
    # WPA
    wpa_v5=('wpa_bowl_v5', 'sum'),
    wpa_v4=('wpa_bowl_v4', 'sum'),
    # Death-alive specifically
    da_wpa=('wpa_bowl_v5', lambda x: x[(df.loc[x.index,'bucket_chase_death_alive']==1)].sum()),
    # Shutdown
    shutdown_overs=('is_shutdown_over', 'sum'),
    elite_shutdown_overs=('is_elite_shutdown', 'sum'),
    shutdown_wpa=('wpa_bowl_v5', lambda x: x[df.loc[x.index,'is_shutdown_over']].sum()),
    # match importance
    seasons=('season', 'nunique'),
    matches=('match_id', 'nunique'),
    imp_matches=('match_importance', lambda x: (x >= 1.4).sum()),
).reset_index()

bowl_agg['economy']       = bowl_agg['runs'] / bowl_agg['balls'].clip(lower=1) * 6
bowl_agg['hp_economy']    = bowl_agg['hp_runs'] / bowl_agg['hp_balls'].clip(lower=1) * 6
bowl_agg['wkt_rate']      = bowl_agg['wkts'] / bowl_agg['balls'].clip(lower=1) * 6
bowl_agg['hp_wkt_rate']   = bowl_agg['hp_wkts'] / bowl_agg['hp_balls'].clip(lower=1) * 6
bowl_agg['wpa_per_match'] = bowl_agg['wpa_v5'] / bowl_agg['matches'].clip(lower=1)
bowl_agg['dot_rate']      = bowl_agg['dots'] / bowl_agg['balls'].clip(lower=1)

# Merge MWPP
bowl_agg = bowl_agg.merge(bowl_mwpp, on=['bowler_id', 'bowler_name'], how='left')
bowl_agg['mwpp']           = bowl_agg['mwpp'].fillna(0)
bowl_agg['seasons_active'] = bowl_agg['seasons_active'].fillna(bowl_agg['seasons'])

# ── MIN ELIGIBILITY (bowling) ──
# Minimum: 150+ HP balls, 4+ MWPP, 2+ seasons or 15+ matches
bowl_elig = bowl_agg[
    (bowl_agg['hp_balls'] >= 150) &
    (bowl_agg['mwpp'] >= 4) &
    ((bowl_agg['seasons'] >= 2) | (bowl_agg['matches'] >= 15))
].copy()
print(f"      Eligible bowlers (hp>=150, mwpp>=4, 2+seasons): {len(bowl_elig)}")

# ── BOWLING SCORE ──
bowl_elig['wpa_score']       = norm(bowl_elig['wpa_v5'])
bowl_elig['eco_score']       = norm(-bowl_elig['hp_economy'])    # lower eco = better
bowl_elig['wkt_score']       = norm(bowl_elig['hp_wkt_rate'])
bowl_elig['da_score']        = norm(bowl_elig['da_wpa'])
bowl_elig['shutdown_score']  = norm(bowl_elig['shutdown_wpa'])   # shutdown WPA
bowl_elig['elite_sd_score']  = norm(bowl_elig['elite_shutdown_overs'])
bowl_elig['mwpp_score']      = norm(bowl_elig['mwpp'])
bowl_elig['consistency_score']= norm(bowl_elig['wpa_per_match'])
bowl_elig['dot_score']       = norm(bowl_elig['dot_rate'])
bowl_elig['season_bonus']    = bowl_elig['seasons'].clip(upper=5) / 5 * 15

# Choke penalty for bowlers
bowl_choke_agg = df.groupby('bowler_id').agg(
    choke_events=('bowl_choke_event', 'sum'),
    choke_wpa_total=('bowl_choke_wpa', 'sum'),
).reset_index()
bowl_elig = bowl_elig.merge(bowl_choke_agg, on='bowler_id', how='left')
bowl_elig['choke_events']    = bowl_elig['choke_events'].fillna(0)
bowl_elig['choke_wpa_total'] = bowl_elig['choke_wpa_total'].fillna(0)
bowl_elig['choke_penalty']   = norm(-bowl_elig['choke_wpa_total'].clip(upper=0))

# FINAL BOWLING CLUTCH SCORE
# Weights:
#   wpa_score        35% — HP WPA
#   da_score         18% — death alive
#   shutdown_score   15% — shutdown WPA
#   wkt_score        12% — wicket rate in HP
#   eco_score         8% — HP economy
#   mwpp_score        7% — match-winning count
#   consistency_score 5% — per-match
# Choke: −10 pts max | Season bonus: +15 pts
bowl_elig['bowling_clutch_score'] = (
    bowl_elig['wpa_score']        * 0.35 +
    bowl_elig['da_score']         * 0.18 +
    bowl_elig['shutdown_score']   * 0.15 +
    bowl_elig['wkt_score']        * 0.12 +
    bowl_elig['eco_score']        * 0.08 +
    bowl_elig['mwpp_score']       * 0.07 +
    bowl_elig['consistency_score']* 0.05 -
    bowl_elig['choke_penalty']    * 0.10 +
    bowl_elig['season_bonus']
).clip(0, 100)

bowl_elig = bowl_elig.sort_values('bowling_clutch_score', ascending=False).reset_index(drop=True)

# ──────────────────── PRINT TOP 10 ──────────────────────────────
print("\n" + "=" * 60)
print("  TOP 10 BATTERS UNDER PRESSURE (v5)")
print("=" * 60)
bat10 = bat_elig.head(10)
for i, r in bat10.iterrows():
    print(f"  {i+1:2d}. {r['striker_name']:<22} Score={r['batting_clutch_score']:.1f} "
          f"| WPA={r['wpa_v5']:.2f} | DA-WPA={r['da_wpa']:.2f} | CA-WPA={r['ca_wpa']:.2f} "
          f"| MWPP={int(r['mwpp'])} | SR={r['sr']:.1f} | Seas={int(r['seasons'])}")

print()
print("=" * 60)
print("  TOP 10 BOWLERS UNDER PRESSURE (v5)")
print("=" * 60)
bowl10 = bowl_elig.head(10)
for i, r in bowl10.iterrows():
    print(f"  {i+1:2d}. {r['bowler_name']:<22} Score={r['bowling_clutch_score']:.1f} "
          f"| WPA={r['wpa_v5']:.2f} | DA-WPA={r['da_wpa']:.2f} | SD-WPA={r['shutdown_wpa']:.2f} "
          f"| MWPP={int(r['mwpp'])} | Eco={r['economy']:.2f} | Seas={int(r['seasons'])}")

# ──────────────────── SAVE ──────────────────────────────────────
print("\nSaving parquets...")
bat_elig.to_parquet('bat_rankings_v5.parquet', index=False)
bowl_elig.to_parquet('bowl_rankings_v5.parquet', index=False)

# Save enriched ball-by-ball for dashboard
df.to_parquet('valid_v5.parquet', index=False)

print("\nDone! Files saved:")
print("  bat_rankings_v5.parquet")
print("  bowl_rankings_v5.parquet")
print("  valid_v5.parquet")
