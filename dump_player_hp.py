import pandas as pd
bat_hp = pd.read_parquet('bat_hp_match_logs.parquet')
bowl_hp = pd.read_parquet('bowl_hp_match_logs.parquet')
bat10 = pd.read_parquet('bat_rankings_v7.parquet').head(10)['striker_name'].tolist()
bowl10 = pd.read_parquet('bowl_rankings_v7.parquet').head(10)['bowler_name'].tolist()

with open('player_hp_summary.txt', 'w', encoding='utf-8') as f:
    f.write("======================================================================\n")
    f.write("      HIGH PERFORMANCE MATCHES UNDER PRESSURE (TOP 10 BATTERS)\n")
    f.write("======================================================================\n\n")

    for name in bat10:
        sub = bat_hp[bat_hp['striker_name'] == name].sort_values('wpa', ascending=False)
        f.write(f"### {name} — Total HP Pressure Matches: {len(sub)}\n")
        for idx, r in sub.iterrows():
            f.write(f"  • {r['match_date']} | {int(r['total_runs'])} ({int(r['total_balls'])}) [HP: {int(r['hp_runs'])} off {int(r['hp_balls'])}b, SR {r['hp_sr']:.1f}] | WPA: {r['wpa']:+.2f} | DA-WPA: {r['da_wpa']:+.2f} | Rescue: {r['rescue_wpa']:+.2f} | {r['home_team']} vs {r['away_team']} ({r['comp_name']}) | Result: {r['result']}\n")
        f.write("\n")

    f.write("\n======================================================================\n")
    f.write("      HIGH PERFORMANCE MATCHES UNDER PRESSURE (TOP 10 BOWLERS)\n")
    f.write("======================================================================\n\n")

    for name in bowl10:
        sub = bowl_hp[bowl_hp['bowler_name'] == name].sort_values('wpa', ascending=False)
        f.write(f"### {name} — Total HP Pressure Matches: {len(sub)}\n")
        for idx, r in sub.iterrows():
            f.write(f"  • {r['match_date']} | {int(r['total_wkts'])}/{int(r['total_runs'])} in {r['total_balls']/6:.1f} ov [HP: {int(r['hp_wkts'])} wkts, Eco {r['hp_economy']:.2f}] | WPA: {r['wpa']:+.2f} | Shutdowns: {int(r['shutdown_overs'])} | {r['home_team']} vs {r['away_team']} ({r['comp_name']}) | Result: {r['result']}\n")
        f.write("\n")

print("Dumped all matches to player_hp_summary.txt successfully!")
