import pandas as pd

b_logs = pd.read_parquet('d:/rr/bat_hp_match_logs.parquet')
bw_logs = pd.read_parquet('d:/rr/bowl_hp_match_logs.parquet')

print("\n--- SKY logs top high-WPA matches ---")
sky = b_logs[b_logs['striker_name'] == 'Suryakumar Yadav'].sort_values(by='hp_wpa', ascending=False).head(5)
print(sky[['match_date', 'player_team', 'opponent_team', 'comp_name', 'total_runs', 'total_balls', 'hp_wpa']].to_string())

print("\n--- Bumrah logs top high-WPA matches ---")
bum = bw_logs[bw_logs['bowler_name'] == 'Jasprit Bumrah'].sort_values(by='hp_wpa', ascending=False).head(5)
print(bum[['match_date', 'player_team', 'opponent_team', 'comp_name', 'total_wkts', 'total_runs', 'hp_wpa']].to_string())

print("\n--- Miller logs top high-WPA matches ---")
mil = b_logs[b_logs['striker_name'] == 'David Miller'].sort_values(by='hp_wpa', ascending=False).head(5)
print(mil[['match_date', 'player_team', 'opponent_team', 'comp_name', 'total_runs', 'total_balls', 'hp_wpa']].to_string())
