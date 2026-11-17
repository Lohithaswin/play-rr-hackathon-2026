"""
SupeRR Selector v4 — Phase 2: Rankings with Choke Penalty
"""
import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')

print("Loading v4 WPA data...")
bbb = pd.read_parquet('bbb_v4.parquet')
valid = bbb[bbb['is_valid']].copy()

# ═══════════════════════════════════════════════════════
# PHASE-AWARE PRESSURE CLASSIFICATION
# ═══════════════════════════════════════════════════════
print("\nPhase-aware pressure classification...")

# MATCH ALIVE flag: WP between 20-80% (genuine contest)
valid['match_alive'] = valid['wp_before'].between(0.20, 0.80)

# Phase labels
valid['phase'] = pd.cut(valid['overid'], bins=[0,6,10,15,20],
    labels=['powerplay','middle','late','death'])

# ── 5 Pressure Buckets (priority order) ──
# BUCKET 1: Chase Death Alive (THE highest pressure in cricket)
valid['bucket_chase_death_alive'] = (
    (valid['innings']==2) & (valid['phase']=='death') & valid['match_alive'])

# BUCKET 2: Chase Late Alive (overs 11-15, match in balance)
valid['bucket_chase_late_alive'] = (
    (valid['innings']==2) & (valid['phase']=='late') & valid['match_alive'])

# BUCKET 3: Bat-first Death (setting, overs 16-20)
valid['bucket_bat_death'] = (
    (valid['innings']==1) & (valid['phase']=='death'))

# BUCKET 4: Chase PP (chasing, need to build platform)
valid['bucket_chase_pp'] = (
    (valid['innings']==2) & (valid['phase']=='powerplay') & valid['match_alive'])

# BUCKET 5: Bat-first PP end (overs 5-6, launching)
valid['bucket_bat_pp_end'] = (
    (valid['innings']==1) & (valid['overid'].isin([5,6])))

# BONUS flags (add to any bucket)
valid['f_quick_wkts']   = valid['recent_wickets_5'] >= 2
valid['f_dot_pileup']   = valid['recent_dots_5'] >= 3
valid['f_high_rrr']     = valid['required_rr'].fillna(0) > 9
valid['f_knockout']     = valid['is_knockout'] == 1
valid['f_collapse']     = (valid['wickets_remaining'] <= 3) & (valid['overid'] >= 15)
valid['f_important']    = valid['match_importance'] >= 1.5

# Phase-weighted LI threshold
# Different threshold per phase: death alive gets LOWER threshold (more inclusive)
LI_BASE = valid['li_norm'].quantile(0.60)
LI_HIGH = valid['li_norm'].quantile(0.72)

valid['is_high_pressure'] = (
    valid['bucket_chase_death_alive'] |
    valid['bucket_chase_late_alive'] |
    valid['bucket_bat_death'] |
    (
        (valid['li_norm'] >= LI_BASE) & (
            valid['bucket_chase_pp'] |
            valid['bucket_bat_pp_end'] |
            valid['f_quick_wkts'] |
            valid['f_knockout'] |
            (valid['f_high_rrr'] & (valid['innings']==2))
        )
    )
)

valid['is_elite_pressure'] = (
    valid['bucket_chase_death_alive'] |
    (valid['bucket_chase_late_alive'] & (valid['li_norm'] >= LI_HIGH)) |
    (valid['bucket_bat_death'] & (valid['li_norm'] >= LI_HIGH))
)

n_hi   = int(valid['is_high_pressure'].sum())
n_elite= int(valid['is_elite_pressure'].sum())
print(f"  High-pressure: {n_hi:,}  ({n_hi/len(valid)*100:.1f}%)")
print(f"  Elite-pressure: {n_elite:,} ({n_elite/len(valid)*100:.1f}%)")

# Phase breakdown
for col in ['bucket_chase_death_alive','bucket_chase_late_alive','bucket_bat_death',
            'bucket_chase_pp','bucket_bat_pp_end']:
    ct = int(valid[col].sum())
    print(f"    {col}: {ct:,}")

