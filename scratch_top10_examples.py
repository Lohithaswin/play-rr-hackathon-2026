import pandas as pd

b_logs = pd.read_parquet('d:/rr/bat_hp_match_logs.parquet')
bw_logs = pd.read_parquet('d:/rr/bowl_hp_match_logs.parquet')

top_batters = [
    'David Miller', 'Suryakumar Yadav', 'Namboori Tilak Varma', 'Heinrich Klaasen',
    'Glenn Phillips', 'Shimron Hetmyer', 'Hardik Pandya', 'Virat Kohli',
    'Nicholas Pooran', 'Venkatesh Iyer'
]

print("=== TOP BATTERS MATCH EXAMPLES ===")
for p in top_batters:
    sub = b_logs[b_logs['striker_name'] == p].sort_values(by=['hp_wpa', 'total_runs'], ascending=False).head(3)
    print(f"\n--- {p} ---")
    for _, r in sub.iterrows():
        print(f"[{r['match_date']}] vs {r.get('opponent_team','Opp')} ({r.get('comp_name','')}) | Runs: {r['total_runs']} ({r['total_balls']}b) | HP SR: {r.get('hp_sr',0):.1f} | CA WPA: {r.get('ca_wpa',0):.2f} | Rescue WPA: {r.get('rescue_wpa',0):.2f} | Total WPA: +{r.get('hp_wpa',0):.2f} | Team Won: {r.get('batting_team_won',0)}")

top_bowlers = [
    'Jasprit Bumrah', 'Sunil Narine', 'Josh Hazlewood', 'Mustafizur Rahman',
    'Nathan Ellis', 'Bhuvneshwar Kumar', 'Rashid Khan', 'Axar Patel',
    'Varun Chakravarthy', 'Maheesh Theekshana'
]

print("\n\n=== TOP BOWLERS MATCH EXAMPLES ===")
for p in top_bowlers:
    sub = bw_logs[bw_logs['bowler_name'] == p].sort_values(by=['hp_wpa', 'total_wkts'], ascending=False).head(3)
    print(f"\n--- {p} ---")
    for _, r in sub.iterrows():
        print(f"[{r['match_date']}] vs {r.get('opponent_team','Opp')} ({r.get('comp_name','')}) | Figures: {r['total_wkts']}/{r['total_runs']} ({r['total_balls']}b) | HP Eco: {r.get('hp_economy',0):.2f} | Total WPA: +{r.get('hp_wpa',0):.2f} | Team Won: {r.get('bowling_team_won',0)}")
