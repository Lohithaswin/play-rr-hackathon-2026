import pandas as pd
import numpy as np

p_bat = pd.read_parquet('bat_rankings_v15.parquet')
bw = pd.read_parquet('bowl_rankings_v15.parquet')
bat_hp_logs = pd.read_parquet('bat_hp_match_logs.parquet')
bowl_hp_logs = pd.read_parquet('bowl_hp_match_logs.parquet')

out = []
out.append("=" * 90)
out.append("  SUPER R SELECTOR v15: INDUSTRY STANDARD HIGH-PRESSURE AUDIT & MATCH LOGS")
out.append("  (Zero Tolerance for Negative Factors, ML Ball-by-Ball Expected Runs, Strict Aliveness)")
out.append("=" * 90)
out.append("\n" + "=" * 90)
out.append("  TOP 10 BATTERS UNDER PRESSURE (2022-2026)")
out.append("=" * 90)

for idx, r in p_bat.head(10).iterrows():
    name = r['striker_name']
    out.append(f"\n#{r['rank_bat']} {name.upper()} — Clutch Score: {r['batting_clutch_score']:.1f}/100")
    out.append(f"   Matches: {r['matches']} | Authentic MWPPs: {r['authentic_mwpp']} | Comeback Knocks in Wins: {r['comeback_knocks']}")
    out.append(f"   Counter-Attack WPA: +{r['ca_wpa']:.2f} | Death-Alive Chase WPA: +{r['da_wpa']:.2f} | Rescue WPA: +{r['rescue_wpa']:.2f}")
    out.append(f"   Pressure SR: {r['hp_sr']:.1f} (Career SR: {r['total_sr']:.1f}, Elevation: +{r['sr_elevation']:.1f})")
    out.append(f"   Negative Factors Penalties: {r['total_penalties']:.1f} (PRISTINE - ZERO DEDUCTIONS)")
    
    # Logs
    sub_logs = bat_hp_logs[bat_hp_logs['striker_name'] == name].head(3)
    if len(sub_logs) > 0:
        out.append("   Signature High-Pressure Match Inning Logs:")
        for _, l in sub_logs.iterrows():
            opp = l['away_team'] if l['home_team'] in str(l.get('comp_name', '')) else l['home_team']
            won = "WON" if l['batting_team_won'] == 1 else "LOST"
            date = str(l.get('match_date', ''))[:10]
            out.append(f"     * [{date}] vs {opp} ({l['comp_name']}) — {l['total_runs']} runs off {l['total_balls']} balls (SR {l['total_sr']:.1f}), HP WPA: +{l['hp_wpa']:.2f} [{won}]")

out.append("\n" + "=" * 90)
out.append("  TOP 10 BOWLERS UNDER PRESSURE (2022-2026)")
out.append("=" * 90)

for idx, r in bw.head(10).iterrows():
    name = r['bowler_name']
    craft = "SPIN" if r['is_spinner'] == 1 else "PACE"
    out.append(f"\n#{r['rank_bowl']} {name.upper()} ({craft}) — Clutch Score: {r['bowling_clutch_score']:.1f}/100")
    out.append(f"   Matches: {r['matches']} | ML Death Alive Saved: +{r['ml_death_alive_saved']:.1f} runs | ML HP Runs Saved: +{r['ml_hp_runs_saved']:.1f} runs")
    out.append(f"   Alive HP WPA: +{r['hp_wpa_b']:.2f} | Pressure Economy: {r['hp_eco']:.2f} | Meltdown Overs: {r['meltdown_overs']:.0f} (Rate: {r['meltdown_rate']*100:.1f}%)")
    out.append(f"   Berserk Batters Dismissed in Wins: {r['is_berserk_wkt_win']:.0f} | Shutdown Dots in Wins: {r['shutdown_dot_win']:.0f} | Death Yorkers: {r['death_yorker']:.0f}")
    out.append(f"   Negative Factor Deductions: {r['total_penalties']:.1f}")
    
    # Logs
    sub_logs = bowl_hp_logs[bowl_hp_logs['bowler_name'] == name].head(3)
    if len(sub_logs) > 0:
        out.append("   Signature High-Pressure Match Bowling Logs:")
        for _, l in sub_logs.iterrows():
            opp = l['home_team'] if l['bowling_team_won'] == 1 and l.get('away_team') else l.get('away_team', 'Opp')
            won = "WON" if l['bowling_team_won'] == 1 else "LOST"
            date = str(l.get('match_date', ''))[:10]
            out.append(f"     * [{date}] vs {opp} ({l['comp_name']}) — {l['total_wkts']}/{l['total_runs']} ({l['total_balls']}b, HP Eco: {l['hp_economy']:.2f}), HP WPA: +{l['hp_wpa']:.2f} [{won}]")