# ═══════════════════════════════════════════════════════
# IMPORTANCE & PHASE WEIGHTS
# ═══════════════════════════════════════════════════════
# Each ball gets a multiplier based on WHAT phase and HOW alive the match is
valid['phase_weight'] = np.select(
    [
        valid['bucket_chase_death_alive'],
        valid['bucket_chase_late_alive'],
        valid['bucket_bat_death'],
        valid['bucket_chase_pp'],
        valid['bucket_bat_pp_end'],
    ],
    [3.0, 2.2, 2.0, 1.5, 1.3],
    default=1.0
)

# Extra bonuses
valid['bonus_mult'] = (
    1.0 +
    valid['f_quick_wkts'].astype(float) * 0.3 +
    valid['f_dot_pileup'].astype(float) * 0.2 +
    valid['f_knockout'].astype(float) * 0.4 +
    valid['f_collapse'].astype(float) * 0.3 +
    valid['f_important'].astype(float) * 0.3
)

# Match importance multiplier
valid['imp_weight'] = valid['match_importance']

# Win multiplier
valid['win_mult_bat']  = np.where(valid['batting_team_won']==1, 1.3, 0.8)
valid['win_mult_bowl'] = np.where(valid['batting_team_won']==0, 1.3, 0.8)

# LI-based impact weight (higher for more critical balls)
valid['impact_weight'] = np.where(valid['li_norm'] >= 3.0, 2.5,
    np.where(valid['li_norm'] >= 2.0, 2.0,
    np.where(valid['li_norm'] >= 1.0, 1.5, 1.0)))

# ── ENHANCED WPA (fully weighted)
valid['wpa_bat_v4'] = (valid['wpa_batting'] * valid['phase_weight'] *
    valid['bonus_mult'] * valid['imp_weight'] * valid['win_mult_bat'] * valid['impact_weight'])
valid['wpa_bowl_v4'] = (valid['wpa_bowling'] * valid['phase_weight'] *
    valid['bonus_mult'] * valid['imp_weight'] * valid['win_mult_bowl'] * valid['impact_weight'])

# ═══════════════════════════════════════════════════════
# CHOKE DETECTION
# ═══════════════════════════════════════════════════════
print("\nChoke detection...")

# BATTER CHOKE: dismissed in high-pressure alive match
# (WPA is already negative when dismissed, but we add extra penalty)
valid['bat_choke_event'] = (
    valid['is_valid_wicket'] &
    valid['is_high_pressure'] &
    valid['match_alive']
)
# How bad is this choke? = raw WPA * phase_weight (already negative)
valid['bat_choke_wpa'] = np.where(valid['bat_choke_event'],
    valid['wpa_batting'] * valid['phase_weight'] * valid['imp_weight'], 0)

# BATTER BONUS: Scores 4+ in high-pressure (runs matter most in death)
valid['bat_clutch_hit'] = (
    valid['is_high_pressure'] &
    valid['match_alive'] &
    (valid['total_ball_runs'] >= 4)
)
valid['bat_clutch_hit_wpa'] = np.where(valid['bat_clutch_hit'],
    valid['wpa_batting'] * valid['phase_weight'] * valid['imp_weight'], 0)

# BOWLER CHOKE: concedes 4+ in high-pressure alive match
valid['bowl_choke_event'] = (
    (valid['total_ball_runs'] >= 4) &
    valid['is_high_pressure'] &
    valid['match_alive']
)
valid['bowl_choke_wpa'] = np.where(valid['bowl_choke_event'],
    valid['wpa_bowling'] * valid['phase_weight'] * valid['imp_weight'], 0)  # already negative

