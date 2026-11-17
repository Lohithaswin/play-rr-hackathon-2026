"""
SupeRR Selector Season 2 — Advanced Win Probability + Clutch Engine
====================================================================
Phase 1: Compute ball-by-ball match state features
Phase 2: Train LightGBM Win Probability model
Phase 3: Compute WPA, Leverage Index, Pressure Release / Shutdown signals
Phase 4: Score batters & bowlers with outcome-weighted clutch metrics
Phase 5: Produce final Top 10 rankings
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = r"6af458274c1e8_data_pack/Data Pack"

# ═══════════════════════════════════════════════════════
# PHASE 1 — LOAD & ENGINEER MATCH STATE
# ═══════════════════════════════════════════════════════
print("=" * 60)
print("PHASE 1: Loading and engineering match state")
print("=" * 60)

bbb     = pd.read_csv(f"{DATA_DIR}/ball_by_ball.csv")
matches = pd.read_csv(f"{DATA_DIR}/matches.csv")
comps   = pd.read_csv(f"{DATA_DIR}/competitions.csv")
players = pd.read_csv(f"{DATA_DIR}/competition_team_player_mapping.csv")

# Keep only T20 innings 1 & 2
bbb = bbb[bbb['innings'].isin([1, 2])].copy()
bbb = bbb.merge(
    matches[['match_id','comp_id','stage','knock_out','win_team_id','result']],
    on='match_id', how='left'
)
bbb = bbb.merge(comps[['comp_id','match_format','season']], on='comp_id', how='left')

# Drop matches with no result (abandoned)
bbb = bbb[bbb['win_team_id'].notna()].copy()
bbb['win_team_id'] = bbb['win_team_id'].astype(int)

# Valid deliveries (not wide or no-ball)
bbb['is_valid'] = ~bbb['extras_type'].isin(['wide', 'Overstep'])
bbb['is_valid_wicket'] = bbb['is_wicket'] & ~bbb['dismissal_type'].isin(['RetiredHurt'])

# Runs for batting team (all runs including extras)
bbb['total_ball_runs'] = bbb['runs'] + bbb['extras1_runs'].fillna(0)
# Runs charged to bowler
bbb['bowler_runs'] = np.where(
    bbb['extras_type'].isin(['byes','legbyes']), bbb['extras1_runs'].fillna(0),
    bbb['total_ball_runs']
)

bbb = bbb.sort_values(['match_id','innings','innings_ball_num']).reset_index(drop=True)

# ── Cumulative state (all balls, then valid-ball-indexed)
bbb['valid_flag'] = bbb['is_valid'].astype(int)
bbb['valid_balls_cum'] = bbb.groupby(['match_id','innings'])['valid_flag'].transform('cumsum')
# "Before this ball" = shift(1)
bbb['valid_balls_before'] = (
    bbb.groupby(['match_id','innings'])['valid_flag']
    .transform(lambda x: x.shift(1).fillna(0).cumsum()).astype(int)
)

bbb['runs_cum'] = (
    bbb.groupby(['match_id','innings'])['total_ball_runs']
    .transform('cumsum')
)
bbb['runs_before'] = (
    bbb.groupby(['match_id','innings'])['total_ball_runs']
    .transform(lambda x: x.shift(1).fillna(0).cumsum())
)

bbb['wickets_cum'] = (
    bbb.groupby(['match_id','innings'])['is_valid_wicket']
    .transform('cumsum')
)
bbb['wickets_before'] = (
    bbb.groupby(['match_id','innings'])['is_valid_wicket']
    .transform(lambda x: x.shift(1).fillna(0).cumsum()).astype(int)
)

# Balls & wickets remaining
bbb['balls_remaining'] = (120 - bbb['valid_balls_before']).clip(lower=1)
bbb['wickets_remaining'] = (10 - bbb['wickets_before']).clip(lower=0)

# ── Innings 1 totals → target for innings 2
inn1 = (bbb[bbb['innings'] == 1]
        .groupby('match_id')
        .agg(inn1_total=('total_ball_runs','sum'))
        .reset_index())
inn1['target'] = inn1['inn1_total'] + 1
bbb = bbb.merge(inn1[['match_id','target']], on='match_id', how='left')

# Chase variables
bbb['runs_needed'] = np.where(bbb['innings']==2,
    (bbb['target'] - bbb['runs_before']).clip(lower=0), np.nan)
bbb['required_rr'] = np.where(
    (bbb['innings']==2) & (bbb['balls_remaining'] > 0),
    bbb['runs_needed'] * 6 / bbb['balls_remaining'], np.nan)
bbb['current_rr'] = np.where(
    bbb['valid_balls_before'] > 0,
    bbb['runs_before'] * 6 / bbb['valid_balls_before'], 0.0)
bbb['rr_gap'] = (bbb['required_rr'] - bbb['current_rr']).fillna(0)

# Match outcome: did the batting team on this ball win?
bbb['batting_team_won'] = (bbb['batting_team_id'] == bbb['win_team_id']).astype(int)

# Is knockout / high-stakes
bbb['is_knockout'] = ((bbb['knock_out'] == 1) |
    bbb['stage'].isin(['Final','Semi Final','Qualifier','Eliminator'])).astype(int)

print(f"Deliveries after cleaning: {len(bbb):,}  |  Matches: {bbb['match_id'].nunique()}")

# ─── ROLLING MATCH CONTEXT (for shutdown / pressure-release)
# Run rate of last 2 overs by the opposition (for bowlers)
valid_only = bbb[bbb['is_valid']].copy()

# Per-over run rate in each innings
over_rr = (valid_only.groupby(['match_id','innings','overid'])
            .agg(over_runs=('total_ball_runs','sum'), over_balls=('valid_flag','sum'))
            .reset_index())
over_rr['over_rr'] = over_rr['over_runs'] / over_rr['over_balls'] * 6
# Previous over run rate (shifted by 1 over)
over_rr['prev_over_rr'] = over_rr.groupby(['match_id','innings'])['over_rr'].shift(1)
over_rr['prev2_over_rr'] = over_rr.groupby(['match_id','innings'])['over_rr'].shift(2)
over_rr['recent_avg_rr'] = over_rr[['prev_over_rr','prev2_over_rr']].mean(axis=1)

bbb = bbb.merge(over_rr[['match_id','innings','overid','over_rr','recent_avg_rr']],
                on=['match_id','innings','overid'], how='left')

# Rolling: last 5 valid balls - dots and wickets (for pressure-release detection)
def rolling_n(group, col, func, n=5):
    return group[col].rolling(n, min_periods=1).apply(func, raw=True).shift(1).fillna(0)

bbb['recent_dots_5'] = (
    bbb.groupby(['match_id','innings'], group_keys=False)
    .apply(lambda g: (g['runs'] == 0).astype(int).rolling(5, min_periods=1).sum().shift(1).fillna(0))
)
bbb['recent_wickets_5'] = (
    bbb.groupby(['match_id','innings'], group_keys=False)
    .apply(lambda g: g['is_valid_wicket'].astype(int).rolling(5, min_periods=1).sum().shift(1).fillna(0))
)
bbb['recent_runs_12'] = (
    bbb.groupby(['match_id','innings'], group_keys=False)
    .apply(lambda g: g['total_ball_runs'].rolling(12, min_periods=1).sum().shift(1).fillna(0))
)

bbb.to_parquet('bbb_v2.parquet', index=False)
print("Saved bbb_v2.parquet\n")

# ═══════════════════════════════════════════════════════
# PHASE 2 — WIN PROBABILITY MODEL (LightGBM)
# ═══════════════════════════════════════════════════════
print("=" * 60)
print("PHASE 2: Training Win Probability Model")
print("=" * 60)

import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss

# Features for WP model
# Inn 1: predict if the BATTING team (team batting first) wins
# Inn 2: predict if the BATTING team (chasing team) wins
# We train separate models for each innings

FEATURES_INN1 = [
    'overid', 'valid_balls_before', 'balls_remaining',
    'wickets_remaining', 'wickets_before',
    'runs_before', 'current_rr',
    'is_knockout',
]
FEATURES_INN2 = [
    'overid', 'valid_balls_before', 'balls_remaining',
    'wickets_remaining', 'wickets_before',
    'runs_before', 'runs_needed', 'required_rr', 'current_rr', 'rr_gap',
    'is_knockout', 'target',
]

bbb_v2 = bbb.copy()

# ── INN1 MODEL
inn1_df = bbb_v2[bbb_v2['innings'] == 1].dropna(subset=['batting_team_won'])
X1 = inn1_df[FEATURES_INN1].fillna(0)
y1 = inn1_df['batting_team_won']
X1_tr, X1_va, y1_tr, y1_va = train_test_split(X1, y1, test_size=0.2, random_state=42)

params = dict(
    objective='binary', metric='auc', learning_rate=0.05,
    num_leaves=63, n_estimators=400, min_child_samples=20,
    feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=5,
    verbose=-1
)
model_inn1 = lgb.LGBMClassifier(**params)
model_inn1.fit(X1_tr, y1_tr,
               eval_set=[(X1_va, y1_va)],
               callbacks=[lgb.early_stopping(30, verbose=False)])

auc1 = roc_auc_score(y1_va, model_inn1.predict_proba(X1_va)[:,1])
bs1  = brier_score_loss(y1_va, model_inn1.predict_proba(X1_va)[:,1])
print(f"Inn1 WP Model — AUC: {auc1:.4f}  |  Brier: {bs1:.4f}")

# ── INN2 MODEL
inn2_df = bbb_v2[bbb_v2['innings'] == 2].dropna(subset=['batting_team_won','runs_needed'])
X2 = inn2_df[FEATURES_INN2].fillna(0)
y2 = inn2_df['batting_team_won']
X2_tr, X2_va, y2_tr, y2_va = train_test_split(X2, y2, test_size=0.2, random_state=42)

model_inn2 = lgb.LGBMClassifier(**params)
model_inn2.fit(X2_tr, y2_tr,
               eval_set=[(X2_va, y2_va)],
               callbacks=[lgb.early_stopping(30, verbose=False)])

auc2 = roc_auc_score(y2_va, model_inn2.predict_proba(X2_va)[:,1])
bs2  = brier_score_loss(y2_va, model_inn2.predict_proba(X2_va)[:,1])
print(f"Inn2 WP Model — AUC: {auc2:.4f}  |  Brier: {bs2:.4f}")

# ── Predict WP BEFORE this ball (pre-delivery state)
bbb_v2['wp_before'] = np.nan
mask1 = bbb_v2['innings'] == 1
bbb_v2.loc[mask1, 'wp_before'] = model_inn1.predict_proba(
    bbb_v2.loc[mask1, FEATURES_INN1].fillna(0))[:,1]

mask2 = (bbb_v2['innings'] == 2) & bbb_v2['runs_needed'].notna()
bbb_v2.loc[mask2, 'wp_before'] = model_inn2.predict_proba(
    bbb_v2.loc[mask2, FEATURES_INN2].fillna(0))[:,1]

# ── Predict WP AFTER: simulate state change and re-predict
def state_after(row):
    """Shift state by this ball's outcome to get post-delivery WP."""
    new_wkts = row['wickets_before'] + int(row['is_valid_wicket'])
    new_valid = row['valid_balls_before'] + int(row['is_valid'])
    new_runs  = row['runs_before'] + row['total_ball_runs']
    new_wkts_rem = max(10 - new_wkts, 0)
    new_balls_rem = max(120 - new_valid, 1)

    if row['innings'] == 1:
        new_crr = new_runs * 6 / max(new_valid, 1)
        feat = {
            'overid': row['overid'],
            'valid_balls_before': new_valid,
            'balls_remaining': new_balls_rem,
            'wickets_remaining': new_wkts_rem,
            'wickets_before': new_wkts,
            'runs_before': new_runs,
            'current_rr': new_crr,
            'is_knockout': row['is_knockout'],
        }
        return feat, 1
    else:
        new_runs_needed = max(row['target'] - new_runs, 0)
        new_rrr = new_runs_needed * 6 / new_balls_rem
        new_crr = new_runs * 6 / max(new_valid, 1)
        new_rr_gap = new_rrr - new_crr
        feat = {
            'overid': row['overid'],
            'valid_balls_before': new_valid,
            'balls_remaining': new_balls_rem,
            'wickets_remaining': new_wkts_rem,
            'wickets_before': new_wkts,
            'runs_before': new_runs,
            'runs_needed': new_runs_needed,
            'required_rr': new_rrr,
            'current_rr': new_crr,
            'rr_gap': new_rr_gap,
            'is_knockout': row['is_knockout'],
            'target': row['target'],
        }
        return feat, 2

