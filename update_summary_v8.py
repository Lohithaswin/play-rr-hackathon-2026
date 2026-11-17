import pandas as pd

bat_logs = pd.read_parquet('bat_hp_match_logs.parquet')
bowl_logs = pd.read_parquet('bowl_hp_match_logs.parquet')
bat_top = pd.read_parquet('bat_rankings_v8.parquet').head(10)
bowl_top = pd.read_parquet('bowl_rankings_v7.parquet').head(10)

with open('player_hp_summary.txt', 'w', encoding='utf-8') as f:
    f.write('=========================================================================================\n')
    f.write('           SUPER R SELECTOR v8 — AUTHENTIC HIGH-PRESSURE MATCH LOGS\n')
    f.write('   (Strict Cricket Criteria: No 4(4) / 9(3) Cameos unless Winning Death Chase Finish)\n')
    f.write('=========================================================================================\n\n')

    f.write('--- TOP 10 BATTERS UNDER PRESSURE ---\n\n')
    for _, r in bat_top.iterrows():
        pname = r['striker_name']
        p_matches = bat_logs[bat_logs['striker_name'] == pname].sort_values('hp_wpa', ascending=False)
        f.write(f"★ Rank {r['rank_bat']}: {pname} (Score: {r['batting_clutch_score']:.1f} | Matches: {r['matches']} | Authentic HP Matches: {len(p_matches)})\n")
        f.write(f"   Career HP Stats: Runs={int(r['hp_runs'])} | SR={r['hp_sr']:.1f} | HP-WPA={r['wpa_v5']:.2f} | Death-Alive WPA={r['da_wpa']:.2f}\n")
        f.write('   --------------------------------------------------------------------------------------\n')
        f.write('   Date       Comp / Opposition                 Runs (Balls)   HP-Runs (Balls)   HP-SR    HP-WPA   Result\n')
        f.write('   --------------------------------------------------------------------------------------\n')
        for _, m in p_matches.iterrows():
            res = 'WON' if m['batting_team_won'] == 1 else 'LOST'
            cname = str(m['comp_name'])[:30]
            f.write(f"   {str(m['match_date']):<10} {cname:<32} {int(m['total_runs']):3d} ({int(m['total_balls']):2d})     {int(m['hp_runs']):3d} ({int(m['hp_balls']):2d})       {m['hp_sr']:5.1f}   {m['hp_wpa']:6.2f}   {res}\n")
        f.write('\n')

    f.write('\n--- TOP 10 BOWLERS UNDER PRESSURE ---\n\n')
    for _, r in bowl_top.iterrows():
        pname = r['bowler_name']
        p_spells = bowl_logs[bowl_logs['bowler_name'] == pname].sort_values('hp_wpa', ascending=False)
        f.write(f"★ Rank {r['rank_bowl']}: {pname} (Score: {r['bowling_clutch_score']:.1f} | Matches: {r['matches']} | Authentic HP Spells: {len(p_spells)})\n")
        f.write(f"   Career HP Stats: Balls={int(r['hp_balls'])} | Eco={r['hp_economy']:.2f} | HP-WPA={r['wpa_v5']:.2f} | Death Saved={r['d_runs_saved']:.1f}\n")
        f.write('   --------------------------------------------------------------------------------------\n')
        f.write('   Date       Comp / Opposition                 Figures        HP-Overs (Runs-Wkts)  HP-Eco   HP-WPA   Result\n')
        f.write('   --------------------------------------------------------------------------------------\n')
        for _, m in p_spells.iterrows():
            res = 'WON' if m['bowling_team_won'] == 1 else 'LOST'
            cname = str(m['comp_name'])[:30]
            ov_str = f"{int(m['hp_balls'])}b ({int(m['hp_runs'])}r-{int(m['hp_wkts'])}w)"
            fig_str = f"{int(m['total_wkts'])}/{int(m['total_runs'])}"
            f.write(f"   {str(m['match_date']):<10} {cname:<32} {fig_str:<12}   {ov_str:<20}  {m['hp_economy']:5.2f}   {m['hp_wpa']:6.2f}   {res}\n")
        f.write('\n')

print('Successfully updated player_hp_summary.txt')