# BOWLER BONUS: wicket in high-pressure alive match
valid['bowl_clutch_wkt'] = (
    valid['is_valid_wicket'] &
    valid['is_high_pressure'] &
    valid['match_alive']
)
valid['bowl_clutch_wkt_wpa'] = np.where(valid['bowl_clutch_wkt'],
    valid['wpa_bowling'] * valid['phase_weight'] * valid['imp_weight'], 0)

n_bat_choke  = int(valid['bat_choke_event'].sum())
n_bowl_choke = int(valid['bowl_choke_event'].sum())
n_bat_hit    = int(valid['bat_clutch_hit'].sum())
n_bowl_wkt   = int(valid['bowl_clutch_wkt'].sum())
print(f"  Batter choke dismissals: {n_bat_choke:,}")
print(f"  Batter clutch hits (4+): {n_bat_hit:,}")
print(f"  Bowler choke boundaries: {n_bowl_choke:,}")
print(f"  Bowler clutch wickets: {n_bowl_wkt:,}")

# ═══════════════════════════════════════════════════════
# SHUTDOWN OVERS
# ═══════════════════════════════════════════════════════
over_stats = (valid.groupby(['match_id','innings','overid','bowler_id','bowler_name'])
    .agg(over_runs=('total_ball_runs','sum'), over_balls=('is_valid','sum'),
         over_wkts=('is_valid_wicket','sum'), recent_avg_rr=('recent_avg_rr','first'),
         match_imp=('match_importance','first'), alive_balls=('match_alive','sum'))
    .reset_index())
over_stats['over_eco'] = over_stats['over_runs'] / over_stats['over_balls'] * 6
# Shutdown = opp was scoring at 9+ RPO AND this over conceded ≤6, with match alive
over_stats['is_shutdown'] = (
    (over_stats['recent_avg_rr'] >= 9) &
    (over_stats['over_eco'] <= 6) &
    (over_stats['over_balls'] >= 5) &
    (over_stats['alive_balls'] >= 2)
)
# Super shutdown = opp at 10+ and conceded ≤4
over_stats['is_super_shutdown'] = (
    (over_stats['recent_avg_rr'] >= 10) &
    (over_stats['over_eco'] <= 4) &
    (over_stats['over_balls'] >= 5)
)
print(f"\n  Shutdown overs: {int(over_stats['is_shutdown'].sum()):,}")
print(f"  Super-shutdown overs: {int(over_stats['is_super_shutdown'].sum()):,}")

# ═══════════════════════════════════════════════════════
# COMEBACK FACTOR
# ═══════════════════════════════════════════════════════
bat_stints = (valid.groupby(['match_id','innings','striker_id','striker_name'])
    .agg(wp_in=('wp_before','first'), wp_out=('wp_after','last'),
         balls=('runs','count'), runs=('runs','sum'),
         wpa_total=('wpa_batting','sum')).reset_index())
bat_stints['wp_swing'] = bat_stints['wp_out'] - bat_stints['wp_in']
bat_stints['is_comeback'] = (bat_stints['wp_in']<0.35) & (bat_stints['wp_swing']>0.10) & (bat_stints['balls']>=10)
bat_stints['is_rescue']   = (bat_stints['wp_in']<0.20) & (bat_stints['wp_swing']>0.15) & (bat_stints['balls']>=8)
# Choke innings: entered with WP > 0.60, team lost (WP dropped during their innings)
bat_stints['is_choke_innings'] = (
    (bat_stints['wp_in'] > 0.50) & (bat_stints['wp_swing'] < -0.20) & (bat_stints['balls'] >= 15))
comeback_bat = bat_stints.groupby(['striker_id','striker_name']).agg(
    comeback_inn=('is_comeback','sum'), rescue_inn=('is_rescue','sum'),
    choke_innings=('is_choke_innings','sum'), avg_wp_swing=('wp_swing','mean')).reset_index()

bowl_stints = (valid.groupby(['match_id','innings','bowler_id','bowler_name'])
    .agg(wp_in=('wp_before','first'), wp_out=('wp_after','last'),
         balls=('runs','count'), wkts=('is_valid_wicket','sum'),
         wpa_total=('wpa_bowling','sum')).reset_index())
