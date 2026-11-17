import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
print('Loading WPA data...')
df = pd.read_parquet('bbb_v2_wpa.parquet')

valid = df[df['is_valid']].copy()
LI_THRESHOLD = valid['leverage_index_norm'].quantile(0.70)
LI_SUPER     = valid['leverage_index_norm'].quantile(0.85)

valid['recent_wicket_3'] = (valid.groupby(['match_id','innings'], group_keys=False)
    .apply(lambda g: g['is_valid_wicket'].astype(int).rolling(3,min_periods=1).sum().shift(1).fillna(0)))
valid['under_dot_stress'] = (valid['recent_dots_5'] >= 3) | (valid['recent_wicket_3'] >= 1)

valid['ctx_flags'] = (
    (valid['overid'] >= 17).astype(int) +
    ((valid['overid'].isin([5,6])) & (valid['innings']==1)).astype(int) +
    valid['required_rr'].fillna(0).gt(9).astype(int) +
    (valid['recent_wickets_5'] >= 2).astype(int) +
    (valid['recent_dots_5'] >= 3).astype(int) +
    ((valid['innings']==2) & (valid['target'] >= 185)).astype(int) +
    (valid['is_knockout'] == 1).astype(int) +
    ((valid['wickets_remaining'] <= 3) & (valid['overid'] >= 15)).astype(int)
)
valid['is_high_pressure'] = (valid['leverage_index_norm'] >= LI_THRESHOLD) & (valid['ctx_flags'] >= 1)
valid['is_super_pressure'] = (valid['leverage_index_norm'] >= LI_SUPER) & (valid['ctx_flags'] >= 2)
valid['is_pressure_release'] = (valid['under_dot_stress'] & (valid['total_ball_runs'] >= 4) & valid['is_high_pressure'])

valid.to_parquet('valid_v2.parquet', index=False)
n_hi  = int(valid['is_high_pressure'].sum())
n_rel = int(valid['is_pressure_release'].sum())
print('Saved valid_v2.parquet')
print('High-pressure:', n_hi, '|  Releases:', n_rel)
print('Pct:', round(n_hi/len(valid)*100,1))

# ─── over-level shutdown stats
over_stats = (valid.groupby(['match_id','innings','overid','bowler_id','bowler_name'])
    .agg(over_runs=('total_ball_runs','sum'), over_balls=('is_valid','sum'),
         over_wickets=('is_valid_wicket','sum'), recent_avg_rr=('recent_avg_rr','first'),
         batting_team_won=('batting_team_won','first'), is_knockout=('is_knockout','first'))
    .reset_index())
over_stats['over_economy'] = over_stats['over_runs'] / over_stats['over_balls'] * 6
over_stats['is_shutdown_over'] = ((over_stats['recent_avg_rr'] >= 9) &
    (over_stats['over_economy'] <= 6) & (over_stats['over_balls'] >= 5))
print('Shutdown overs:', int(over_stats['is_shutdown_over'].sum()))

# ─── BAT RANKINGS
hi   = valid[valid['is_high_pressure']].copy()
norm = valid[valid['leverage_index_norm'] < valid['leverage_index_norm'].quantile(0.30)].copy()
rel  = valid[valid['is_pressure_release']].copy()

MIN_BAT  = 100
MIN_BOWL = 80

def bat_m(d, mq=0):
    g = d.groupby(['striker_id','striker_name'])
    r = g.agg(balls=('runs','count'), runs=('runs','sum'),
              fours=('is_four','sum'), sixes=('is_six','sum'),
              dots=('runs', lambda x:(x==0).sum()), wkts_lost=('is_valid_wicket','sum'),
              wpa_sum=('wpa_batting','sum'), wpa_mean=('wpa_batting','mean'),
              avg_li=('leverage_index_norm','mean'), win_balls=('batting_team_won','sum')).reset_index()
    r['sr'] = r['runs']/r['balls']*100
    r['avg'] = r['runs']/r['wkts_lost'].replace(0,np.nan)
    r['dot_pct'] = r['dots']/r['balls']*100
    r['bdry_pct'] = (r['fours']+r['sixes'])/r['balls']*100
    r['win_contrib_pct'] = r['win_balls']/r['balls']*100
    if mq: r = r[r['balls']>=mq]
    return r

