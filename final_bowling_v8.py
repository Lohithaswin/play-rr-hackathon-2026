"""
FINAL BOWLING RANKING SYSTEM v8 — DEFINITIVE PRODUCTION VERSION
=================================================================
System Design:
  #1 Win Impact  — Phase-balanced XGBoost runs saved across ALL 3 phases (PP+Mid+Death) [35%]
  #2 Authentic HP WPA — Win-probability added in authentic high-pressure matches [15%]
  #3 Consistency  — Pressure match consistency rate (showing up repeatedly) [15%]
  #4 Opp Quality WPA — Opposition-quality-weighted WPA (elite=1.5x, minnow=0.5x) [10%]
  #5 Clutch Wickets — Wickets in winning pressure matches [8%]
  #6 Dots         — Dot balls in high-RR situations in wins [7%]
  #7 Knockout Pedigree — Finals, semis, qualifier appearances [5%]
  #8 Economy      — HP economy rate [5%]

Phase Penalties (All 3 Phases, Independent, Non-Blended):
  - PP Leakage: |ml_pp_runs_saved| × 0.70 if negative
  - Mid Leakage: |ml_mid_runs_saved| × 0.80 if negative
  - Death Leakage: |ml_death_runs_saved| × 0.80 if negative
  Deduction scale: 0.75 × max_raw (severe punishment for phase leakage)

Opposition Quality Context:
  - Knockouts/Finals: opp_q = 1.5
  - Minnow teams: opp_q = 0.5
  - Standard: opp_q = 1.0
  Quality adjustment: clip(avg_opp_q, 0.90, 1.10) × raw score

Outlier Protection:
  - hp_wpa_b capped at 90th percentile before normalization
  - Negative hp_wpa_b floored to 0 (no double penalty)
"""

import pandas as pd
import numpy as np

bowl_base = pd.read_parquet('bowl_rankings_final.parquet')
logs = pd.read_parquet('bowl_hp_match_logs.parquet')

# --- OPPOSITION QUALITY ---
ELITE_STAGE_KO = {'Final', 'Semi Final', 'Qualifier', 'Eliminator'}
MINNOW_TEAMS = {
    'afghanistan', 'netherlands', 'namibia', 'uganda', 'papua new guinea',
    'oman', 'canada', 'usa', 'ireland', 'scotland', 'uae', 'jersey',
    'nepal', 'bahrain', 'singapore', 'hong kong', 'malaysia'
}

def get_opp_q(row):
    if row['stage'] in ELITE_STAGE_KO:
        return 1.5
    all_teams = (str(row.get('home_team', '')) + str(row.get('away_team', ''))).lower()
    return 0.5 if any(m in all_teams for m in MINNOW_TEAMS) else 1.0

logs['opp_q'] = logs.apply(get_opp_q, axis=1)
logs['quality_wpa'] = logs['hp_wpa'] * logs['opp_q']
logs['is_knockout'] = logs['stage'].isin(ELITE_STAGE_KO).astype(int)

bowler_qual = logs.groupby('bowler_id').agg(
    quality_wpa_sum=('quality_wpa', 'sum'),
    knockout_count=('is_knockout', 'sum'),
    avg_opp_q=('opp_q', 'mean'),
    minnow_count=('opp_q', lambda x: (x == 0.5).sum()),
).reset_index()

# --- MERGE ---
bowl_v8 = bowl_base.merge(bowler_qual, on='bowler_id', how='left')
bowl_v8['quality_wpa_sum'] = bowl_v8['quality_wpa_sum'].fillna(0)
bowl_v8['knockout_count'] = bowl_v8['knockout_count'].fillna(0)
bowl_v8['avg_opp_q'] = bowl_v8['avg_opp_q'].fillna(1.0)
bowl_v8['minnow_count'] = bowl_v8['minnow_count'].fillna(0)

# --- POSITIVE PHASE CONTRIBUTIONS (independent) ---
bowl_v8['pos_pp'] = bowl_v8['ml_pp_runs_saved'].clip(lower=0)
bowl_v8['pos_mid'] = bowl_v8['ml_mid_runs_saved'].clip(lower=0)
bowl_v8['pos_death'] = bowl_v8['ml_death_runs_saved'].clip(lower=0)
bowl_v8['ml_total_pos'] = bowl_v8['pos_pp'] + bowl_v8['pos_mid'] + bowl_v8['pos_death']

# --- PHASE PENALTIES — ALL 3 PHASES, INDEPENDENT, NON-BLENDED ---
bowl_v8['pen_pp_v8'] = np.where(
    bowl_v8['ml_pp_runs_saved'] < 0, abs(bowl_v8['ml_pp_runs_saved']) * 0.70, 0.0)
bowl_v8['pen_mid_v8'] = np.where(
    bowl_v8['ml_mid_runs_saved'] < 0, abs(bowl_v8['ml_mid_runs_saved']) * 0.80, 0.0)
bowl_v8['pen_death_v8'] = np.where(
    bowl_v8['ml_death_runs_saved'] < 0, abs(bowl_v8['ml_death_runs_saved']) * 0.80, 0.0)