bowl_stints['wp_swing_bowl'] = bowl_stints['wp_in'] - bowl_stints['wp_out']  # bowling team perspective: reduce batting wp
# Comeback spell: batting team was cruising (WP>0.60), bowler pulled it back
bowl_stints['is_comeback_bowl'] = (
    (bowl_stints['wp_in']>0.60) & (bowl_stints['wp_swing_bowl']>0.10) & (bowl_stints['balls']>=6))
# Choke spell: bowled when batting team was struggling (WP<0.35) but let them back in
bowl_stints['is_choke_bowl'] = (
    (bowl_stints['wp_in']<0.40) & (bowl_stints['wp_swing_bowl']<-0.15) & (bowl_stints['balls']>=6))
comeback_bowl = bowl_stints.groupby(['bowler_id','bowler_name']).agg(
    comeback_spells=('is_comeback_bowl','sum'), choke_spells=('is_choke_bowl','sum')).reset_index()

print(f"\n  Batter comebacks: {int(bat_stints['is_comeback'].sum())}")
print(f"  Batter rescues:   {int(bat_stints['is_rescue'].sum())}")
print(f"  Batter choke inn: {int(bat_stints['is_choke_innings'].sum())}")
print(f"  Bowler comebacks: {int(bowl_stints['is_comeback_bowl'].sum())}")
print(f"  Bowler choke spl: {int(bowl_stints['is_choke_bowl'].sum())}")

# ═══════════════════════════════════════════════════════
# PHASE-SPLIT BATTING STATS
# ═══════════════════════════════════════════════════════
print("\nComputing phase-split stats...")

def phase_bat_stats(balls_df, phase_col=None):
    if phase_col:
        balls_df = balls_df[balls_df[phase_col]]
    g = balls_df.groupby(['striker_id','striker_name'])
    return g.agg(
        balls=('runs','count'), runs=('runs','sum'),
        wkts_lost=('is_valid_wicket','sum'),
        fours=('is_four','sum'), sixes=('is_six','sum'),
        dots=('runs',lambda x:(x==0).sum()),
        wpa=('wpa_bat_v4','sum'), wpa_mean=('wpa_bat_v4','mean'),
        wpa_raw=('wpa_batting','sum'),
        choke_wpa=('bat_choke_wpa','sum'),     # negative
        clutch_hit_wpa=('bat_clutch_hit_wpa','sum'),  # positive
        avg_li=('li_norm','mean'),
        win_balls=('batting_team_won','sum'),
        matches=('match_id','nunique'),
    ).reset_index().assign(
        sr=lambda d: d['runs']/d['balls']*100,
        avg=lambda d: d['runs']/d['wkts_lost'].replace(0,np.nan),
        dot_pct=lambda d: d['dots']/d['balls']*100,
        bdry_pct=lambda d: (d['fours']+d['sixes'])/d['balls']*100,
    )

hi   = valid[valid['is_high_pressure']].copy()
norm = valid[valid['li_norm'] < valid['li_norm'].quantile(0.25)].copy()
elite = valid[valid['is_elite_pressure']].copy()
p_rel = valid[valid['bat_clutch_hit']].copy()

bat_hi   = phase_bat_stats(hi)
bat_hi   = bat_hi[bat_hi['balls'] >= 80]
bat_norm = phase_bat_stats(norm)
bat_elite= phase_bat_stats(elite)

# Phase-specific death alive stats
bat_death_alive = phase_bat_stats(valid, 'bucket_chase_death_alive')
bat_death_set   = phase_bat_stats(valid, 'bucket_bat_death')

# Release moments
bat_release = p_rel.groupby(['striker_id','striker_name']).agg(
    release_moments=('bat_clutch_hit','sum')).reset_index()