bat_hi   = bat_m(hi, MIN_BAT)
bat_norm = bat_m(norm, 20)
bat_wpa  = hi.groupby(['striker_id','striker_name']).agg(clutch_wpa=('wpa_batting','sum'),clutch_wpa_mean=('wpa_batting','mean')).reset_index()
bat_rel  = rel.groupby(['striker_id','striker_name']).agg(release_moments=('is_pressure_release','sum'),release_runs=('total_ball_runs','sum')).reset_index()

bat = bat_hi.merge(bat_norm[['striker_id','striker_name','sr','avg','dot_pct']].rename(columns={'sr':'sr_base','avg':'avg_base','dot_pct':'dot_base'}),on=['striker_id','striker_name'],how='left')
bat = bat.merge(bat_wpa, on=['striker_id','striker_name'], how='left')
bat = bat.merge(bat_rel, on=['striker_id','striker_name'], how='left')
bat['release_moments'] = bat['release_moments'].fillna(0)

bat['sr_ratio']  = (bat['sr']/bat['sr_base'].replace(0,np.nan)).clip(0,2.5)
bat['avg_ratio'] = (bat['avg']/bat['avg_base'].replace(0,np.nan)).clip(0,2.5)

wpa_p95 = bat['clutch_wpa_mean'].quantile(0.95)
bat['wpa_score']     = (bat['clutch_wpa_mean']/wpa_p95*100).clip(-50,100)
bat['sr_score']      = (bat['sr']/180*100).clip(0,100)
bat['ratio_score']   = ((bat['sr_ratio']+bat['avg_ratio'])/2*50).clip(0,100)
bat['release_per_50']= bat['release_moments']/bat['balls']*50
bat['release_score'] = (bat['release_per_50']*10).clip(0,25)
bat['win_score']     = (bat['win_contrib_pct']-50).clip(-25,25)
bat['vol_adj']       = np.minimum(bat['balls']/300,1.0)
bat['raw']           = (0.35*bat['wpa_score'].fillna(0) + 0.25*bat['sr_score'] +
                        0.20*bat['ratio_score'].fillna(50) + 0.12*bat['release_score'] +
                        0.08*bat['win_score'].fillna(0))
bat['batting_clutch_score'] = (bat['raw']*bat['vol_adj']).clip(0,100)

# ─── BOWL RANKINGS
def bowl_m(d, mq=0):
    g = d.groupby(['bowler_id','bowler_name'])
    r = g.agg(balls=('runs','count'), runs=('bowler_runs','sum'), wkts=('is_valid_wicket','sum'),
              dots=('runs',lambda x:(x==0).sum()), fours_con=('is_four','sum'), sixes_con=('is_six','sum'),
              wpa_sum=('wpa_bowling','sum'), wpa_mean=('wpa_bowling','mean'),
              avg_li=('leverage_index_norm','mean'), win_balls=('batting_team_won',lambda x:(x==0).sum())).reset_index()
    r['economy'] = r['runs']/r['balls']*6
    r['bowl_avg'] = r['runs']/r['wkts'].replace(0,np.nan)
    r['bowl_sr']  = r['balls']/r['wkts'].replace(0,np.nan)
    r['dot_pct']  = r['dots']/r['balls']*100
    r['bdry_conceded_pct'] = (r['fours_con']+r['sixes_con'])/r['balls']*100
    r['wkt_pct']  = r['wkts']/r['balls']*100
    if mq: r = r[r['balls']>=mq]
    return r