print("Computing WP after each delivery (vectorised)...")

# Vectorized post-state computation
def compute_wp_after(bbb_df, model_inn1, model_inn2, feat1, feat2):
    df = bbb_df.copy()
    new_wkts    = df['wickets_before'] + df['is_valid_wicket'].astype(int)
    new_valid   = df['valid_balls_before'] + df['is_valid'].astype(int)
    new_runs    = df['runs_before'] + df['total_ball_runs']
    new_wkts_rem = (10 - new_wkts).clip(lower=0)
    new_balls_rem = (120 - new_valid).clip(lower=1)
    new_crr     = new_runs * 6 / new_valid.replace(0, 1)
    new_runs_needed = (df['target'] - new_runs).clip(lower=0)
    new_rrr     = new_runs_needed * 6 / new_balls_rem
    new_rr_gap  = new_rrr - new_crr

    # Inn1
    m1 = df['innings'] == 1
    post1 = pd.DataFrame({
        'overid':              df.loc[m1,'overid'],
        'valid_balls_before':  new_valid[m1],
        'balls_remaining':     new_balls_rem[m1],
        'wickets_remaining':   new_wkts_rem[m1],
        'wickets_before':      new_wkts[m1],
        'runs_before':         new_runs[m1],
        'current_rr':          new_crr[m1],
        'is_knockout':         df.loc[m1,'is_knockout'],
    })
    wp_after = pd.Series(np.nan, index=df.index)
    if len(post1):
        wp_after[m1] = model_inn1.predict_proba(post1[feat1].fillna(0))[:,1]

    # Inn2
    m2 = (df['innings'] == 2) & df['runs_needed'].notna()
    if m2.sum():
        post2 = pd.DataFrame({
            'overid':              df.loc[m2,'overid'],
            'valid_balls_before':  new_valid[m2],
            'balls_remaining':     new_balls_rem[m2],
            'wickets_remaining':   new_wkts_rem[m2],
            'wickets_before':      new_wkts[m2],
            'runs_before':         new_runs[m2],
            'runs_needed':         new_runs_needed[m2],
            'required_rr':         new_rrr[m2],
            'current_rr':          new_crr[m2],
            'rr_gap':              new_rr_gap[m2],
            'is_knockout':         df.loc[m2,'is_knockout'],
            'target':              df.loc[m2,'target'],
        })
        wp_after[m2] = model_inn2.predict_proba(post2[feat2].fillna(0))[:,1]

    return wp_after