# Choke dismissals
bat_choke_dim = valid[valid['bat_choke_event']].groupby(['striker_id','striker_name']).agg(
    choke_dismissals=('bat_choke_event','sum'),
    choke_wpa_total=('bat_choke_wpa','sum')).reset_index()

# Merge batting
bat = bat_hi.merge(bat_norm[['striker_id','sr','avg']].rename(
    columns={'sr':'sr_base','avg':'avg_base'}), on='striker_id', how='left')
bat = bat.merge(bat_elite[['striker_id','wpa','wpa_mean']].rename(
    columns={'wpa':'elite_wpa','wpa_mean':'elite_wpa_mean'}), on='striker_id', how='left')
bat = bat.merge(bat_death_alive[['striker_id','balls','runs','wpa','sr']].rename(
    columns={'balls':'da_balls','runs':'da_runs','wpa':'da_wpa','sr':'da_sr'}), on='striker_id', how='left')
bat = bat.merge(bat_death_set[['striker_id','balls','wpa']].rename(
    columns={'balls':'ds_balls','wpa':'ds_wpa'}), on='striker_id', how='left')
bat = bat.merge(bat_release, on=['striker_id','striker_name'], how='left')
bat = bat.merge(bat_choke_dim, on=['striker_id','striker_name'], how='left')
bat = bat.merge(comeback_bat, on=['striker_id','striker_name'], how='left')

for c in ['release_moments','choke_dismissals','choke_wpa_total','elite_wpa',
          'elite_wpa_mean','da_balls','da_wpa','da_sr','ds_balls','ds_wpa',
          'comeback_inn','rescue_inn','choke_innings']:
    bat[c] = bat[c].fillna(0)

print(f"Eligible batters: {len(bat)}")

# ── COMPOSITE BATTING SCORE v4
wpa_p95 = bat['wpa_mean'].quantile(0.95)
bat['wpa_score']       = (bat['wpa_mean'] / wpa_p95 * 100).clip(-50, 100)
bat['sr_score']        = (bat['sr'] / 190 * 100).clip(0, 100)
bat['sr_ratio']        = (bat['sr'] / bat['sr_base'].replace(0,np.nan)).clip(0, 2.5).fillna(1)
bat['avg_ratio']       = (bat['avg'] / bat['avg_base'].replace(0,np.nan)).clip(0, 2.5).fillna(1)
bat['ratio_score']     = ((bat['sr_ratio'] + bat['avg_ratio']) / 2 * 50).clip(0, 100)
bat['release_per_50']  = bat['release_moments'] / bat['balls'] * 50
bat['release_score']   = (bat['release_per_50'] * 15).clip(0, 30)
bat['comeback_score']  = ((bat['comeback_inn']*4 + bat['rescue_inn']*7) / bat['matches'].replace(0,1) * 40).clip(0, 30)

# Death alive chase: bonus for performing in THE most critical phase
bat['da_score']        = (bat['da_wpa'] * 5).clip(0, 25)

# CHOKE PENALTY: negative WPA from dismissals in pressure × 1.5 penalty
bat['choke_penalty']   = (bat['choke_wpa_total'].clip(-100, 0) * 1.5).clip(-50, 0)
bat['choke_inn_penalty']= -(bat['choke_innings'] / bat['matches'].replace(0,1) * 15).clip(0, 20)

# Volume adjustment
bat['vol_adj'] = np.minimum(bat['balls'] / 250, 1.0)

bat['raw_score'] = (
    0.32 * bat['wpa_score'].fillna(0) +
    0.14 * bat['sr_score'] +
    0.12 * bat['ratio_score'] +
    0.12 * bat['release_score'] +
    0.10 * bat['comeback_score'] +
    0.08 * bat['da_score'] +
    0.08 * bat['choke_penalty'] +  # already negative
    0.04 * bat['choke_inn_penalty']  # already negative
)
bat['batting_clutch_score'] = (bat['raw_score'] * bat['vol_adj']).clip(-20, 100)
bat_top = bat.sort_values('batting_clutch_score', ascending=False).head(25)

