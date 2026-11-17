import pandas as pd
valid = pd.read_parquet('valid_v6.parquet')
mat = pd.read_csv('6af458274c1e8_data_pack/Data Pack/matches.csv')

# Precompute columns for fast aggregation
valid['da_wpa_col'] = valid['wpa_bat_v5'] * valid['bucket_chase_death_alive']
valid['ca_wpa_col'] = valid['wpa_bat_v5'] * valid['is_counter_attack_ball']
valid['rescue_wpa_col'] = valid['wpa_bat_v5'] * valid['rescue_ball']
valid['cd_wpa_col'] = valid['wpa_bat_v5'] * valid['close_death_ball']

inn_bat = valid.groupby(['match_id', 'innings', 'striker_name', 'batting_team_won', 'target', 'comp_name', 'season']).agg(
    runs=('runs', 'sum'),
    balls=('valid_flag', 'sum'),
    fours=('is_four', 'sum'),
    sixes=('is_six', 'sum'),
    hp_balls=('is_high_pressure', 'sum'),
    wpa_v5=('wpa_bat_v5', 'sum'),
    da_wpa=('da_wpa_col', 'sum'),
    ca_wpa=('ca_wpa_col', 'sum'),
    rescue_wpa=('rescue_wpa_col', 'sum'),
    cd_wpa=('cd_wpa_col', 'sum')
).reset_index()

inn_bat = inn_bat.merge(mat[['match_id', 'home_team', 'away_team', 'match_date', 'stage', 'result']], on='match_id', how='left')
inn_bat['sr'] = inn_bat['runs'] / inn_bat['balls'] * 100

print('=== TOP 10 HIGH PRESSURE CHASE KNOCKS ===')
chase = inn_bat[(inn_bat['innings'] == 2) & (inn_bat['batting_team_won'] == 1) & (inn_bat['runs'] >= 30)].sort_values('wpa_v5', ascending=False)
for idx, r in chase.head(10).iterrows():
    print(f"{r['striker_name']} : {int(r['runs'])}* ({int(r['balls'])}) | SR: {r['sr']:.1f} | Total WPA: {r['wpa_v5']:.2f} | DA-WPA: {r['da_wpa']:.2f} | Match: {r['home_team']} vs {r['away_team']} ({r['comp_name']}, {r['stage']}) | Result: {r['result']}")

print('\n=== TOP 6 POST-COLLAPSE RESCUE KNOCKS ===')
rescue = inn_bat[(inn_bat['runs'] >= 35) & (inn_bat['rescue_wpa'] >= 2.5)].sort_values('rescue_wpa', ascending=False)
for idx, r in rescue.head(6).iterrows():
    print(f"{r['striker_name']} : {int(r['runs'])} ({int(r['balls'])}) | Rescue-WPA: {r['rescue_wpa']:.2f} | Total WPA: {r['wpa_v5']:.2f} | Match: {r['home_team']} vs {r['away_team']} ({r['comp_name']}) | Result: {r['result']}")

print('\n=== TOP 6 DEATH OVER CLUTCH FINISHES (HIGH DA-WPA) ===')
death_fin = inn_bat[(inn_bat['innings'] == 2) & (inn_bat['da_wpa'] >= 3.0)].sort_values('da_wpa', ascending=False)
for idx, r in death_fin.head(6).iterrows():
    print(f"{r['striker_name']} : {int(r['runs'])} ({int(r['balls'])}) | DA-WPA: {r['da_wpa']:.2f} | CD-WPA: {r['cd_wpa']:.2f} | Match: {r['home_team']} vs {r['away_team']} ({r['comp_name']}) | Result: {r['result']}")

inn_bowl = valid.groupby(['match_id', 'innings', 'bowler_name', 'batting_team_won', 'comp_name', 'season']).agg(
    balls=('valid_flag', 'sum'),
    runs=('bowler_runs', 'sum'),
    wkts=('is_valid_wicket', 'sum'),
    hp_balls=('is_high_pressure', 'sum'),
    wpa=('wpa_bowl_v5', 'sum'),
    shutdown_overs=('is_shutdown_over', 'sum'),
    dy_balls=('death_yorker', 'sum')
).reset_index()

inn_bowl = inn_bowl.merge(mat[['match_id', 'home_team', 'away_team', 'match_date', 'stage', 'result']], on='match_id', how='left')
inn_bowl['eco'] = inn_bowl['runs'] / inn_bowl['balls'] * 6

print('\n=== TOP 5 HIGH PRESSURE BOWLING SPELLS ===')
top_sp = inn_bowl[(inn_bowl['balls'] >= 18) & (inn_bowl['batting_team_won'] == 0)].sort_values('wpa', ascending=False)
for idx, r in top_sp.head(5).iterrows():
    print(f"{r['bowler_name']} : {int(r['wkts'])}/{int(r['runs'])} in {r['balls']/6:.1f} ov (Eco {r['eco']:.1f}) | WPA: {r['wpa']:.2f} | Shutdowns: {int(r['shutdown_overs'])} | Match: {r['home_team']} vs {r['away_team']} ({r['comp_name']}) | {r['result']}")

print('\n=== BUMRAH ICONIC PRESSURE DEFENSE SPELLS ===')
bum = inn_bowl[inn_bowl['bowler_name'] == 'Jasprit Bumrah'].sort_values('wpa', ascending=False)
for idx, r in bum.head(4).iterrows():
    print(f"Bumrah : {int(r['wkts'])}/{int(r['runs'])} in {r['balls']/6:.1f} ov (Eco {r['eco']:.1f}) | WPA: {r['wpa']:.2f} | Shutdowns: {int(r['shutdown_overs'])} | Match: {r['home_team']} vs {r['away_team']} ({r['comp_name']}) | {r['result']}")
