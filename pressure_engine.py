"""
SupeRR Selector Season 2 — Pressure Performance Engine
=======================================================
Identifies pressure situations ball-by-ball and computes
batter/bowler performance ratings under pressure vs baseline.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = r"6af458274c1e8_data_pack/Data Pack"

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────

print("Loading data...")
bbb = pd.read_csv(f"{DATA_DIR}/ball_by_ball.csv")
matches = pd.read_csv(f"{DATA_DIR}/matches.csv")
comps = pd.read_csv(f"{DATA_DIR}/competitions.csv")
players = pd.read_csv(f"{DATA_DIR}/competition_team_player_mapping.csv")

# Keep only T20 innings (1 or 2)
bbb = bbb[bbb['innings'].isin([1, 2])].copy()

# Merge match and competition context
bbb = bbb.merge(
    matches[['match_id', 'comp_id', 'stage', 'knock_out',
             'home_team_id', 'away_team_id', 'win_team_id']],
    on='match_id', how='left'
)
bbb = bbb.merge(comps[['comp_id', 'match_format', 'season']], on='comp_id', how='left')

# Flag legit deliveries (not wide or no-ball/overstep)
bbb['is_valid_ball'] = ~bbb['extras_type'].isin(['wide', 'Overstep'])
print(f"Total deliveries: {len(bbb):,}  |  Valid: {bbb['is_valid_ball'].sum():,}")

# ─────────────────────────────────────────────
# 2. COMPUTE CUMULATIVE MATCH STATE
# ─────────────────────────────────────────────

print("Computing cumulative match state...")

# Sort properly
bbb = bbb.sort_values(['match_id', 'innings', 'innings_ball_num']).reset_index(drop=True)

# Runs scored from valid balls (bat + running extras) for scoring purposes
bbb['bat_runs'] = bbb['runs']
# byes/legbyes don't count against bowler but count towards total
bbb['bowler_runs'] = np.where(bbb['extras_type'].isin(['byes', 'legbyes']), 0,
                               bbb['runs'] + bbb['extras1_runs'])

# Wicket flag (run-outs sometimes don't have wicket ball)
bbb['is_valid_wicket'] = bbb['is_wicket'] & ~bbb['dismissal_type'].isin(['RetiredHurt'])

# Cumulative wickets fallen in innings
bbb['cum_wickets'] = bbb.groupby(['match_id', 'innings'])['is_valid_wicket'].cumsum()
# Shift so cum_wickets is state BEFORE this ball
bbb['wickets_before'] = bbb.groupby(['match_id', 'innings'])['is_valid_wicket'].transform(lambda x: x.shift(1)).fillna(0).cumsum().astype(int)

# Cumulative valid balls in innings
bbb['valid_ball_flag'] = bbb['is_valid_ball'].astype(int)
bbb['cum_valid_balls'] = bbb.groupby(['match_id', 'innings'])['valid_ball_flag'].cumsum()
bbb['valid_balls_before'] = bbb.groupby(['match_id', 'innings'])['valid_ball_flag'].transform(lambda x: x.shift(1).fillna(0).cumsum()).astype(int)

# Cumulative innings runs
bbb['runs_before'] = bbb.groupby(['match_id', 'innings'])['runs'].transform(lambda x: x.shift(1).fillna(0).cumsum()) + \
                     bbb.groupby(['match_id', 'innings'])['extras1_runs'].transform(lambda x: x.shift(1).fillna(0).cumsum())

# Balls remaining in innings (assume 120 valid balls per innings unless D/L)
bbb['balls_remaining'] = 120 - bbb['valid_balls_before']
bbb['balls_remaining'] = bbb['balls_remaining'].clip(lower=1)

# Wickets remaining (10 total)
bbb['wickets_remaining'] = 10 - bbb['wickets_before']

# ─────────────────────────────────────────────
# 3. BUILD CHASE CONTEXT (innings 2)
# ─────────────────────────────────────────────

print("Building chase context (inn2)...")

# Total first innings score per match
inn1_totals = (bbb[bbb['innings'] == 1]
               .groupby('match_id')
               .agg(inn1_runs=('runs', 'sum'), inn1_extras=('extras1_runs', 'sum'))
               .reset_index())
inn1_totals['target'] = inn1_totals['inn1_runs'] + inn1_totals['inn1_extras'] + 1

bbb = bbb.merge(inn1_totals[['match_id', 'target']], on='match_id', how='left')

# For innings 2: runs_needed and required run rate
bbb['runs_needed'] = np.where(
    bbb['innings'] == 2,
    (bbb['target'] - bbb['runs_before']).clip(lower=0),
    np.nan
)
bbb['required_rr'] = np.where(
    bbb['innings'] == 2,
    bbb['runs_needed'] * 6 / bbb['balls_remaining'],
    np.nan
)
# Current run rate in chase
bbb['current_rr'] = np.where(
    (bbb['innings'] == 2) & (bbb['valid_balls_before'] > 0),
    bbb['runs_before'] * 6 / bbb['valid_balls_before'],
    np.nan
)
# Pressure gap: how much RRR exceeds CRR
bbb['rr_gap'] = np.where(
    bbb['innings'] == 2,
    bbb['required_rr'] - bbb['current_rr'].fillna(0),
    np.nan
)

# ─────────────────────────────────────────────
# 4. PRESSURE SITUATION IDENTIFICATION
# ─────────────────────────────────────────────
# Multi-factor composite pressure index (0–100 scale)
# Each component contributes independently and they're combined.

print("Computing pressure index...")

# Component weights
W_POWERPLAY_END  = 15   # Last 2 overs of powerplay (overs 5-6)
W_QUICK_WICKETS  = 25   # Multiple wickets in rapid succession
W_DOT_PRESSURE   = 15   # Pileup of dot balls
W_DEATH_OVERS    = 20   # Death overs (17-20), always pressure
W_CHASE_RRR      = 20   # Required run rate pressure in chase
W_CHASE_BIG_HUNT = 10   # Chasing a large total from ball 1
W_KNOCKOUT       = 10   # Knockout match bonus (applied separately)

# 4a. Powerplay end pressure (overs 5-6)
bbb['pp_end_pressure'] = np.where(
    (bbb['overid'].isin([5, 6])) & (bbb['innings'] == 1),
    W_POWERPLAY_END, 0
)

# 4b. Quick wickets pressure — 3+ wickets in last 30 valid balls
# Rolling wickets in last 30 balls per innings
bbb_sorted = bbb.copy()

def rolling_wickets(group, window=30):
    return group['is_valid_wicket'].rolling(window, min_periods=1).sum().shift(1).fillna(0)

bbb_sorted['recent_wickets'] = (
    bbb_sorted.groupby(['match_id', 'innings'], group_keys=False)
    .apply(rolling_wickets)
)
bbb_sorted['quick_wicket_pressure'] = np.where(
    bbb_sorted['recent_wickets'] >= 3,
    W_QUICK_WICKETS,
    np.where(bbb_sorted['recent_wickets'] >= 2, W_QUICK_WICKETS * 0.5, 0)
)

# 4c. Dot ball pile-up — 4+ consecutive dots
def rolling_dots(group, window=5):
    is_dot = (group['runs'] == 0) & (group['is_valid_ball'])
    return is_dot.rolling(window, min_periods=1).sum().shift(1).fillna(0)

bbb_sorted['recent_dots'] = (
    bbb_sorted.groupby(['match_id', 'innings'], group_keys=False)
    .apply(rolling_dots)
)
bbb_sorted['dot_pressure'] = np.where(
    bbb_sorted['recent_dots'] >= 4,
    W_DOT_PRESSURE,
    np.where(bbb_sorted['recent_dots'] >= 3, W_DOT_PRESSURE * 0.5, 0)
)

# 4d. Death overs (17-20)
bbb_sorted['death_pressure'] = np.where(
    bbb_sorted['overid'] >= 17,
    W_DEATH_OVERS, 0
)

# 4e. Chase RRR pressure
# High RRR: >10 is extreme, >9 is high, >8 is moderate
bbb_sorted['chase_rrr_pressure'] = pd.array(np.where(
    bbb_sorted['required_rr'] > 12,
    W_CHASE_RRR * 1.5,
    np.where(bbb_sorted['required_rr'] > 10,
             W_CHASE_RRR * 1.2,
             np.where(bbb_sorted['required_rr'] > 9,
                      W_CHASE_RRR,
                      np.where(bbb_sorted['required_rr'] > 8,
                               W_CHASE_RRR * 0.6, 0)))
), dtype=float)
bbb_sorted['chase_rrr_pressure'] = bbb_sorted['chase_rrr_pressure'].fillna(0)

# 4f. Big total chase pressure from ball 1 (target > 185)
bbb_sorted['big_chase_pressure'] = np.where(
    (bbb_sorted['innings'] == 2) & (bbb_sorted['target'] >= 185),
    W_CHASE_BIG_HUNT, 0
)

# 4g. Knockout match bonus
bbb_sorted['knockout_pressure'] = np.where(
    bbb_sorted['knock_out'] == 1,
    W_KNOCKOUT,
    np.where(bbb_sorted['stage'].isin(['Final', 'Semi Final', 'Qualifier', 'Eliminator']),
             W_KNOCKOUT * 0.8, 0)
)

# 4h. Innings-critical: low wickets remaining in death
bbb_sorted['collapse_pressure'] = np.where(
    (bbb_sorted['overid'] >= 15) & (bbb_sorted['wickets_remaining'] <= 3),
    15,
    np.where((bbb_sorted['overid'] >= 10) & (bbb_sorted['wickets_remaining'] <= 2), 10, 0)
)

# ── Composite Pressure Index (capped at 100)
bbb_sorted['pressure_index'] = (
    bbb_sorted['pp_end_pressure'] +
    bbb_sorted['quick_wicket_pressure'] +
    bbb_sorted['dot_pressure'] +
    bbb_sorted['death_pressure'] +
    bbb_sorted['chase_rrr_pressure'] +
    bbb_sorted['big_chase_pressure'] +
    bbb_sorted['knockout_pressure'] +
    bbb_sorted['collapse_pressure']
).clip(upper=100)

# Binary pressure flag: index >= 20
bbb_sorted['is_pressure'] = bbb_sorted['pressure_index'] >= 20

print(f"\nPressure situation stats:")
print(f"  Total valid balls: {bbb_sorted['is_valid_ball'].sum():,}")
print(f"  Pressure balls (PI>=20): {bbb_sorted[bbb_sorted['is_pressure'] & bbb_sorted['is_valid_ball']].shape[0]:,}")
print(f"  % under pressure: {bbb_sorted[bbb_sorted['is_pressure'] & bbb_sorted['is_valid_ball']].shape[0] / bbb_sorted['is_valid_ball'].sum() * 100:.1f}%")
print(f"\nPressure Index distribution:")
print(bbb_sorted['pressure_index'].describe())

# Save enriched dataset
bbb_sorted.to_parquet('bbb_enriched.parquet', index=False)
print("\nSaved bbb_enriched.parquet")