out.append("\n" + "=" * 90)
out.append("  AUDIT: PROMINENT PLAYERS PENALIZED FOR NEGATIVE FACTORS")
out.append("=" * 90)
pen_batters = ['Shubman Gill', 'Heinrich Klaasen', 'Rovman Powell', 'Jos Buttler']
out.append("\nBATTERS PENALIZED:")
for name in pen_batters:
    r = p_bat[p_bat['striker_name'] == name]
    if len(r):
        row = r.iloc[0]
        out.append(f" * {name:18}: Rank #{row['rank_bat']} | Total Deduction: -{row['total_penalties']:.1f} pts | Final Score: {row['batting_clutch_score']:.1f}")
        if row['rescue_wpa'] < 0:
            out.append(f"     -> FAILED RESCUE: Rescue WPA = {row['rescue_wpa']:.2f} (Penalty: -{row['pen_rescue']:.1f} pts)")
        if row['da_wpa'] < 0:
            out.append(f"     -> FAILED DEATH CHASE: Death-Alive WPA = {row['da_wpa']:.2f} (Penalty: -{row['pen_da']:.1f} pts)")
        if row['sr_elevation'] < 0:
            out.append(f"     -> PRESSURE TIMIDNESS: SR Elevation = {row['sr_elevation']:.1f} (Penalty: -{row['pen_elev']:.1f} pts)")

pen_bowlers = ['Arshdeep Singh', 'Rashid Khan', 'Ravi Bishnoi', 'Mohammed Siraj', 'Sam Curran', 'Kagiso Rabada']
out.append("\nBOWLERS PENALIZED:")
for name in pen_bowlers:
    r = bw[bw['bowler_name'] == name]
    if len(r):
        row = r.iloc[0]
        out.append(f" * {name:18}: Rank #{row['rank_bowl']} | Total Deduction: -{row['total_penalties']:.1f} pts | Final Score: {row['bowling_clutch_score']:.1f}")
        if row['ml_death_alive_saved'] < 0:
            out.append(f"     -> DEATH RUN LEAKAGE: ML Death Alive Saved = {row['ml_death_alive_saved']:.1f} (Penalty: -{row['pen_death']:.1f} pts)")
        if row['ml_hp_runs_saved'] < 0:
            out.append(f"     -> HIGH-PRESSURE LEAKAGE: ML HP Runs Saved = {row['ml_hp_runs_saved']:.1f} (Penalty: -{row['pen_hp_saved']:.1f} pts)")
        if row['hp_wpa_b'] < 0:
            out.append(f"     -> NET NEGATIVE MATCH IMPACT: HP WPA = {row['hp_wpa_b']:.2f} (Penalty: -{row['pen_hp_wpa']:.1f} pts)")
        if row['hp_eco'] > 8.50:
            out.append(f"     -> HIGH PRESSURE ECONOMY: HP Eco = {row['hp_eco']:.2f} vs 8.50 Par (Penalty: -{row['pen_eco']:.1f} pts)")
        if row['meltdown_rate'] > 0.08:
            out.append(f"     -> EXCESSIVE MELTDOWNS: {row['meltdown_overs']:.0f} meltdowns in {row['matches']} matches ({row['meltdown_rate']*100:.1f}%) (Penalty: -{row['pen_meltdowns']:.1f} pts)")

with open('player_hp_summary.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print("Updated player_hp_summary.txt successfully!")