print("\nTOP 15 BATTERS (v4):")
for i, r in bat_top.head(15).reset_index(drop=True).iterrows():
    print(f"  #{i+1:2d}: {r['striker_name']:<26} "
          f"B={int(r['balls']):<4} SR={r['sr']:.1f} Avg={r['avg']:.1f} "
          f"WPA={r['wpa']:.2f} Rel={int(r['release_moments'])} "
          f"CB={int(r['comeback_inn'])} ChokeDis={int(r['choke_dismissals'])} "
          f"DA_WPA={r['da_wpa']:.2f} Score={r['batting_clutch_score']:.2f}")

# ══ BOWLING ══
def phase_bowl_stats(balls_df, phase_col=None):
    if phase_col:
        balls_df = balls_df[balls_df[phase_col]]
    g = balls_df.groupby(['bowler_id','bowler_name'])
    return g.agg(
        balls=('runs','count'), runs=('bowler_runs','sum'),
        wkts=('is_valid_wicket','sum'),
        dots=('runs',lambda x:(x==0).sum()),
        fours_con=('is_four','sum'), sixes_con=('is_six','sum'),
        wpa=('wpa_bowl_v4','sum'), wpa_mean=('wpa_bowl_v4','mean'),
        wpa_raw=('wpa_bowling','sum'),
        choke_wpa=('bowl_choke_wpa','sum'),
        clutch_wkt_wpa=('bowl_clutch_wkt_wpa','sum'),
        avg_li=('li_norm','mean'),
        win_balls=('batting_team_won',lambda x:(x==0).sum()),
        matches=('match_id','nunique'),
    ).reset_index().assign(
        economy=lambda d: d['runs']/d['balls']*6,
        dot_pct=lambda d: d['dots']/d['balls']*100,
        wkt_pct=lambda d: d['wkts']/d['balls']*100,
        bdry_pct=lambda d: (d['fours_con']+d['sixes_con'])/d['balls']*100,
    )

bowl_hi   = phase_bowl_stats(hi)
bowl_hi   = bowl_hi[bowl_hi['balls'] >= 60]
bowl_norm = phase_bowl_stats(norm)

# Phase-specific death alive stats for bowlers
bowl_death_alive = phase_bowl_stats(valid, 'bucket_chase_death_alive')
bowl_death_set   = phase_bowl_stats(valid, 'bucket_bat_death')

bowl_choke_dim = valid[valid['bowl_choke_event']].groupby(['bowler_id','bowler_name']).agg(
    choke_boundaries=('bowl_choke_event','sum'),
    choke_wpa_total=('bowl_choke_wpa','sum')).reset_index()

shut = over_stats[over_stats['is_shutdown']].groupby(['bowler_id','bowler_name']).agg(
    shutdown_overs=('is_shutdown','sum')).reset_index()
super_shut = over_stats[over_stats['is_super_shutdown']].groupby(['bowler_id','bowler_name']).agg(
    super_shutdown=('is_super_shutdown','sum')).reset_index()

bowl = bowl_hi.copy()
bowl = bowl.merge(bowl_norm[['bowler_id','economy','dot_pct']].rename(
    columns={'economy':'eco_base','dot_pct':'dot_base'}), on='bowler_id', how='left')
bowl = bowl.merge(bowl_death_alive[['bowler_id','balls','wpa','wkts']].rename(
    columns={'balls':'da_balls','wpa':'da_wpa','wkts':'da_wkts'}), on='bowler_id', how='left')
bowl = bowl.merge(bowl_death_set[['bowler_id','balls','wpa']].rename(
    columns={'balls':'ds_balls','wpa':'ds_wpa'}), on='bowler_id', how='left')
bowl = bowl.merge(bowl_choke_dim, on=['bowler_id','bowler_name'], how='left')
bowl = bowl.merge(comeback_bowl, on=['bowler_id','bowler_name'], how='left')
bowl = bowl.merge(shut, on=['bowler_id','bowler_name'], how='left')
bowl = bowl.merge(super_shut, on=['bowler_id','bowler_name'], how='left')

