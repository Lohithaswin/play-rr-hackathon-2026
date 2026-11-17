"""
SupeRR Selector Season 2 — Player Ranking Engine
=================================================
Computes batting and bowling performance under pressure vs baseline,
produces Top 10 rankings with confidence-weighted composite scores.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("Loading enriched dataset...")
df = pd.read_parquet('bbb_enriched.parquet')

# Valid deliveries only for all metrics
valid = df[df['is_valid_ball']].copy()
# Pressure threshold: PI >= 25 (tighter than 20 — avoids false positives)
pressure = valid[valid['pressure_index'] >= 25].copy()
normal   = valid[valid['pressure_index'] < 10].copy()  # truly low-pressure baseline

print(f"Valid balls: {len(valid):,}")
print(f"Pressure balls (PI>=25): {len(pressure):,}")
print(f"Normal balls (PI<10): {len(normal):,}")

# ─────────────────────────────────────────────
# MIN THRESHOLDS FOR ELIGIBILITY
# ─────────────────────────────────────────────
MIN_PRESSURE_BALLS_BAT  = 50   # batters: min balls faced under pressure
MIN_PRESSURE_BALLS_BOWL = 50   # bowlers: min balls bowled under pressure

# ─────────────────────────────────────────────
# BATTING METRICS UNDER PRESSURE
# ─────────────────────────────────────────────
print("\n=== BATTING RANKINGS ===")

def compute_batting_metrics(balls_df, label=''):
    grp = balls_df.groupby(['striker_id', 'striker_name'])
    return grp.agg(
        balls_faced = ('runs', 'count'),
        runs_scored = ('runs', 'sum'),
        fours       = ('is_four', 'sum'),
        sixes       = ('is_six', 'sum'),
        dots        = ('runs', lambda x: (x == 0).sum()),
        wickets_lost= ('is_wicket', 'sum'),
        avg_pi      = ('pressure_index', 'mean'),
    ).reset_index()

bat_pressure = compute_batting_metrics(pressure, 'pressure')
bat_baseline = compute_batting_metrics(normal,   'baseline')

# Compute rates
def enrich_batting(df, suffix=''):
    df = df.copy()
    df['strike_rate'] = df['runs_scored'] / df['balls_faced'] * 100
    df['average'] = df['runs_scored'] / df['wickets_lost'].replace(0, np.nan)
    df['boundary_rate'] = (df['fours'] + df['sixes']) / df['balls_faced'] * 100
    df['dot_rate'] = df['dots'] / df['balls_faced'] * 100
    df.columns = ['striker_id', 'striker_name'] + [
        f'{c}_{suffix}' if c not in ['striker_id', 'striker_name'] else c
        for c in df.columns[2:]
    ]
    return df

bat_p = enrich_batting(bat_pressure, 'p')
bat_b = enrich_batting(bat_baseline, 'b')

bat_merged = bat_p.merge(bat_b, on=['striker_id', 'striker_name'], how='left')

# Filter: minimum pressure balls
bat_merged = bat_merged[bat_merged['balls_faced_p'] >= MIN_PRESSURE_BALLS_BAT]
print(f"Eligible batters (>={MIN_PRESSURE_BALLS_BAT} pressure balls): {len(bat_merged)}")

# ── Clutch Performance Ratio (CPR) for batting
# CPR = (SR under pressure / SR baseline) * (Avg under pressure / Avg baseline)
# Higher = better under pressure than normal
bat_merged['sr_ratio'] = bat_merged['strike_rate_p'] / bat_merged['strike_rate_b'].replace(0, np.nan)
bat_merged['avg_ratio'] = bat_merged['average_p'] / bat_merged['average_b'].replace(0, np.nan)
bat_merged['boundary_ratio'] = bat_merged['boundary_rate_p'] / bat_merged['boundary_rate_b'].replace(0, np.nan)

# Cap ratios to avoid extreme outliers
bat_merged['sr_ratio'] = bat_merged['sr_ratio'].clip(0, 3)
bat_merged['avg_ratio'] = bat_merged['avg_ratio'].clip(0, 3)
bat_merged['boundary_ratio'] = bat_merged['boundary_ratio'].clip(0, 3)

# Composite batting pressure score
# 40% SR in pressure, 30% average in pressure, 20% boundary rate, 10% CPR vs baseline
bat_merged['bat_abs_score'] = (
    0.40 * bat_merged['strike_rate_p'] / 150 * 100 +   # normalized to 150 as max SR
    0.30 * bat_merged['average_p'].clip(0, 50) / 50 * 100 +
    0.20 * bat_merged['boundary_rate_p'] / 30 * 100 +  # 30% boundary as max
    0.10 * bat_merged['dot_rate_p'].apply(lambda x: max(0, 100 - x))  # fewer dots = better
)

bat_merged['bat_cpr'] = (
    0.5 * bat_merged['sr_ratio'].fillna(1) +
    0.3 * bat_merged['avg_ratio'].fillna(1) +
    0.2 * bat_merged['boundary_ratio'].fillna(1)
)

# Combined batting score: absolute performance + clutch bonus
bat_merged['batting_pressure_score'] = (
    0.65 * bat_merged['bat_abs_score'] +
    0.35 * bat_merged['bat_cpr'] * 50   # scale CPR to comparable range
).clip(0, 100)

# Confidence adjustment: more pressure balls = more reliable
bat_merged['confidence'] = np.minimum(bat_merged['balls_faced_p'] / 200, 1.0)
bat_merged['batting_pressure_score_adj'] = (
    bat_merged['batting_pressure_score'] * bat_merged['confidence']
)

bat_top = bat_merged.sort_values('batting_pressure_score_adj', ascending=False).head(20)

print("\nTop 20 Batters Under Pressure:")
print(bat_top[['striker_name', 'balls_faced_p', 'runs_scored_p',
               'strike_rate_p', 'average_p', 'boundary_rate_p',
               'strike_rate_b', 'average_b', 'bat_cpr',
               'batting_pressure_score_adj']].to_string(index=False))

# ─────────────────────────────────────────────
# BOWLING METRICS UNDER PRESSURE
# ─────────────────────────────────────────────
print("\n\n=== BOWLING RANKINGS ===")

def compute_bowling_metrics(balls_df):
    grp = balls_df.groupby(['bowler_id', 'bowler_name'])
    return grp.agg(
        balls_bowled = ('runs', 'count'),
        runs_conceded= ('bowler_runs', 'sum'),
        wickets      = ('is_valid_wicket', 'sum'),
        dots         = ('runs', lambda x: (x == 0).sum()),
        boundaries_conceded = ('is_four', 'sum'),
        sixes_conceded = ('is_six', 'sum'),
        avg_pi       = ('pressure_index', 'mean'),
    ).reset_index()

bowl_pressure = compute_bowling_metrics(pressure)
bowl_baseline = compute_bowling_metrics(normal)

def enrich_bowling(df, suffix=''):
    df = df.copy()
    df['economy'] = df['runs_conceded'] / df['balls_bowled'] * 6
    df['bowling_avg'] = df['runs_conceded'] / df['wickets'].replace(0, np.nan)
    df['bowling_sr'] = df['balls_bowled'] / df['wickets'].replace(0, np.nan)
    df['dot_rate'] = df['dots'] / df['balls_bowled'] * 100
    df['boundary_rate'] = (df['boundaries_conceded'] + df['sixes_conceded']) / df['balls_bowled'] * 100
    df.columns = ['bowler_id', 'bowler_name'] + [
        f'{c}_{suffix}' if c not in ['bowler_id', 'bowler_name'] else c
        for c in df.columns[2:]
    ]
    return df

bowl_p = enrich_bowling(bowl_pressure, 'p')
bowl_b = enrich_bowling(bowl_baseline, 'b')

bowl_merged = bowl_p.merge(bowl_b, on=['bowler_id', 'bowler_name'], how='left')

# Filter: minimum pressure balls
bowl_merged = bowl_merged[bowl_merged['balls_bowled_p'] >= MIN_PRESSURE_BALLS_BOWL]
print(f"Eligible bowlers (>={MIN_PRESSURE_BALLS_BOWL} pressure balls): {len(bowl_merged)}")

# Economy ratio (baseline_economy / pressure_economy) — higher = controls better
bowl_merged['economy_ratio'] = bowl_merged['economy_b'] / bowl_merged['economy_p'].replace(0, np.nan)
bowl_merged['wicket_ratio'] = (bowl_merged['wickets_p'] / bowl_merged['balls_bowled_p']) / \
                               (bowl_merged['wickets_b'] / bowl_merged['balls_bowled_b'].replace(0, np.nan))
bowl_merged['dot_ratio'] = bowl_merged['dot_rate_p'] / bowl_merged['dot_rate_b'].replace(0, np.nan)

# Cap ratios
bowl_merged['economy_ratio'] = bowl_merged['economy_ratio'].clip(0, 3)
bowl_merged['wicket_ratio']  = bowl_merged['wicket_ratio'].clip(0, 5)
bowl_merged['dot_ratio']     = bowl_merged['dot_ratio'].clip(0, 3)

# Absolute bowling pressure score
# Low economy + wickets + dots = good
bowl_merged['bowl_abs_score'] = (
    0.35 * (1 - bowl_merged['economy_p'].clip(5, 15) / 15) * 100 +  # lower economy = higher score
    0.30 * bowl_merged['wickets_p'] / bowl_merged['balls_bowled_p'] * 600 +  # wicket % scaled
    0.20 * bowl_merged['dot_rate_p'] +  # higher dots = better
    0.15 * (1 - bowl_merged['boundary_rate_p'].clip(0, 20) / 20) * 100
)

bowl_merged['bowl_cpr'] = (
    0.4 * bowl_merged['economy_ratio'].fillna(1) +
    0.3 * bowl_merged['wicket_ratio'].fillna(1) +
    0.3 * bowl_merged['dot_ratio'].fillna(1)
)

bowl_merged['bowling_pressure_score'] = (
    0.65 * bowl_merged['bowl_abs_score'] +
    0.35 * bowl_merged['bowl_cpr'] * 50
).clip(0, 100)

# Confidence adjustment
bowl_merged['confidence'] = np.minimum(bowl_merged['balls_bowled_p'] / 200, 1.0)
bowl_merged['bowling_pressure_score_adj'] = (
    bowl_merged['bowling_pressure_score'] * bowl_merged['confidence']
)

bowl_top = bowl_merged.sort_values('bowling_pressure_score_adj', ascending=False).head(20)

print("\nTop 20 Bowlers Under Pressure:")
print(bowl_top[['bowler_name', 'balls_bowled_p', 'runs_conceded_p', 'wickets_p',
                'economy_p', 'dot_rate_p', 'boundary_rate_p',
                'economy_b', 'bowl_cpr',
                'bowling_pressure_score_adj']].to_string(index=False))

# ─────────────────────────────────────────────
# SAVE RESULTS
# ─────────────────────────────────────────────
bat_merged.to_parquet('bat_rankings.parquet', index=False)
bowl_merged.to_parquet('bowl_rankings.parquet', index=False)

print("\n=== FINAL TOP 10 BATTERS ===")
for i, row in bat_top.head(10).reset_index(drop=True).iterrows():
    print(f"  #{i+1}: {row['striker_name']} | PI-avg={row['avg_pi_p']:.0f} | SR(P)={row['strike_rate_p']:.1f} | Avg(P)={row['average_p']:.1f} | Balls={row['balls_faced_p']:.0f} | Score={row['batting_pressure_score_adj']:.2f}")

print("\n=== FINAL TOP 10 BOWLERS ===")
for i, row in bowl_top.head(10).reset_index(drop=True).iterrows():
    print(f"  #{i+1}: {row['bowler_name']} | PI-avg={row['avg_pi_p']:.0f} | Eco(P)={row['economy_p']:.2f} | Wkts(P)={row['wickets_p']:.0f} | Dots={row['dot_rate_p']:.1f}% | Score={row['bowling_pressure_score_adj']:.2f}")

print("\nDone. Saved bat_rankings.parquet and bowl_rankings.parquet")