bowl_hi   = bowl_m(hi, MIN_BOWL)
bowl_norm = bowl_m(norm, 20)
bowl_wpa  = hi.groupby(['bowler_id','bowler_name']).agg(clutch_wpa=('wpa_bowling','sum'),clutch_wpa_mean=('wpa_bowling','mean')).reset_index()
shut_cr   = over_stats[over_stats['is_shutdown_over']].groupby(['bowler_id','bowler_name']).agg(
    shutdown_overs=('is_shutdown_over','sum'), shutdown_wkts=('over_wickets','sum')).reset_index()

bowl = bowl_hi.merge(bowl_norm[['bowler_id','bowler_name','economy','dot_pct']].rename(columns={'economy':'eco_base','dot_pct':'dot_base'}),on=['bowler_id','bowler_name'],how='left')
bowl = bowl.merge(bowl_wpa, on=['bowler_id','bowler_name'], how='left')
bowl = bowl.merge(shut_cr,  on=['bowler_id','bowler_name'], how='left')
bowl['shutdown_overs'] = bowl['shutdown_overs'].fillna(0)

bowl['eco_ratio']  = (bowl['eco_base']/bowl['economy'].replace(0,np.nan)).clip(0,2.5)
bowl['dot_ratio']  = (bowl['dot_pct']/bowl['dot_base'].replace(0,np.nan)).clip(0,2.5)
wpa_p95b = bowl['clutch_wpa_mean'].quantile(0.95)
bowl['wpa_score']  = (bowl['clutch_wpa_mean']/wpa_p95b*100).clip(-50,100)
bowl['eco_score']  = ((1-bowl['economy']/15)*100).clip(0,100)
bowl['wkt_score']  = (bowl['wkt_pct']*15).clip(0,100)
bowl['dot_score']  = bowl['dot_pct'].clip(0,70)
bowl['ratio_score']= ((bowl['eco_ratio']+bowl['dot_ratio'])/2*50).clip(0,100)
bowl['shutdown_per_10'] = bowl['shutdown_overs']/bowl['balls']*60
bowl['shutdown_score']  = (bowl['shutdown_per_10']*10).clip(0,25)
bowl['vol_adj']    = np.minimum(bowl['balls']/250,1.0)
bowl['raw']        = (0.35*bowl['wpa_score'].fillna(0) + 0.25*bowl['eco_score'] +
                      0.15*bowl['wkt_score'] + 0.10*bowl['dot_score']/70*100 +
                      0.10*bowl['ratio_score'].fillna(50) + 0.05*bowl['shutdown_score'])
bowl['bowling_clutch_score'] = (bowl['raw']*bowl['vol_adj']).clip(0,100)

bat.to_parquet('bat_rankings_v2.parquet', index=False)
bowl.to_parquet('bowl_rankings_v2.parquet', index=False)

print('\n=== TOP 10 BATTERS ===')
bt = bat.sort_values('batting_clutch_score',ascending=False).head(10).reset_index(drop=True)
for i,row in bt.iterrows():
    print(f"  #{i+1:2d}: {row['striker_name']:<28} Balls={int(row['balls']):<4} SR(P)={row['sr']:.1f} Avg(P)={row['avg']:.1f} WPA={row['clutch_wpa']:.3f} Rel={int(row['release_moments'])} Score={row['batting_clutch_score']:.2f}")

print('\n=== TOP 10 BOWLERS ===')
bw = bowl.sort_values('bowling_clutch_score',ascending=False).head(10).reset_index(drop=True)
for i,row in bw.iterrows():
    print(f"  #{i+1:2d}: {row['bowler_name']:<28} Balls={int(row['balls']):<4} Eco={row['economy']:.2f} Wkts={int(row['wkts'])} WPA={row['clutch_wpa']:.3f} SD={int(row['shutdown_overs'])} Score={row['bowling_clutch_score']:.2f}")

print('\nAll files saved.')