for c in ['da_balls','da_wpa','da_wkts','ds_balls','ds_wpa','choke_boundaries',
          'choke_wpa_total','comeback_spells','choke_spells','shutdown_overs','super_shutdown']:
    bowl[c] = bowl[c].fillna(0)

print(f"\nEligible bowlers: {len(bowl)}")

wpa_p95b = bowl['wpa_mean'].quantile(0.95)
bowl['wpa_score']     = (bowl['wpa_mean'] / wpa_p95b * 100).clip(-50, 100)
bowl['eco_score']     = ((1 - bowl['economy'] / 15) * 100).clip(0, 100)
bowl['eco_ratio']     = (bowl['eco_base'] / bowl['economy'].replace(0,np.nan)).clip(0, 2.5).fillna(1)
bowl['dot_ratio']     = (bowl['dot_pct'] / bowl['dot_base'].replace(0,np.nan)).clip(0, 2.5).fillna(1)
bowl['ratio_score']   = ((bowl['eco_ratio'] + bowl['dot_ratio']) / 2 * 50).clip(0, 100)
bowl['wkt_score']     = (bowl['wkt_pct'] * 15).clip(0, 100)
bowl['dot_score']     = (bowl['dot_pct'] / 65 * 100).clip(0, 100)
bowl['shutdown_score']= ((bowl['shutdown_overs'] + bowl['super_shutdown']*2) / bowl['matches'].replace(0,1) * 40).clip(0, 30)
bowl['comeback_score']= (bowl['comeback_spells'] / bowl['matches'].replace(0,1) * 50).clip(0, 25)
bowl['da_score']      = (bowl['da_wpa'] * 5 + bowl['da_wkts'] * 3).clip(0, 25)
# CHOKE PENALTY for bowlers
bowl['choke_penalty'] = (bowl['choke_wpa_total'].clip(-100, 0) * 1.5).clip(-50, 0)
bowl['choke_sp_pen']  = -(bowl['choke_spells'] / bowl['matches'].replace(0,1) * 15).clip(0, 20)
bowl['vol_adj'] = np.minimum(bowl['balls'] / 200, 1.0)

bowl['raw_score'] = (
    0.30 * bowl['wpa_score'].fillna(0) +
    0.16 * bowl['eco_score'] +
    0.10 * bowl['wkt_score'] +
    0.08 * bowl['dot_score'] +
    0.08 * bowl['ratio_score'] +
    0.10 * bowl['shutdown_score'] +
    0.08 * bowl['comeback_score'] +
    0.06 * bowl['da_score'] +
    0.04 * bowl['choke_penalty'] +
    0.00 * bowl['choke_sp_pen']
)
bowl['bowling_clutch_score'] = (bowl['raw_score'] * bowl['vol_adj']).clip(-20, 100)
bowl_top = bowl.sort_values('bowling_clutch_score', ascending=False).head(25)

print("\nTOP 15 BOWLERS (v4):")
for i, r in bowl_top.head(15).reset_index(drop=True).iterrows():
    print(f"  #{i+1:2d}: {r['bowler_name']:<26} "
          f"B={int(r['balls']):<4} Eco={r['economy']:.2f} Wkts={int(r['wkts'])} "
          f"WPA={r['wpa']:.2f} SD={int(r['shutdown_overs'])} "
          f"CB={int(r['comeback_spells'])} ChokeBdry={int(r['choke_boundaries'])} "
          f"DA_WPA={r['da_wpa']:.2f} Score={r['bowling_clutch_score']:.2f}")

# Save
bat.to_parquet('bat_rankings_v4.parquet', index=False)
bowl.to_parquet('bowl_rankings_v4.parquet', index=False)
valid.to_parquet('valid_v4.parquet', index=False)
print("\nAll v4 files saved.")
