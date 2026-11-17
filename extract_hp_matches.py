import pandas as pd, numpy as np

print("Loading data...")
valid = pd.read_parquet('valid_v6.parquet')
mat = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')
bat10 = pd.read_parquet('bat_rankings_v7.parquet').head(10)
bowl10 = pd.read_parquet('bowl_rankings_v7.parquet').head(10)

# Precompute columns for fast aggregation
valid['da_wpa_col'] = valid['wpa_bat_v5'] * valid['bucket_chase_death_alive']
valid['ca_wpa_col'] = valid['wpa_bat_v5'] * valid['is_counter_attack_ball']
valid['rescue_wpa_col'] = valid['wpa_bat_v5'] * valid['rescue_ball']
valid['cd_wpa_col'] = valid['wpa_bat_v5'] * valid['close_death_ball']

# --- BATTING MATCH LOGS ---
bat_match = valid.groupby(['match_id', 'innings', 'striker_id', 'striker_name', 'batting_team_won', 'comp_name', 'season']).agg(
    total_runs=('runs', 'sum'),
    total_balls=('valid_flag', 'sum'),
    fours=('is_four', 'sum'),
    sixes=('is_six', 'sum'),
    hp_balls=('is_high_pressure', 'sum'),
    hp_runs=('runs', lambda x: x[valid.loc[x.index, 'is_high_pressure'] == 1].sum()),
    wpa=('wpa_bat_v5', 'sum'),
    da_wpa=('da_wpa_col', 'sum'),
    ca_wpa=('ca_wpa_col', 'sum'),
    rescue_wpa=('rescue_wpa_col', 'sum'),
    cd_wpa=('cd_wpa_col', 'sum')
).reset_index()

bat_match = bat_match.merge(mat[['match_id', 'home_team', 'away_team', 'match_date', 'stage', 'result', 'man_of_the_match']], on='match_id', how='left')
bat_match['total_sr'] = bat_match['total_runs'] / bat_match['total_balls'].clip(lower=1) * 100
bat_match['hp_sr'] = bat_match['hp_runs'] / bat_match['hp_balls'].clip(lower=1) * 100
bat_match['is_mom'] = (bat_match['man_of_the_match'] == bat_match['striker_id']).astype(int)

# Definition of High Performance Match Under Pressure (Batting):
# HP WPA >= 0.50 OR (hp_balls >= 6 AND hp_sr >= 160 AND hp_runs >= 20) OR (da_wpa >= 1.0) OR (rescue_wpa >= 1.5)
bat_match['is_hp_performance'] = (
    (bat_match['hp_balls'] >= 3) &
    (
        (bat_match['wpa'] >= 0.50) |
        ((bat_match['hp_balls'] >= 6) & (bat_match['hp_sr'] >= 160.0) & (bat_match['hp_runs'] >= 20)) |
        (bat_match['da_wpa'] >= 1.0) |
        (bat_match['rescue_wpa'] >= 1.5)
    )
).astype(int)

# --- BOWLING MATCH LOGS ---
valid['da_wpa_b_col'] = valid['wpa_bowl_v5'] * valid['bucket_chase_death_alive']
valid['cd_wpa_b_col'] = valid['wpa_bowl_v5'] * valid['close_death_ball']

bowl_match = valid.groupby(['match_id', 'innings', 'bowler_id', 'bowler_name', 'batting_team_won', 'comp_name', 'season']).agg(
    total_balls=('valid_flag', 'sum'),
    total_runs=('bowler_runs', 'sum'),
    total_wkts=('is_valid_wicket', 'sum'),
    hp_balls=('is_high_pressure', 'sum'),
    hp_runs=('bowler_runs', lambda x: x[valid.loc[x.index, 'is_high_pressure'] == 1].sum()),
    hp_wkts=('is_valid_wicket', lambda x: x[valid.loc[x.index, 'is_high_pressure'] == 1].sum()),
    wpa=('wpa_bowl_v5', 'sum'),
    da_wpa=('da_wpa_b_col', 'sum'),
    cd_wpa=('cd_wpa_b_col', 'sum'),
    shutdown_overs=('is_shutdown_over', 'sum'),
    elite_shutdowns=('is_elite_shutdown', 'sum'),
    dy_balls=('death_yorker', 'sum')
).reset_index()

bowl_match = bowl_match.merge(mat[['match_id', 'home_team', 'away_team', 'match_date', 'stage', 'result', 'man_of_the_match']], on='match_id', how='left')
bowl_match['bowling_team_won'] = 1 - bowl_match['batting_team_won']
bowl_match['economy'] = bowl_match['total_runs'] / bowl_match['total_balls'].clip(lower=1) * 6
bowl_match['hp_economy'] = bowl_match['hp_runs'] / bowl_match['hp_balls'].clip(lower=1) * 6
bowl_match['is_mom'] = (bowl_match['man_of_the_match'] == bowl_match['bowler_id']).astype(int)

# Definition of High Performance Match Under Pressure (Bowling):
# HP WPA >= 0.50 OR (hp_balls >= 6 AND hp_economy <= 7.0) OR (hp_wkts >= 2) OR (shutdown_overs >= 1 AND hp_economy <= 8.0)
bowl_match['is_hp_performance'] = (
    (bowl_match['hp_balls'] >= 3) &
    (
        (bowl_match['wpa'] >= 0.50) |
        ((bowl_match['hp_balls'] >= 6) & (bowl_match['hp_economy'] <= 7.0)) |
        (bowl_match['hp_wkts'] >= 2) |
        ((bowl_match['shutdown_overs'] >= 1) & (bowl_match['hp_economy'] <= 8.0))
    )
).astype(int)

# Save full match logs for dashboard
bat_hp_matches = bat_match[bat_match['is_hp_performance'] == 1].sort_values('wpa', ascending=False).reset_index(drop=True)
bowl_hp_matches = bowl_match[bowl_match['is_hp_performance'] == 1].sort_values('wpa', ascending=False).reset_index(drop=True)

bat_hp_matches.to_parquet('bat_hp_match_logs.parquet', index=False)
bowl_hp_matches.to_parquet('bowl_hp_match_logs.parquet', index=False)
bat_hp_matches.to_csv('bat_hp_match_logs.csv', index=False)
bowl_hp_matches.to_csv('bowl_hp_match_logs.csv', index=False)

print(f"Total Batting HP Performances across all players: {len(bat_hp_matches)}")
print(f"Total Bowling HP Performances across all players: {len(bowl_hp_matches)}")

# Print counts for top 10
print("\n--- TOP 10 BATTERS HP PERFORMANCE MATCH COUNTS ---")
for name in bat10['striker_name']:
    count = (bat_hp_matches['striker_name'] == name).sum()
    print(f"  {name:<24}: {count} High-Performance Pressure Matches")

print("\n--- TOP 10 BOWLERS HP PERFORMANCE MATCH COUNTS ---")
for name in bowl10['bowler_name']:
    count = (bowl_hp_matches['bowler_name'] == name).sum()
    print(f"  {name:<24}: {count} High-Performance Pressure Matches")