bowl_v8['total_pen_v8'] = bowl_v8['pen_pp_v8'] + bowl_v8['pen_mid_v8'] + bowl_v8['pen_death_v8']

# --- NORMALIZE COMPONENTS ---
def norm(s, cap_pct=None, floor_zero=False):
    s = s.copy()
    if floor_zero:
        s = s.clip(lower=0)
    if cap_pct:
        s = s.clip(upper=s.quantile(cap_pct))
    mn, mx = s.min(), s.max()
    return (s - mn) / (mx - mn + 1e-9) * 100.0

bowl_v8['N_ml'] = norm(bowl_v8['ml_total_pos'])
# hp_wpa_b: cap at 90th pct (prevents 1 hero performance dominating), floor at 0
bowl_v8['N_wpa'] = norm(bowl_v8['hp_wpa_b'], cap_pct=0.90, floor_zero=True)
bowl_v8['N_qual'] = norm(bowl_v8['quality_wpa_sum'])
bowl_v8['N_cons'] = norm(bowl_v8['hp_consistency_rate'])
bowl_v8['N_wkts'] = norm(bowl_v8['wkt_clutch_win_tot'])
bowl_v8['N_dots'] = norm(bowl_v8['dot_high_rr_win'])
bowl_v8['N_eco'] = norm(-bowl_v8['hp_eco'])
bowl_v8['N_ko'] = norm(bowl_v8['knockout_count'])

# --- WEIGHTS v8.0 ---
W = {
    'N_ml':   0.35,  # Phase-balanced XGBoost runs saved (all 3 phases, positive only)
    'N_wpa':  0.15,  # Authentic HP-match WPA (capped p90, floor 0)
    'N_qual': 0.10,  # Opposition-quality-weighted WPA
    'N_cons': 0.15,  # Pressure consistency rate
    'N_wkts': 0.08,  # Clutch wickets in winning pressure matches
    'N_dots': 0.07,  # Dot balls in high-RR situations in wins
    'N_eco':  0.05,  # HP economy rate
    'N_ko':   0.05,  # Knockout match pedigree
}
assert abs(sum(W.values()) - 1.0) < 1e-6

bowl_v8['raw_v8'] = sum(bowl_v8[col] * w for col, w in W.items())

# --- OPPOSITION QUALITY MULTIPLIER (tight range: 0.90-1.10) ---
bowl_v8['quality_adj'] = bowl_v8['avg_opp_q'].clip(0.90, 1.10)
bowl_v8['raw_v8_adj'] = bowl_v8['raw_v8'] * bowl_v8['quality_adj']

# --- PHASE DEDUCTIONS (scale 0.75 — strict punishment for ANY phase leak) ---
raw_max = bowl_v8['raw_v8_adj'].max()
pen_max = bowl_v8['total_pen_v8'].max() + 1e-9
# scale=0.75: max possible deduction = 75% of the best raw score (very severe for big leaks)
bowl_v8['ded_normalized'] = (bowl_v8['total_pen_v8'] / pen_max) * raw_max * 0.75

# --- RELIABILITY MULTIPLIER ---
bowl_v8['reliability_v8'] = np.sqrt(bowl_v8['matches'] / bowl_v8['matches'].max())

# --- FINAL CLUTCH SCORE ---
bowl_v8['clutch_v8'] = (
    (bowl_v8['raw_v8_adj'] - bowl_v8['ded_normalized']) * bowl_v8['reliability_v8']
).clip(0, 100)

# --- RANK AND SAVE ---
bowl_v8 = bowl_v8.sort_values('clutch_v8', ascending=False).reset_index(drop=True)
bowl_v8['rank_v8'] = bowl_v8.index + 1

bowl_v8.to_parquet('bowl_rankings_v8.parquet', index=False)
bowl_v8.to_csv('bowl_v8_transparent.csv', index=False)

# --- PRINT TOP 15 ---
key_cols = ['rank_v8', 'bowler_name', 'matches', 'hp_consistency_rate',
            'ml_pp_runs_saved', 'ml_mid_runs_saved', 'ml_death_runs_saved',
            'ml_total_pos',
            'pen_pp_v8', 'pen_mid_v8', 'pen_death_v8', 'total_pen_v8',
            'hp_wpa_b', 'quality_wpa_sum', 'knockout_count', 'avg_opp_q', 'clutch_v8']

print("=" * 110)
print("  FINAL BOWLING TOP 15 — v8.0 DEFINITIVE")
print("  Win Impact #1 | Full Phase Penalty (PP+Mid+Death) | Opposition Quality Context")
print("=" * 110)
print(bowl_v8.head(15)[key_cols].to_string())

print("\n--- EXPELLED/PENALISED PLAYERS ---")
track = ['Ravi Bishnoi', 'Mohammed Siraj', 'Arshdeep Singh', 'Varun Chakravarthy', 'Rashid Khan']
print(bowl_v8[bowl_v8['bowler_name'].isin(track)][key_cols].to_string())
