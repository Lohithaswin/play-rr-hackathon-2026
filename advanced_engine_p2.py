"""
Phase 3+4+5 — Clutch Scoring, Pressure Release/Shutdown, Final Rankings
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("Loading WPA-enriched data...")
df = pd.read_parquet('bbb_v2_wpa.parquet')
players = pd.read_csv('6af458274c1e8_data_pack/Data Pack/competition_team_player_mapping.csv')

valid = df[df['is_valid']].copy()

# ═══════════════════════════════════════════════════════
# PHASE 3 — PRESSURE CLASSIFICATION (TIGHTER)
# ═══════════════════════════════════════════════════════
print("\nPhase 3: Pressure classification via LI + context...")

# HIGH PRESSURE = High Leverage AND contextual pressure signals
# LI-based: top 30% leverage balls
LI_THRESHOLD = valid['leverage_index_norm'].quantile(0.70)
print(f"Leverage threshold (p70): {LI_THRESHOLD:.3f}")

# Context flags
valid['f_death']       = valid['overid'] >= 17
valid['f_pp_end']      = (valid['overid'].isin([5,6])) & (valid['innings']==1)
valid['f_high_rrr']    = valid['required_rr'] > 9
valid['f_quick_wkts']  = valid['recent_wickets_5'] >= 2
valid['f_dot_pileup']  = valid['recent_dots_5'] >= 3
valid['f_big_chase']   = (valid['innings']==2) & (valid['target'] >= 185)
valid['f_knockout']    = valid['is_knockout'] == 1
valid['f_collapse']    = (valid['wickets_remaining'] <= 3) & (valid['overid'] >= 15)

# Any contextual flag
valid['ctx_flags'] = (
    valid['f_death'].astype(int) +
    valid['f_pp_end'].astype(int) +
    valid['f_high_rrr'].astype(int) +
    valid['f_quick_wkts'].astype(int) +
    valid['f_dot_pileup'].astype(int) +
    valid['f_big_chase'].astype(int) +
    valid['f_knockout'].astype(int) +
    valid['f_collapse'].astype(int)
)

# PRESSURE = high leverage AND at least 1 context flag
valid['is_high_pressure'] = (
    (valid['leverage_index_norm'] >= LI_THRESHOLD) &
    (valid['ctx_flags'] >= 1)
)

# SUPER PRESSURE = top 15% LI + 2+ context flags (most critical moments)
LI_SUPER = valid['leverage_index_norm'].quantile(0.85)
valid['is_super_pressure'] = (
    (valid['leverage_index_norm'] >= LI_SUPER) &
    (valid['ctx_flags'] >= 2)
)

n_hi  = valid['is_high_pressure'].sum()
n_sup = valid['is_super_pressure'].sum()
print(f"High-pressure balls: {n_hi:,} ({n_hi/len(valid)*100:.1f}%)")
print(f"Super-pressure balls: {n_sup:,} ({n_sup/len(valid)*100:.1f}%)")

# ── PRESSURE RELEASE SIGNAL (for batters)
# A ball is a "pressure release" if:
#   - 3+ dots in last 5 balls OR wicket in last 3 balls
#   - AND batter hits 4+ on this ball
valid['recent_wicket_3'] = (
    valid.groupby(['match_id','innings'], group_keys=False)
    .apply(lambda g: g['is_valid_wicket'].astype(int).rolling(3,min_periods=1).sum().shift(1).fillna(0))
)
valid['under_dot_stress'] = (valid['recent_dots_5'] >= 3) | (valid['recent_wicket_3'] >= 1)
valid['is_pressure_release'] = (
    valid['under_dot_stress'] &
    (valid['total_ball_runs'] >= 4) &
    valid['is_high_pressure']
)

# ── SHUTDOWN OVER SIGNAL (for bowlers)
# Bowler concedes ≤5 runs in an over where the recent average over RR was >9
# Collect over-level data
over_stats = (valid.groupby(['match_id','innings','overid','bowler_id','bowler_name'])
              .agg(
                  over_runs=('total_ball_runs','sum'),
                  over_balls=('is_valid','sum'),
                  over_wickets=('is_valid_wicket','sum'),
                  recent_avg_rr=('recent_avg_rr','first'),
                  leverage_mean=('leverage_index_norm','mean'),
                  batting_team_won=('batting_team_won','first'),
                  is_knockout=('is_knockout','first'),
              ).reset_index())
over_stats['over_economy'] = over_stats['over_runs'] / over_stats['over_balls'] * 6
# Shutdown = recent 2-over RR was hot (>9) but this over conceded ≤6
over_stats['is_shutdown_over'] = (
    (over_stats['recent_avg_rr'] >= 9) &
    (over_stats['over_economy'] <= 6) &
    (over_stats['over_balls'] >= 5)
)
print(f"\nShutdown overs: {over_stats['is_shutdown_over'].sum():,}")

# ═══════════════════════════════════════════════════════
# PHASE 4 — PLAYER SCORING
# ═══════════════════════════════════════════════════════
print("\nPhase 4: Computing player scores...")

# ── ELIGIBILITY
MIN_PRESSURE_BALLS_BAT  = 100
MIN_PRESSURE_BALLS_BOWL = 80

# ─────────────────────────────────────────────
# 4A. BATTING
# ─────────────────────────────────────────────

hi_press = valid[valid['is_high_pressure']].copy()
sup_press = valid[valid['is_super_pressure']].copy()
normal = valid[valid['leverage_index_norm'] < valid['leverage_index_norm'].quantile(0.30)].copy()
p_release = valid[valid['is_pressure_release']].copy()

def bat_metrics(balls_df, min_qual=0):
    g = balls_df.groupby(['striker_id','striker_name'])
    res = g.agg(
        balls=('runs','count'),
        runs=('runs','sum'),
        fours=('is_four','sum'),
        sixes=('is_six','sum'),
        dots=('runs', lambda x: (x==0).sum()),
        wkts_lost=('is_valid_wicket','sum'),
        wpa_sum=('wpa_batting','sum'),
        wpa_mean=('wpa_batting','mean'),
        avg_li=('leverage_index_norm','mean'),
        win_balls=('batting_team_won','sum'),  # balls played in games team won
    ).reset_index()
    res['sr'] = res['runs'] / res['balls'] * 100
    res['avg'] = res['runs'] / res['wkts_lost'].replace(0, np.nan)
    res['dot_pct'] = res['dots'] / res['balls'] * 100
    res['bdry_pct'] = (res['fours'] + res['sixes']) / res['balls'] * 100
    res['win_contrib_pct'] = res['win_balls'] / res['balls'] * 100
    if min_qual:
        res = res[res['balls'] >= min_qual]
    return res

bat_hi   = bat_metrics(hi_press, MIN_PRESSURE_BALLS_BAT)
bat_sup  = bat_metrics(sup_press, 20)
bat_norm = bat_metrics(normal, 20)

# WPA-based clutch: total WPA in high-leverage situations
bat_wpa_clutch = hi_press.groupby(['striker_id','striker_name']).agg(
    clutch_wpa=('wpa_batting','sum'),
    clutch_wpa_mean=('wpa_batting','mean'),
).reset_index()

# Pressure release moments
bat_release = p_release.groupby(['striker_id','striker_name']).agg(
    release_moments=('is_pressure_release','sum'),
    release_runs=('total_ball_runs','sum'),
).reset_index()

# Super pressure performance
bat_super = bat_metrics(sup_press, 10)
bat_super = bat_super[['striker_id','striker_name','sr','avg','wpa_mean']].rename(
    columns={'sr':'sr_super','avg':'avg_super','wpa_mean':'wpa_super'})

# Merge
bat = bat_hi.merge(bat_norm[['striker_id','striker_name','sr','avg','dot_pct']].rename(
    columns={'sr':'sr_base','avg':'avg_base','dot_pct':'dot_pct_base'}),
    on=['striker_id','striker_name'], how='left')
bat = bat.merge(bat_wpa_clutch, on=['striker_id','striker_name'], how='left')
bat = bat.merge(bat_release, on=['striker_id','striker_name'], how='left')
bat = bat.merge(bat_super,   on=['striker_id','striker_name'], how='left')

bat['release_moments'] = bat['release_moments'].fillna(0)

print(f"Eligible batters (>={MIN_PRESSURE_BALLS_BAT} pressure balls): {len(bat)}")

# ── COMPOSITE BATTING SCORE
# 1. Clutch WPA (most important)
# 2. Strike rate under pressure vs baseline ratio
# 3. Average under pressure
# 4. Pressure release moments per 50 balls
# 5. Win contribution ratio

bat['sr_ratio'] = (bat['sr'] / bat['sr_base'].replace(0,np.nan)).clip(0, 2.5)
bat['avg_ratio'] = (bat['avg'] / bat['avg_base'].replace(0,np.nan)).clip(0, 2.5)

# Normalise WPA per ball (central metric)
wpa_max_bat = bat['clutch_wpa_mean'].quantile(0.95)
bat['wpa_score'] = (bat['clutch_wpa_mean'] / wpa_max_bat * 100).clip(-50, 100)

# SR under pressure, normalised to 180 as elite T20 mark
bat['sr_score'] = (bat['sr'] / 180 * 100).clip(0, 100)

# Clutch ratio vs baseline
bat['ratio_score'] = ((bat['sr_ratio'] + bat['avg_ratio']) / 2 * 50).clip(0, 100)

# Pressure release bonus
bat['release_per_50'] = bat['release_moments'] / bat['balls'] * 50
bat['release_score'] = (bat['release_per_50'] * 10).clip(0, 25)

# Win contribution: played more balls in winning contexts
bat['win_score'] = (bat['win_contrib_pct'] - 50).clip(-25, 25)  # centre at 50%

# Volume / reliability adjustment (more balls = more reliable)
bat['vol_adj'] = np.minimum(bat['balls'] / 300, 1.0)

bat['raw_bat_score'] = (
    0.35 * bat['wpa_score'].fillna(0) +
    0.25 * bat['sr_score'] +
    0.20 * bat['ratio_score'].fillna(50) +
    0.12 * bat['release_score'] +
    0.08 * bat['win_score'].fillna(0)
)
bat['batting_clutch_score'] = (bat['raw_bat_score'] * bat['vol_adj']).clip(0, 100)

bat_top = bat.sort_values('batting_clutch_score', ascending=False).head(20)

print("\nTop 20 Batters:")
print(bat_top[['striker_name','balls','runs','sr','avg','sr_base','sr_ratio',
               'clutch_wpa','clutch_wpa_mean','release_moments','batting_clutch_score']].to_string(index=False))

# ─────────────────────────────────────────────
# 4B. BOWLING
# ─────────────────────────────────────────────

def bowl_metrics(balls_df, min_qual=0):
    g = balls_df.groupby(['bowler_id','bowler_name'])
    res = g.agg(
        balls=('runs','count'),
        runs=('bowler_runs','sum'),
        wkts=('is_valid_wicket','sum'),
        dots=('runs', lambda x: (x==0).sum()),
        fours_con=('is_four','sum'),
        sixes_con=('is_six','sum'),
        wpa_sum=('wpa_bowling','sum'),
        wpa_mean=('wpa_bowling','mean'),
        avg_li=('leverage_index_norm','mean'),
        win_balls=('batting_team_won', lambda x: (x==0).sum()),  # balls where bowler's team won
    ).reset_index()
    res['economy'] = res['runs'] / res['balls'] * 6
    res['bowl_avg'] = res['runs'] / res['wkts'].replace(0, np.nan)
    res['bowl_sr'] = res['balls'] / res['wkts'].replace(0, np.nan)
    res['dot_pct'] = res['dots'] / res['balls'] * 100
    res['bdry_conceded_pct'] = (res['fours_con'] + res['sixes_con']) / res['balls'] * 100
    res['wkt_pct'] = res['wkts'] / res['balls'] * 100
    if min_qual:
        res = res[res['balls'] >= min_qual]
    return res

bowl_hi   = bowl_metrics(hi_press, MIN_PRESSURE_BALLS_BOWL)
bowl_norm = bowl_metrics(normal, 20)

bowl_wpa_clutch = hi_press.groupby(['bowler_id','bowler_name']).agg(
    clutch_wpa=('wpa_bowling','sum'),
    clutch_wpa_mean=('wpa_bowling','mean'),
).reset_index()

# Shutdown over credit
shutdown_credit = over_stats[over_stats['is_shutdown_over']].groupby(['bowler_id','bowler_name']).agg(
    shutdown_overs=('is_shutdown_over','sum'),
    shutdown_wkts=('over_wickets','sum'),
    shutdown_runs=('over_runs','sum'),
).reset_index()

bowl = bowl_hi.merge(bowl_norm[['bowler_id','bowler_name','economy','dot_pct']].rename(
    columns={'economy':'eco_base','dot_pct':'dot_pct_base'}),
    on=['bowler_id','bowler_name'], how='left')
bowl = bowl.merge(bowl_wpa_clutch, on=['bowler_id','bowler_name'], how='left')
bowl = bowl.merge(shutdown_credit, on=['bowler_id','bowler_name'], how='left')

bowl['shutdown_overs'] = bowl['shutdown_overs'].fillna(0)

print(f"\nEligible bowlers (>={MIN_PRESSURE_BALLS_BOWL} pressure balls): {len(bowl)}")

# ── COMPOSITE BOWLING SCORE
bowl['eco_ratio'] = (bowl['eco_base'] / bowl['economy'].replace(0,np.nan)).clip(0, 2.5)
bowl['dot_ratio'] = (bowl['dot_pct'] / bowl['dot_pct_base'].replace(0,np.nan)).clip(0, 2.5)

wpa_max_bowl = bowl['clutch_wpa_mean'].quantile(0.95)
bowl['wpa_score'] = (bowl['clutch_wpa_mean'] / wpa_max_bowl * 100).clip(-50, 100)

# Economy under pressure (lower = better)
bowl['eco_score'] = ((1 - bowl['economy'] / 15) * 100).clip(0, 100)

# Wicket % under pressure
bowl['wkt_score'] = (bowl['wkt_pct'] * 15).clip(0, 100)

# Dot % under pressure
bowl['dot_score'] = bowl['dot_pct'].clip(0, 70)

# Eco ratio vs baseline
bowl['ratio_score'] = ((bowl['eco_ratio'] + bowl['dot_ratio']) / 2 * 50).clip(0, 100)

# Shutdown over bonus
bowl['shutdown_per_10'] = bowl['shutdown_overs'] / bowl['balls'] * 60
bowl['shutdown_score'] = (bowl['shutdown_per_10'] * 10).clip(0, 25)

# Volume adjustment
bowl['vol_adj'] = np.minimum(bowl['balls'] / 250, 1.0)

bowl['raw_bowl_score'] = (
    0.35 * bowl['wpa_score'].fillna(0) +
    0.25 * bowl['eco_score'] +
    0.15 * bowl['wkt_score'] +
    0.10 * bowl['dot_score'] / 70 * 100 +
    0.10 * bowl['ratio_score'].fillna(50) +
    0.05 * bowl['shutdown_score']
)
bowl['bowling_clutch_score'] = (bowl['raw_bowl_score'] * bowl['vol_adj']).clip(0, 100)

bowl_top = bowl.sort_values('bowling_clutch_score', ascending=False).head(20)

print("\nTop 20 Bowlers:")
print(bowl_top[['bowler_name','balls','wkts','economy','dot_pct','eco_base',
                'clutch_wpa','clutch_wpa_mean','shutdown_overs','bowling_clutch_score']].to_string(index=False))

# ═══════════════════════════════════════════════════════
# PHASE 5 — FINAL TOP 10
# ═══════════════════════════════════════════════════════
print("\n" + "="*60)
print("FINAL RANKINGS")
print("="*60)

print("\nTOP 10 BATTERS UNDER PRESSURE:")
for i, row in bat_top.head(10).reset_index(drop=True).iterrows():
    print(f"  #{i+1:2d}: {row['striker_name']:<28} | Balls={int(row['balls']):<4} | "
          f"SR(P)={row['sr']:.1f} | Avg(P)={row['avg']:.1f} | "
          f"WPA={row['clutch_wpa']:.3f} | Releases={int(row['release_moments'])} | "
          f"Score={row['batting_clutch_score']:.2f}")

print("\nTOP 10 BOWLERS UNDER PRESSURE:")
for i, row in bowl_top.head(10).reset_index(drop=True).iterrows():
    print(f"  #{i+1:2d}: {row['bowler_name']:<28} | Balls={int(row['balls']):<4} | "
          f"Eco(P)={row['economy']:.2f} | Wkts={int(row['wkts'])} | "
          f"WPA={row['clutch_wpa']:.3f} | Shutdowns={int(row['shutdown_overs'])} | "
          f"Score={row['bowling_clutch_score']:.2f}")

# Save
bat.to_parquet('bat_rankings_v2.parquet', index=False)
bowl.to_parquet('bowl_rankings_v2.parquet', index=False)
valid.to_parquet('valid_v2.parquet', index=False)
print("\nSaved all rankings.")
