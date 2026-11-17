"""
SupeRR Selector v3 — Enhanced Pressure Intelligence
=====================================================
Adds: Match Importance, Team Dependency, Comeback Factor,
      High-Impact Ball Weighting, Win Multiplier
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("LOADING BASE DATA")
print("=" * 60)

df      = pd.read_parquet('bbb_v2_wpa.parquet')
matches = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')
comps   = pd.read_csv('6af458274c1e8_data_pack/Data Pack/competitions.csv')
players = pd.read_csv('6af458274c1e8_data_pack/Data Pack/competition_team_player_mapping.csv')

valid = df[df['is_valid']].copy()

# ═══════════════════════════════════════════════════════
# 1. MATCH IMPORTANCE MULTIPLIER
# ═══════════════════════════════════════════════════════
print("\n1. Computing Match Importance...")

# Get match context
match_ctx = matches[['match_id','comp_id','match_number','stage','knock_out']].copy()
match_ctx = match_ctx.merge(comps[['comp_id','match_format','comp_name','season']], on='comp_id', how='left')

# Count total matches per competition
comp_match_count = matches.groupby('comp_id')['match_id'].count().reset_index(name='total_comp_matches')
match_ctx = match_ctx.merge(comp_match_count, on='comp_id', how='left')

# Match position in competition (later = more important in league stage)
match_ctx['match_position_pct'] = match_ctx['match_number'] / match_ctx['total_comp_matches']

# Is IPL? (IPL has higher global significance)
match_ctx['is_ipl'] = match_ctx['comp_name'].str.contains('IPL|Indian Premier League', case=False, na=False).astype(int)

# Is ICC tournament? (World Cup etc.)
match_ctx['is_icc_event'] = match_ctx['comp_name'].str.contains(
    'World Cup|World Championship|Asia Cup|Champions', case=False, na=False).astype(int)

# Build multiplier
def match_importance(row):
    base = 1.0

    # Stage-based
    stage = str(row['stage']).lower() if pd.notna(row['stage']) else ''
    if 'final' == stage:
        base = 2.5
    elif 'semi' in stage:
        base = 2.2
    elif 'qualifier' in stage or 'eliminator' in stage:
        base = 2.0
    elif row['knock_out'] == 1:
        base = 2.0
    elif 'super' in stage:  # Super 4 / Super 8
        base = 1.5
    else:
        # League stage: later matches are more important (playoff race)
        if row['match_position_pct'] > 0.75:
            base = 1.4   # Last quarter of league = must-win territory
        elif row['match_position_pct'] > 0.5:
            base = 1.2
        else:
            base = 1.0

    # Competition prestige bonus
    if row['is_ipl']:
        base *= 1.15  # IPL is the highest-quality T20 league
    elif row['is_icc_event']:
        base *= 1.2   # ICC events = national pride pressure

    return round(base, 3)

match_ctx['match_importance'] = match_ctx.apply(match_importance, axis=1)

print(f"  Match importance distribution:")
print(f"    min={match_ctx['match_importance'].min():.2f}  "
      f"median={match_ctx['match_importance'].median():.2f}  "
      f"max={match_ctx['match_importance'].max():.2f}")
print(f"  Finals/SF/QF/EL: {(match_ctx['match_importance'] >= 2.0).sum()} matches")
print(f"  Late league (must-win): {((match_ctx['match_importance'] >= 1.3) & (match_ctx['match_importance'] < 2.0)).sum()} matches")

# Merge into valid
valid = valid.merge(match_ctx[['match_id','match_importance','is_ipl','is_icc_event']],
                    on='match_id', how='left')
valid['match_importance'] = valid['match_importance'].fillna(1.0)

# ═══════════════════════════════════════════════════════
# 2. TEAM DEPENDENCY INDEX
# ═══════════════════════════════════════════════════════
print("\n2. Computing Team Dependency Index...")

# Per batter per match: what % of team's total innings runs did they score?
batter_match_runs = (valid.groupby(['match_id','innings','batting_team_id','striker_id','striker_name'])
    .agg(player_runs=('runs','sum'), player_balls=('runs','count'))
    .reset_index())

innings_total_runs = (valid.groupby(['match_id','innings','batting_team_id'])
    .agg(team_runs=('total_ball_runs','sum'), team_balls=('runs','count'))
    .reset_index())

batter_dep = batter_match_runs.merge(innings_total_runs, on=['match_id','innings','batting_team_id'])
batter_dep['run_share'] = batter_dep['player_runs'] / batter_dep['team_runs'].replace(0, np.nan)
batter_dep['ball_share'] = batter_dep['player_balls'] / batter_dep['team_balls']

# Dependency = high run_share means team leaned on this player
# Score: if you scored 40%+ of runs, you carried the team
batter_dep['bat_dependency'] = np.where(
    batter_dep['run_share'] >= 0.40, 2.0,
    np.where(batter_dep['run_share'] >= 0.30, 1.5,
    np.where(batter_dep['run_share'] >= 0.20, 1.2, 1.0)))

# Per bowler per match: what % of team's wickets did they take?
bowler_match_wkts = (valid.groupby(['match_id','innings','bowling_team_id','bowler_id','bowler_name'])
    .agg(player_wkts=('is_valid_wicket','sum'), player_balls=('runs','count'),
         player_runs_conceded=('bowler_runs','sum'))
    .reset_index())

innings_total_wkts = (valid.groupby(['match_id','innings','bowling_team_id'])
    .agg(team_wkts=('is_valid_wicket','sum'), team_balls=('runs','count'))
    .reset_index())

bowler_dep = bowler_match_wkts.merge(innings_total_wkts, on=['match_id','innings','bowling_team_id'])
bowler_dep['wkt_share'] = bowler_dep['player_wkts'] / bowler_dep['team_wkts'].replace(0, np.nan)
bowler_dep['ball_share'] = bowler_dep['player_balls'] / bowler_dep['team_balls']

bowler_dep['bowl_dependency'] = np.where(
    bowler_dep['wkt_share'] >= 0.40, 2.0,
    np.where(bowler_dep['wkt_share'] >= 0.30, 1.5,
    np.where(bowler_dep['wkt_share'] >= 0.20, 1.2, 1.0)))

# Merge dependency back to ball level
valid = valid.merge(
    batter_dep[['match_id','innings','striker_id','bat_dependency','run_share']],
    on=['match_id','innings','striker_id'], how='left')
valid['bat_dependency'] = valid['bat_dependency'].fillna(1.0)

valid = valid.merge(
    bowler_dep[['match_id','innings','bowler_id','bowl_dependency','wkt_share']],
    on=['match_id','innings','bowler_id'], how='left')
valid['bowl_dependency'] = valid['bowl_dependency'].fillna(1.0)

print(f"  Batters with 40%+ run share in a match: {(batter_dep['run_share'] >= 0.40).sum()} innings")
print(f"  Batters with 30%+ run share: {(batter_dep['run_share'] >= 0.30).sum()} innings")
print(f"  Bowlers with 40%+ wkt share: {(bowler_dep['wkt_share'] >= 0.40).sum()} innings")

# ═══════════════════════════════════════════════════════
# 3. COMEBACK FACTOR
# ═══════════════════════════════════════════════════════
print("\n3. Computing Comeback Factor...")

# A batter's comeback = they entered when WP was low and left with WP higher
# Track WP at start and end of each batter's stint per innings

batter_stints = (valid.groupby(['match_id','innings','striker_id','striker_name'])
    .agg(
        wp_entry = ('wp_before', 'first'),
        wp_exit  = ('wp_after',  'last'),
        stint_balls = ('runs', 'count'),
        stint_runs  = ('runs', 'sum'),
        wpa_total   = ('wpa_batting', 'sum'),
    ).reset_index())

batter_stints['wp_swing'] = batter_stints['wp_exit'] - batter_stints['wp_entry']
# Comeback = entered when team was struggling (WP < 0.35) and improved WP
batter_stints['is_comeback'] = (
    (batter_stints['wp_entry'] < 0.35) &
    (batter_stints['wp_swing'] > 0.10) &
    (batter_stints['stint_balls'] >= 10)
)
# Rescue = entered at really bad position (WP < 0.20) and made a real impact
batter_stints['is_rescue'] = (
    (batter_stints['wp_entry'] < 0.20) &
    (batter_stints['wp_swing'] > 0.15) &
    (batter_stints['stint_balls'] >= 8)
)

comeback_agg = batter_stints.groupby(['striker_id','striker_name']).agg(
    comeback_innings = ('is_comeback', 'sum'),
    rescue_innings   = ('is_rescue', 'sum'),
    avg_wp_swing     = ('wp_swing', 'mean'),
    total_wp_swing   = ('wp_swing', 'sum'),
).reset_index()

print(f"  Total comeback innings: {int(batter_stints['is_comeback'].sum())}")
print(f"  Total rescue innings: {int(batter_stints['is_rescue'].sum())}")

# Bowler comeback: entered when batting team was cruising (WP > 0.65 for batting) and pulled it back
bowler_stints = (valid.groupby(['match_id','innings','bowler_id','bowler_name'])
    .agg(
        wp_entry_bowl = ('wp_before', 'first'),
        wp_exit_bowl  = ('wp_after',  'last'),
        stint_balls   = ('runs', 'count'),
        wpa_total     = ('wpa_bowling', 'sum'),
        wkts_taken    = ('is_valid_wicket', 'sum'),
    ).reset_index())

# For bowler: batting team WP was high (>0.60) and bowler brought it down
bowler_stints['wp_swing_bowl'] = bowler_stints['wp_entry_bowl'] - bowler_stints['wp_exit_bowl']  # positive = bowler clawed back
bowler_stints['is_comeback_bowl'] = (
    (bowler_stints['wp_entry_bowl'] > 0.60) &
    (bowler_stints['wp_swing_bowl'] > 0.10) &
    (bowler_stints['stint_balls'] >= 6)
)

comeback_bowl = bowler_stints.groupby(['bowler_id','bowler_name']).agg(
    comeback_spells  = ('is_comeback_bowl', 'sum'),
    avg_wp_swing_bowl= ('wp_swing_bowl', 'mean'),
    total_wp_swing_bowl = ('wp_swing_bowl', 'sum'),
).reset_index()

print(f"  Bowler comeback spells: {int(bowler_stints['is_comeback_bowl'].sum())}")

# ═══════════════════════════════════════════════════════
# 4. ENHANCED PRESSURE FLAGS + IMPORTANCE WEIGHTING
# ═══════════════════════════════════════════════════════
print("\n4. Enhanced pressure classification...")

LI_THRESHOLD = valid['leverage_index_norm'].quantile(0.70)
LI_SUPER     = valid['leverage_index_norm'].quantile(0.85)
LI_ULTRA     = valid['leverage_index_norm'].quantile(0.92)

# Context flags (same as before + new ones)
valid['f_death']     = valid['overid'] >= 17
valid['f_pp_end']    = (valid['overid'].isin([5,6])) & (valid['innings']==1)
valid['f_high_rrr']  = valid['required_rr'].fillna(0) > 9
valid['f_quick_wkts']= valid['recent_wickets_5'] >= 2
valid['f_dot_pileup']= valid['recent_dots_5'] >= 3
valid['f_big_chase'] = (valid['innings']==2) & (valid['target'].fillna(0) >= 185)
valid['f_knockout']  = valid['is_knockout'] == 1
valid['f_collapse']  = (valid['wickets_remaining'] <= 3) & (valid['overid'] >= 15)
valid['f_important'] = valid['match_importance'] >= 1.5  # must-win / playoff
valid['f_carrying']  = valid['bat_dependency'] >= 1.5     # carrying the team

valid['ctx_flags'] = (
    valid['f_death'].astype(int) + valid['f_pp_end'].astype(int) +
    valid['f_high_rrr'].astype(int) + valid['f_quick_wkts'].astype(int) +
    valid['f_dot_pileup'].astype(int) + valid['f_big_chase'].astype(int) +
    valid['f_knockout'].astype(int) + valid['f_collapse'].astype(int) +
    valid['f_important'].astype(int) + valid['f_carrying'].astype(int)
)

valid['is_high_pressure'] = (valid['leverage_index_norm'] >= LI_THRESHOLD) & (valid['ctx_flags'] >= 1)
valid['is_super_pressure'] = (valid['leverage_index_norm'] >= LI_SUPER) & (valid['ctx_flags'] >= 2)
valid['is_ultra_pressure'] = (valid['leverage_index_norm'] >= LI_ULTRA) & (valid['ctx_flags'] >= 3)

# Pressure release
valid['recent_wicket_3'] = (valid.groupby(['match_id','innings'], group_keys=False)
    .apply(lambda g: g['is_valid_wicket'].astype(int).rolling(3,min_periods=1).sum().shift(1).fillna(0)))
valid['under_dot_stress'] = (valid['recent_dots_5'] >= 3) | (valid['recent_wicket_3'] >= 1)
valid['is_pressure_release'] = (valid['under_dot_stress'] & (valid['total_ball_runs'] >= 4) & valid['is_high_pressure'])

n_hi = int(valid['is_high_pressure'].sum())
n_sup = int(valid['is_super_pressure'].sum())
n_ult = int(valid['is_ultra_pressure'].sum())
print(f"  High-pressure: {n_hi:,} ({n_hi/len(valid)*100:.1f}%)")
print(f"  Super-pressure: {n_sup:,} ({n_sup/len(valid)*100:.1f}%)")
print(f"  Ultra-pressure: {n_ult:,} ({n_ult/len(valid)*100:.1f}%)")

# ── IMPORTANCE-WEIGHTED WPA
# WPA * match_importance * (win_bonus)
valid['win_multiplier'] = np.where(valid['batting_team_won'] == 1, 1.3, 0.85)  # winning contributions > losing

# HIGH-IMPACT BALL weighting: top 10% LI balls get 2x, top 5% get 2.5x
valid['impact_weight'] = np.where(
    valid['leverage_index_norm'] >= valid['leverage_index_norm'].quantile(0.95), 2.5,
    np.where(valid['leverage_index_norm'] >= valid['leverage_index_norm'].quantile(0.90), 2.0,
    np.where(valid['leverage_index_norm'] >= valid['leverage_index_norm'].quantile(0.80), 1.5, 1.0)))

# ENHANCED WPA
valid['wpa_bat_enhanced'] = (valid['wpa_batting'] *
    valid['match_importance'] *
    valid['bat_dependency'] *
    valid['impact_weight'])

# For batting team wins, give extra credit
valid['wpa_bat_final'] = valid['wpa_bat_enhanced'] * valid['win_multiplier']

valid['wpa_bowl_enhanced'] = (valid['wpa_bowling'] *
    valid['match_importance'] *
    valid['bowl_dependency'] *
    valid['impact_weight'])

# Win multiplier for bowler: bowling team won = batting team lost
valid['bowl_win_mult'] = np.where(valid['batting_team_won'] == 0, 1.3, 0.85)
valid['wpa_bowl_final'] = valid['wpa_bowl_enhanced'] * valid['bowl_win_mult']

# ── Shutdown overs (recompute with importance)
over_stats = (valid.groupby(['match_id','innings','overid','bowler_id','bowler_name'])
    .agg(over_runs=('total_ball_runs','sum'), over_balls=('is_valid','sum'),
         over_wickets=('is_valid_wicket','sum'), recent_avg_rr=('recent_avg_rr','first'),
         match_imp=('match_importance','first'))
    .reset_index())
over_stats['over_economy'] = over_stats['over_runs'] / over_stats['over_balls'] * 6
over_stats['is_shutdown_over'] = ((over_stats['recent_avg_rr'] >= 9) &
    (over_stats['over_economy'] <= 6) & (over_stats['over_balls'] >= 5))

# ═══════════════════════════════════════════════════════
# 5. PLAYER RANKINGS — FINAL COMPOSITE
# ═══════════════════════════════════════════════════════
print("\n5. Computing final player rankings...")

MIN_BAT  = 80
MIN_BOWL = 60

hi = valid[valid['is_high_pressure']].copy()
norm = valid[valid['leverage_index_norm'] < valid['leverage_index_norm'].quantile(0.30)].copy()
rel = valid[valid['is_pressure_release']].copy()

# ── BATTING ──
def bat_agg(d, mq=0):
    g = d.groupby(['striker_id','striker_name'])
    r = g.agg(
        balls=('runs','count'), runs=('runs','sum'),
        fours=('is_four','sum'), sixes=('is_six','sum'),
        dots=('runs', lambda x:(x==0).sum()),
        wkts_lost=('is_valid_wicket','sum'),
        wpa_enhanced=('wpa_bat_final','sum'),
        wpa_enhanced_mean=('wpa_bat_final','mean'),
        wpa_raw=('wpa_batting','sum'),
        avg_li=('leverage_index_norm','mean'),
        avg_importance=('match_importance','mean'),
        avg_dependency=('bat_dependency','mean'),
        win_balls=('batting_team_won','sum'),
        total_matches=('match_id', 'nunique'),
    ).reset_index()
    r['sr'] = r['runs']/r['balls']*100
    r['avg'] = r['runs']/r['wkts_lost'].replace(0,np.nan)
    r['dot_pct'] = r['dots']/r['balls']*100
    r['bdry_pct'] = (r['fours']+r['sixes'])/r['balls']*100
    r['win_pct'] = r['win_balls']/r['balls']*100
    if mq: r = r[r['balls']>=mq]
    return r

bat_hi   = bat_agg(hi, MIN_BAT)
bat_norm = bat_agg(norm, 15)

# WPA clutch (enhanced)
bat_wpa = hi.groupby(['striker_id','striker_name']).agg(
    clutch_wpa=('wpa_bat_final','sum'),
    clutch_wpa_mean=('wpa_bat_final','mean'),
    clutch_wpa_raw=('wpa_batting','sum'),
).reset_index()

# Release
bat_rel = rel.groupby(['striker_id','striker_name']).agg(
    release_moments=('is_pressure_release','sum'),
).reset_index()

# Ultra-pressure performance
ultra = valid[valid['is_ultra_pressure']].copy()
bat_ultra = ultra.groupby(['striker_id','striker_name']).agg(
    ultra_balls=('runs','count'), ultra_runs=('runs','sum'),
    ultra_wpa=('wpa_bat_final','sum'),
).reset_index()
bat_ultra['ultra_sr'] = bat_ultra['ultra_runs']/bat_ultra['ultra_balls']*100

# Merge all
bat = bat_hi.copy()
bat = bat.merge(bat_norm[['striker_id','sr','avg','dot_pct']].rename(
    columns={'sr':'sr_base','avg':'avg_base','dot_pct':'dot_base'}),
    on='striker_id', how='left')
bat = bat.merge(bat_wpa, on=['striker_id','striker_name'], how='left')
bat = bat.merge(bat_rel, on=['striker_id','striker_name'], how='left')
bat = bat.merge(comeback_agg, on=['striker_id','striker_name'], how='left')
bat = bat.merge(bat_ultra[['striker_id','ultra_balls','ultra_sr','ultra_wpa']],
                on='striker_id', how='left')

bat['release_moments']  = bat['release_moments'].fillna(0)
bat['comeback_innings']  = bat['comeback_innings'].fillna(0)
bat['rescue_innings']    = bat['rescue_innings'].fillna(0)
bat['ultra_balls']       = bat['ultra_balls'].fillna(0)
bat['ultra_wpa']         = bat['ultra_wpa'].fillna(0)

# ── Compute component scores
bat['sr_ratio']  = (bat['sr']/bat['sr_base'].replace(0,np.nan)).clip(0,2.5)
bat['avg_ratio'] = (bat['avg']/bat['avg_base'].replace(0,np.nan)).clip(0,2.5)

wpa_p95 = bat['clutch_wpa_mean'].quantile(0.95)
bat['wpa_score']     = (bat['clutch_wpa_mean']/wpa_p95*100).clip(-50,100)
bat['sr_score']      = (bat['sr']/180*100).clip(0,100)
bat['ratio_score']   = ((bat['sr_ratio'].fillna(1)+bat['avg_ratio'].fillna(1))/2*50).clip(0,100)
bat['release_per_50']= bat['release_moments']/bat['balls']*50
bat['release_score'] = (bat['release_per_50']*12).clip(0,30)
bat['win_score']     = (bat['win_pct']-50).clip(-20,20)

# NEW: Comeback bonus
bat['comeback_score'] = ((bat['comeback_innings']*3 + bat['rescue_innings']*5) / bat['total_matches'] * 50).clip(0, 25)

# NEW: Match importance score — average match importance faced
bat['importance_score'] = ((bat['avg_importance'] - 1.0) * 80).clip(0, 20)

# NEW: Ultra-pressure performance bonus
bat['ultra_score'] = (bat['ultra_wpa'] / bat['ultra_balls'].replace(0,np.nan) * 500).fillna(0).clip(0, 20)

# Volume/reliability
bat['vol_adj'] = np.minimum(bat['balls'] / 250, 1.0)

# ── FINAL COMPOSITE (rebalanced weights)
bat['raw_score'] = (
    0.30 * bat['wpa_score'].fillna(0) +     # Clutch WPA (enhanced)
    0.15 * bat['sr_score'] +                  # Raw SR under pressure
    0.12 * bat['ratio_score'] +               # Clutch vs baseline ratio
    0.12 * bat['release_score'] +             # Pressure release moments
    0.10 * bat['comeback_score'] +            # Comeback/rescue innings
    0.08 * bat['importance_score'] +          # Playing in big matches
    0.08 * bat['ultra_score'] +               # Ultra-pressure performance
    0.05 * bat['win_score'].fillna(0)         # Win contribution
)
bat['batting_clutch_score'] = (bat['raw_score'] * bat['vol_adj']).clip(0, 100)

bat_top = bat.sort_values('batting_clutch_score', ascending=False).head(25)

print(f"\nEligible batters: {len(bat)}")
print("\nTOP 15 BATTERS:")
for i, row in bat_top.head(15).reset_index(drop=True).iterrows():
    print(f"  #{i+1:2d}: {row['striker_name']:<26} "
          f"B={int(row['balls']):<4} SR={row['sr']:.1f} Avg={row['avg']:.1f} "
          f"WPA={row['clutch_wpa']:.3f} Rel={int(row['release_moments'])} "
          f"CB={int(row['comeback_innings'])} Imp={row['avg_importance']:.2f} "
          f"Scr={row['batting_clutch_score']:.2f}")

# ── BOWLING ──
def bowl_agg(d, mq=0):
    g = d.groupby(['bowler_id','bowler_name'])
    r = g.agg(
        balls=('runs','count'), runs=('bowler_runs','sum'),
        wkts=('is_valid_wicket','sum'),
        dots=('runs',lambda x:(x==0).sum()),
        fours_con=('is_four','sum'), sixes_con=('is_six','sum'),
        wpa_enhanced=('wpa_bowl_final','sum'),
        wpa_enhanced_mean=('wpa_bowl_final','mean'),
        wpa_raw=('wpa_bowling','sum'),
        avg_li=('leverage_index_norm','mean'),
        avg_importance=('match_importance','mean'),
        avg_dependency=('bowl_dependency','mean'),
        win_balls=('batting_team_won', lambda x:(x==0).sum()),
        total_matches=('match_id','nunique'),
    ).reset_index()
    r['economy'] = r['runs']/r['balls']*6
    r['dot_pct'] = r['dots']/r['balls']*100
    r['wkt_pct'] = r['wkts']/r['balls']*100
    r['bdry_pct']= (r['fours_con']+r['sixes_con'])/r['balls']*100
    r['win_pct'] = r['win_balls']/r['balls']*100
    if mq: r = r[r['balls']>=mq]
    return r

bowl_hi   = bowl_agg(hi, MIN_BOWL)
bowl_norm = bowl_agg(norm, 15)

bowl_wpa = hi.groupby(['bowler_id','bowler_name']).agg(
    clutch_wpa=('wpa_bowl_final','sum'),
    clutch_wpa_mean=('wpa_bowl_final','mean'),
    clutch_wpa_raw=('wpa_bowling','sum'),
).reset_index()

shut_cr = over_stats[over_stats['is_shutdown_over']].groupby(['bowler_id','bowler_name']).agg(
    shutdown_overs=('is_shutdown_over','sum'),
    shutdown_wkts=('over_wickets','sum'),
).reset_index()

bowl_ultra = ultra.groupby(['bowler_id','bowler_name']).agg(
    ultra_balls=('runs','count'), ultra_wkts=('is_valid_wicket','sum'),
    ultra_wpa=('wpa_bowl_final','sum'),
).reset_index()

bowl = bowl_hi.copy()
bowl = bowl.merge(bowl_norm[['bowler_id','economy','dot_pct']].rename(
    columns={'economy':'eco_base','dot_pct':'dot_base'}),
    on='bowler_id', how='left')
bowl = bowl.merge(bowl_wpa, on=['bowler_id','bowler_name'], how='left')
bowl = bowl.merge(shut_cr, on=['bowler_id','bowler_name'], how='left')
bowl = bowl.merge(comeback_bowl, on=['bowler_id','bowler_name'], how='left')
bowl = bowl.merge(bowl_ultra[['bowler_id','ultra_balls','ultra_wkts','ultra_wpa']],
                  on='bowler_id', how='left')

bowl['shutdown_overs']   = bowl['shutdown_overs'].fillna(0)
bowl['comeback_spells']  = bowl['comeback_spells'].fillna(0)
bowl['ultra_balls']      = bowl['ultra_balls'].fillna(0)
bowl['ultra_wpa']        = bowl['ultra_wpa'].fillna(0)

# Component scores
bowl['eco_ratio'] = (bowl['eco_base']/bowl['economy'].replace(0,np.nan)).clip(0,2.5)
bowl['dot_ratio'] = (bowl['dot_pct']/bowl['dot_base'].replace(0,np.nan)).clip(0,2.5)

wpa_p95b = bowl['clutch_wpa_mean'].quantile(0.95)
bowl['wpa_score']  = (bowl['clutch_wpa_mean']/wpa_p95b*100).clip(-50,100)
bowl['eco_score']  = ((1-bowl['economy']/15)*100).clip(0,100)
bowl['wkt_score']  = (bowl['wkt_pct']*15).clip(0,100)
bowl['dot_score']  = (bowl['dot_pct']/60*100).clip(0,100)
bowl['ratio_score']= ((bowl['eco_ratio'].fillna(1)+bowl['dot_ratio'].fillna(1))/2*50).clip(0,100)
bowl['shutdown_per_10'] = bowl['shutdown_overs']/bowl['balls']*60
bowl['shutdown_score']  = (bowl['shutdown_per_10']*12).clip(0,30)
bowl['win_score']  = (bowl['win_pct']-50).clip(-20,20)
bowl['comeback_score'] = (bowl['comeback_spells'] / bowl['total_matches'] * 60).clip(0, 25)
bowl['importance_score'] = ((bowl['avg_importance'] - 1.0) * 80).clip(0, 20)
bowl['ultra_score'] = (bowl['ultra_wpa'] / bowl['ultra_balls'].replace(0,np.nan) * 500).fillna(0).clip(0, 20)
bowl['vol_adj'] = np.minimum(bowl['balls'] / 200, 1.0)

bowl['raw_score'] = (
    0.30 * bowl['wpa_score'].fillna(0) +
    0.18 * bowl['eco_score'] +
    0.12 * bowl['wkt_score'] +
    0.08 * bowl['dot_score'] +
    0.08 * bowl['ratio_score'].fillna(50) +
    0.08 * bowl['shutdown_score'] +
    0.06 * bowl['comeback_score'] +
    0.05 * bowl['importance_score'] +
    0.05 * bowl['ultra_score']
)
bowl['bowling_clutch_score'] = (bowl['raw_score'] * bowl['vol_adj']).clip(0, 100)

bowl_top = bowl.sort_values('bowling_clutch_score', ascending=False).head(25)

print(f"\nEligible bowlers: {len(bowl)}")
print("\nTOP 15 BOWLERS:")
for i, row in bowl_top.head(15).reset_index(drop=True).iterrows():
    print(f"  #{i+1:2d}: {row['bowler_name']:<26} "
          f"B={int(row['balls']):<4} Eco={row['economy']:.2f} Wkts={int(row['wkts'])} "
          f"WPA={row['clutch_wpa']:.3f} SD={int(row['shutdown_overs'])} "
          f"CB={int(row['comeback_spells'])} Imp={row['avg_importance']:.2f} "
          f"Scr={row['bowling_clutch_score']:.2f}")

# Save
bat.to_parquet('bat_rankings_v3.parquet', index=False)
bowl.to_parquet('bowl_rankings_v3.parquet', index=False)
valid.to_parquet('valid_v3.parquet', index=False)

print("\nAll v3 files saved.")