bbb_v2['wp_after'] = compute_wp_after(bbb_v2, model_inn1, model_inn2,
                                       FEATURES_INN1, FEATURES_INN2)

# WPA from batting team perspective
bbb_v2['wpa_batting'] = bbb_v2['wp_after'] - bbb_v2['wp_before']
# WPA for bowler: reverse sign (good bowl = reduces batting team win prob)
bbb_v2['wpa_bowling'] = bbb_v2['wp_before'] - bbb_v2['wp_after']

# ── Leverage Index (LI) = how much could WP swing on this ball?
# Approximate: LI = |WP(wicket outcome) - WP(boundary outcome)|
# We already have wp_before; simulate wicket vs boundary delta
print("Computing Leverage Index...")

def simulate_wp(bbb_df, outcome_runs, outcome_wkt, model_inn1, model_inn2, feat1, feat2):
    """Simulate WP for a hypothetical outcome on each ball."""
    df = bbb_df.copy()
    new_wkts    = df['wickets_before'] + outcome_wkt
    new_valid   = df['valid_balls_before'] + 1  # always a valid ball for LI calc
    new_runs    = df['runs_before'] + outcome_runs
    new_wkts_rem = (10 - new_wkts).clip(lower=0)
    new_balls_rem = (120 - new_valid).clip(lower=1)
    new_crr     = new_runs * 6 / new_valid.replace(0,1)
    new_runs_needed = (df['target'] - new_runs).clip(lower=0)
    new_rrr     = new_runs_needed * 6 / new_balls_rem
    new_rr_gap  = new_rrr - new_crr

    m1 = df['innings'] == 1
    m2 = (df['innings'] == 2) & df['runs_needed'].notna()
    wp_sim = pd.Series(np.nan, index=df.index)

    if m1.sum():
        post1 = pd.DataFrame({
            'overid':df.loc[m1,'overid'], 'valid_balls_before':new_valid[m1],
            'balls_remaining':new_balls_rem[m1], 'wickets_remaining':new_wkts_rem[m1],
            'wickets_before':new_wkts[m1], 'runs_before':new_runs[m1],
            'current_rr':new_crr[m1], 'is_knockout':df.loc[m1,'is_knockout'],
        })
        wp_sim[m1] = model_inn1.predict_proba(post1[feat1].fillna(0))[:,1]

    if m2.sum():
        post2 = pd.DataFrame({
            'overid':df.loc[m2,'overid'], 'valid_balls_before':new_valid[m2],
            'balls_remaining':new_balls_rem[m2], 'wickets_remaining':new_wkts_rem[m2],
            'wickets_before':new_wkts[m2], 'runs_before':new_runs[m2],
            'runs_needed':new_runs_needed[m2], 'required_rr':new_rrr[m2],
            'current_rr':new_crr[m2], 'rr_gap':new_rr_gap[m2],
            'is_knockout':df.loc[m2,'is_knockout'], 'target':df.loc[m2,'target'],
        })
        wp_sim[m2] = model_inn2.predict_proba(post2[feat2].fillna(0))[:,1]

    return wp_sim

wp_boundary = simulate_wp(bbb_v2, 6, 0, model_inn1, model_inn2, FEATURES_INN1, FEATURES_INN2)
wp_wicket   = simulate_wp(bbb_v2, 0, 1, model_inn1, model_inn2, FEATURES_INN1, FEATURES_INN2)
wp_dot      = simulate_wp(bbb_v2, 0, 0, model_inn1, model_inn2, FEATURES_INN1, FEATURES_INN2)

# LI = range of outcomes
bbb_v2['leverage_index'] = (wp_boundary - wp_wicket).abs()
# Clip & normalise to 0-1+ scale
li_mean = bbb_v2['leverage_index'].quantile(0.95)
bbb_v2['leverage_index_norm'] = (bbb_v2['leverage_index'] / li_mean).clip(0, 3)

print(f"Leverage Index — mean: {bbb_v2['leverage_index'].mean():.4f}  "
      f"| p75: {bbb_v2['leverage_index'].quantile(0.75):.4f}  "
      f"| p95: {bbb_v2['leverage_index'].quantile(0.95):.4f}")

bbb_v2.to_parquet('bbb_v2_wpa.parquet', index=False)
print("Saved bbb_v2_wpa.parquet")
