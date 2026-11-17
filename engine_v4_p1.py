"""
SupeRR Selector v4 — Aliveness-Conditioned Pressure + Choke Penalty
=====================================================================
Key fixes:
  1. Match Aliveness filter: WP 25-75% = genuinely contested
  2. Phase pressure buckets: death alive-chase gets highest weight
  3. Choke penalty: -1.5x negative WPA in high-pressure situations
  4. Proper LI boost for alive-match balls
  5. All-new composite rankings
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import warnings; warnings.filterwarnings('ignore')

print("=" * 60)
print("PHASE 1: Load & Rebuild WP Model with better features")
print("=" * 60)

bbb     = pd.read_csv('6af458274c1e8_data_pack/Data Pack/ball_by_ball.csv')
matches = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')
comps   = pd.read_csv('6af458274c1e8_data_pack/Data Pack/competitions.csv')

bbb = bbb[bbb['innings'].isin([1,2])].copy()
bbb = bbb.merge(matches[['match_id','comp_id','stage','knock_out','win_team_id']], on='match_id', how='left')
bbb = bbb.merge(comps[['comp_id','match_format','comp_name','season']], on='comp_id', how='left')
bbb = bbb[bbb['win_team_id'].notna()].copy()
bbb['win_team_id'] = bbb['win_team_id'].astype(int)

bbb['is_valid'] = ~bbb['extras_type'].isin(['wide','Overstep'])
bbb['is_valid_wicket'] = bbb['is_wicket'] & ~bbb['dismissal_type'].isin(['RetiredHurt'])
bbb['total_ball_runs'] = bbb['runs'] + bbb['extras1_runs'].fillna(0)
bbb['bowler_runs'] = np.where(bbb['extras_type'].isin(['byes','legbyes']),
                               bbb['extras1_runs'].fillna(0), bbb['total_ball_runs'])

bbb = bbb.sort_values(['match_id','innings','innings_ball_num']).reset_index(drop=True)

# Cumulative state
bbb['valid_flag'] = bbb['is_valid'].astype(int)
bbb['valid_balls_before'] = bbb.groupby(['match_id','innings'])['valid_flag'].transform(lambda x: x.shift(1).fillna(0).cumsum()).astype(int)
bbb['runs_before'] = bbb.groupby(['match_id','innings'])['total_ball_runs'].transform(lambda x: x.shift(1).fillna(0).cumsum())
bbb['wickets_before'] = bbb.groupby(['match_id','innings'])['is_valid_wicket'].transform(lambda x: x.shift(1).fillna(0).cumsum()).astype(int)
bbb['balls_remaining'] = (120 - bbb['valid_balls_before']).clip(lower=1)
bbb['wickets_remaining'] = (10 - bbb['wickets_before']).clip(lower=0)
bbb['current_rr'] = bbb['runs_before'] * 6 / bbb['valid_balls_before'].replace(0, np.nan).fillna(0)

# Innings 1 totals → target
inn1t = bbb[bbb['innings']==1].groupby('match_id')['total_ball_runs'].sum().reset_index(name='inn1_total')
inn1t['target'] = inn1t['inn1_total'] + 1
bbb = bbb.merge(inn1t[['match_id','target']], on='match_id', how='left')

bbb['runs_needed'] = np.where(bbb['innings']==2, (bbb['target'] - bbb['runs_before']).clip(lower=0), np.nan)
bbb['required_rr'] = np.where((bbb['innings']==2) & (bbb['balls_remaining']>0),
    bbb['runs_needed']*6/bbb['balls_remaining'], np.nan)
bbb['rr_gap'] = (bbb['required_rr'] - bbb['current_rr']).fillna(0)
bbb['batting_team_won'] = (bbb['batting_team_id'] == bbb['win_team_id']).astype(int)

is_knockout = ((bbb['knock_out']==1) | bbb['stage'].isin(['Final','Semi Final','Qualifier','Eliminator']))
bbb['is_knockout'] = is_knockout.astype(int)

# Match importance
def get_importance(row):
    stage = str(row['stage']).lower() if pd.notna(row['stage']) else ''
    if 'final' == stage: return 2.5
    elif 'semi' in stage: return 2.2
    elif 'qualifier' in stage or 'eliminator' in stage: return 2.0
    elif row['knock_out']==1: return 2.0
    elif 'super' in stage: return 1.5
    else: return 1.2 if row.get('late_match',0) else 1.0

match_meta = matches[['match_id','comp_id','stage','knock_out','match_number']].copy()
comp_total = matches.groupby('comp_id')['match_id'].count().reset_index(name='total')
match_meta = match_meta.merge(comp_total, on='comp_id', how='left')
match_meta['match_pct'] = match_meta['match_number'] / match_meta['total']
match_meta['late_match'] = (match_meta['match_pct'] > 0.65).astype(int)
match_meta['match_importance'] = match_meta.apply(get_importance, axis=1)
# IPL bonus
ipl_comps = comps[comps['comp_name'].str.contains('IPL|Indian Premier', case=False, na=False)]['comp_id']
match_meta['is_ipl'] = match_meta['comp_id'].isin(ipl_comps).astype(int)
match_meta['match_importance'] = match_meta['match_importance'] * np.where(match_meta['is_ipl']==1, 1.15, 1.0)
bbb = bbb.merge(match_meta[['match_id','match_importance']], on='match_id', how='left')
bbb['match_importance'] = bbb['match_importance'].fillna(1.0)

# Rolling context
bbb['recent_dots_5'] = bbb.groupby(['match_id','innings'], group_keys=False).apply(
    lambda g: (g['runs']==0).astype(int).rolling(5,min_periods=1).sum().shift(1).fillna(0))
bbb['recent_wickets_5'] = bbb.groupby(['match_id','innings'], group_keys=False).apply(
    lambda g: g['is_valid_wicket'].astype(int).rolling(5,min_periods=1).sum().shift(1).fillna(0))

# Over run rate
over_rr = (bbb[bbb['is_valid']].groupby(['match_id','innings','overid'])
    .agg(over_runs=('total_ball_runs','sum'), over_balls=('valid_flag','sum')).reset_index())
over_rr['over_rr'] = over_rr['over_runs'] / over_rr['over_balls'] * 6
over_rr['prev_over_rr'] = over_rr.groupby(['match_id','innings'])['over_rr'].shift(1)
over_rr['recent_avg_rr'] = over_rr.groupby(['match_id','innings'])['over_rr'].transform(lambda x: x.rolling(2,min_periods=1).mean().shift(1))
bbb = bbb.merge(over_rr[['match_id','innings','overid','over_rr','recent_avg_rr']], on=['match_id','innings','overid'], how='left')

print(f"Dataset: {len(bbb):,} balls | {bbb['match_id'].nunique()} matches")

# ═══════════════════════════════════════════════════════
# PHASE 2: WIN PROBABILITY MODEL (re-trained with richer features)
# ═══════════════════════════════════════════════════════
print("\nPHASE 2: Training WP Models...")

FEAT1 = ['overid','valid_balls_before','balls_remaining','wickets_remaining',
         'wickets_before','runs_before','current_rr','is_knockout','match_importance']
FEAT2 = ['overid','valid_balls_before','balls_remaining','wickets_remaining',
         'wickets_before','runs_before','runs_needed','required_rr','current_rr',
         'rr_gap','is_knockout','target','match_importance']

params = dict(objective='binary', metric='auc', learning_rate=0.03,
    num_leaves=127, n_estimators=600, min_child_samples=20,
    feature_fraction=0.85, bagging_fraction=0.85, bagging_freq=5,
    reg_alpha=0.1, reg_lambda=1.0, verbose=-1)

m1_df = bbb[bbb['innings']==1].dropna(subset=['batting_team_won'])
X1 = m1_df[FEAT1].fillna(0); y1 = m1_df['batting_team_won']
X1tr,X1va,y1tr,y1va = train_test_split(X1,y1,test_size=0.2,random_state=42)
wp1 = lgb.LGBMClassifier(**params)
wp1.fit(X1tr,y1tr,eval_set=[(X1va,y1va)],callbacks=[lgb.early_stopping(40,verbose=False)])
print(f"Inn1 WP  AUC={roc_auc_score(y1va,wp1.predict_proba(X1va)[:,1]):.4f}")

m2_df = bbb[(bbb['innings']==2) & bbb['runs_needed'].notna()]
X2 = m2_df[FEAT2].fillna(0); y2 = m2_df['batting_team_won']
X2tr,X2va,y2tr,y2va = train_test_split(X2,y2,test_size=0.2,random_state=42)
wp2 = lgb.LGBMClassifier(**params)
wp2.fit(X2tr,y2tr,eval_set=[(X2va,y2va)],callbacks=[lgb.early_stopping(40,verbose=False)])
print(f"Inn2 WP  AUC={roc_auc_score(y2va,wp2.predict_proba(X2va)[:,1]):.4f}")

# Predict WP before
bbb['wp_before'] = np.nan
m1 = bbb['innings']==1
bbb.loc[m1,'wp_before'] = wp1.predict_proba(bbb.loc[m1,FEAT1].fillna(0))[:,1]
m2 = (bbb['innings']==2) & bbb['runs_needed'].notna()
bbb.loc[m2,'wp_before'] = wp2.predict_proba(bbb.loc[m2,FEAT2].fillna(0))[:,1]

# Vectorised WP after
def compute_wp_after(df):
    nw = df['wickets_before'] + df['is_valid_wicket'].astype(int)
    nv = df['valid_balls_before'] + df['is_valid'].astype(int)
    nr = df['runs_before'] + df['total_ball_runs']
    nwr = (10-nw).clip(lower=0); nbr = (120-nv).clip(lower=1)
    ncrr = nr*6/nv.replace(0,np.nan).fillna(0)
    nrn = (df['target']-nr).clip(lower=0)
    nrrr = nrn*6/nbr; ngap = nrrr-ncrr
    wa = pd.Series(np.nan, index=df.index)
    m1 = df['innings']==1
    if m1.sum():
        p1 = pd.DataFrame({'overid':df.loc[m1,'overid'],'valid_balls_before':nv[m1],
            'balls_remaining':nbr[m1],'wickets_remaining':nwr[m1],'wickets_before':nw[m1],
            'runs_before':nr[m1],'current_rr':ncrr[m1],'is_knockout':df.loc[m1,'is_knockout'],
            'match_importance':df.loc[m1,'match_importance']})
        wa[m1] = wp1.predict_proba(p1[FEAT1].fillna(0))[:,1]
    m2 = (df['innings']==2) & df['runs_needed'].notna()
    if m2.sum():
        p2 = pd.DataFrame({'overid':df.loc[m2,'overid'],'valid_balls_before':nv[m2],
            'balls_remaining':nbr[m2],'wickets_remaining':nwr[m2],'wickets_before':nw[m2],
            'runs_before':nr[m2],'runs_needed':nrn[m2],'required_rr':nrrr[m2],
            'current_rr':ncrr[m2],'rr_gap':ngap[m2],'is_knockout':df.loc[m2,'is_knockout'],
            'target':df.loc[m2,'target'],'match_importance':df.loc[m2,'match_importance']})
        wa[m2] = wp2.predict_proba(p2[FEAT2].fillna(0))[:,1]
    return wa

print("Computing WP after each delivery...")
bbb['wp_after'] = compute_wp_after(bbb)
bbb['wpa_batting'] = bbb['wp_after'] - bbb['wp_before']
bbb['wpa_bowling'] = bbb['wp_before'] - bbb['wp_after']

# LI
def sim_wp(df, r, wkt):
    nw = df['wickets_before'] + wkt; nv = df['valid_balls_before']+1
    nr = df['runs_before'] + r; nwr=(10-nw).clip(0); nbr=(120-nv).clip(1)
    ncrr=nr*6/nv; nrn=(df['target']-nr).clip(0); nrrr=nrn*6/nbr; ngap=nrrr-ncrr
    wa = pd.Series(np.nan, index=df.index)
    m1=df['innings']==1
    if m1.sum():
        p=pd.DataFrame({'overid':df.loc[m1,'overid'],'valid_balls_before':nv[m1],
            'balls_remaining':nbr[m1],'wickets_remaining':nwr[m1],'wickets_before':nw[m1],
            'runs_before':nr[m1],'current_rr':ncrr[m1],'is_knockout':df.loc[m1,'is_knockout'],
            'match_importance':df.loc[m1,'match_importance']})
        wa[m1]=wp1.predict_proba(p[FEAT1].fillna(0))[:,1]
    m2=(df['innings']==2)&df['runs_needed'].notna()
    if m2.sum():
        p=pd.DataFrame({'overid':df.loc[m2,'overid'],'valid_balls_before':nv[m2],
            'balls_remaining':nbr[m2],'wickets_remaining':nwr[m2],'wickets_before':nw[m2],
            'runs_before':nr[m2],'runs_needed':nrn[m2],'required_rr':nrrr[m2],
            'current_rr':ncrr[m2],'rr_gap':ngap[m2],'is_knockout':df.loc[m2,'is_knockout'],
            'target':df.loc[m2,'target'],'match_importance':df.loc[m2,'match_importance']})
        wa[m2]=wp2.predict_proba(p[FEAT2].fillna(0))[:,1]
    return wa

print("Computing Leverage Index...")
wp_six  = sim_wp(bbb, 6, 0)
wp_wkt  = sim_wp(bbb, 0, 1)
bbb['leverage_index'] = (wp_six - wp_wkt).abs()

# ── ALIVENESS BOOST  ──────────────────────────────────────────
# Match is "alive" when WP is between 0.20 and 0.80
# Aliveness weight = 1 + 4*(0.5 - |wp - 0.5|) for wp in [0.20,0.80], else 0
bbb['wp_aliveness'] = np.where(
    bbb['wp_before'].between(0.20, 0.80),
    1 + 4*(0.5 - (bbb['wp_before'] - 0.5).abs()),
    0.1  # near-dead matches get minimal weight
)
bbb['li_alive'] = bbb['leverage_index'] * bbb['wp_aliveness']

# Normalise aliveness-adjusted LI
li_p95 = bbb[bbb['is_valid']]['li_alive'].quantile(0.95)
bbb['li_norm'] = (bbb['li_alive'] / li_p95).clip(0, 4)

print(f"LI (aliveness-adj) — mean: {bbb[bbb['is_valid']]['li_alive'].mean():.4f}  p95: {li_p95:.4f}")

# Check new LI distribution by phase
valid = bbb[bbb['is_valid']].copy()
valid['phase'] = pd.cut(valid['overid'], bins=[0,6,10,15,20],
    labels=['PP(1-6)','Mid(7-10)','Late(11-15)','Death(16-20)'])
grp = valid.groupby(['innings','phase'])['li_norm'].agg(['mean','median'])
print("\nAliveness-adjusted LI by phase:")
print(grp)

bbb.to_parquet('bbb_v4.parquet', index=False)
print("\nSaved bbb_v4.parquet")
