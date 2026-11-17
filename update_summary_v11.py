import pandas as pd

bat_logs = pd.read_parquet('bat_hp_match_logs.parquet')
bowl_logs = pd.read_parquet('bowl_hp_match_logs.parquet')
bat_top = pd.read_parquet('bat_rankings_v11.parquet').head(10)
bowl_top = pd.read_parquet('bowl_rankings_v11.parquet').head(10)

with open('player_hp_summary.txt', 'w', encoding='utf-8') as f:
    f.write('=========================================================================================\n')
    f.write('           SUPER R SELECTOR v11 — INDUSTRY-STANDARD CLUTCH ENGINE\n')
    f.write('   (High Counter-Attack, Comeback Mastery, Tough Overs & Multiplied Negative Penalties)\n')
    f.write('=========================================================================================\n\n')

    f.write('--- TOP 10 BATTERS UNDER PRESSURE (v11: Zero Negative Tolerance) ---\n\n')
    for _, r in bat_top.iterrows():
        pname = r['striker_name']
        p_matches = bat_logs[bat_logs['striker_name'] == pname].sort_values('hp_wpa', ascending=False)
        f.write(f"★ Rank {r['rank_bat']}: {pname} (Score: {r['batting_clutch_score']:.1f} | Matches: {r['matches']} | Authentic HP Matches: {len(p_matches)} | Comebacks: {int(r['comeback_knocks'])})\n")
        f.write(f"   Career HP Stats: Runs={int(r['hp_runs'])} | SR={r['hp_sr']:.1f} | CA-WPA={r['ca_wpa']:.2f} | Rescue WPA={r['rescue_wpa']:.2f} | Death-Alive WPA={r['da_wpa']:.2f}\n")
        f.write('   --------------------------------------------------------------------------------------\n')
        f.write('   Date       Comp / Opposition                 Runs (Balls)   HP-Runs (Balls)   HP-SR    HP-WPA   Result\n')
        f.write('   --------------------------------------------------------------------------------------\n')
        for _, m in p_matches.iterrows():
            res = 'WON' if m['batting_team_won'] == 1 else 'LOST'
            cname = str(m['comp_name'])[:30]
            f.write(f"   {str(m['match_date']):<10} {cname:<32} {int(m['total_runs']):3d} ({int(m['total_balls']):2d})     {int(m['hp_runs']):3d} ({int(m['hp_balls']):2d})       {m['hp_sr']:5.1f}   {m['hp_wpa']:6.2f}   {res}\n")
        f.write('\n')

    f.write('\n--- TOP 10 BOWLERS UNDER PRESSURE (v11: 4 Elite Pacers, 6 Elite Spinners) ---\n\n')
    for _, r in bowl_top.iterrows():
        pname = r['bowler_name']
        b_type = "SPIN" if r['is_spinner'] == 1 else "PACE"
        p_spells = bowl_logs[bowl_logs['bowler_name'] == pname].sort_values('hp_wpa', ascending=False)
        f.write(f"★ Rank {r['rank_bowl']}: {pname} [{b_type}] (Score: {r['bowling_clutch_score']:.1f} | Matches: {r['matches']} | Authentic HP Spells: {len(p_spells)} | Comebacks: {int(r['comeback_spells'])})\n")
        f.write(f"   Clutch Metrics: Key Batter Pts={r['wkt_clutch_pts']:.1f} | Lev. Runs Saved={r['leverage_runs_saved']:.1f} | Meltdowns={int(r['meltdown_overs'])} ({r['meltdown_rate']*100:.1f}%)\n")
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

print('Successfully updated player_hp_summary.txt for v11')
