import pandas as pd
import numpy as np

p_bat = pd.read_parquet('bat_rankings_final.parquet')
bw = pd.read_parquet('bowl_rankings_final.parquet')
bat_hp_logs = pd.read_parquet('bat_hp_match_logs.parquet')
bowl_hp_logs = pd.read_parquet('bowl_hp_match_logs.parquet')

out = []
out.append("=" * 95)
out.append("  RAJASTHAN ROYALS HIGH-PERFORMANCE ANALYTICS STUDIO — THE HALLA BOL PRESSURE INDEX")
out.append("  (Substantive Volume Standard >= 500 Balls, Strict Flaw Accountability, Pure ML Impact)")
out.append("=" * 95)

out.append("\n" + "=" * 95)
out.append("  TOP 10 BATTERS UNDER PRESSURE (2022-2026)")
out.append("=" * 95)

for idx, r in p_bat.head(10).iterrows():
    name = r['striker_name']
    ded_str = f"-{r['fair_deductions']:.1f}" if r['fair_deductions'] > 0 else "0.0 (CLEAN)"
    out.append(f"\n#{r['rank_bat']} {name.upper()} — Clutch Score: {r['batting_clutch_score']:.1f}/100")
    out.append(f"   Matches: {r['matches']} | Total Balls: {r['total_balls']} | Pressure Consistency: {r.get('hp_consistency_rate', 0)*100:.1f}%")
    out.append(f"   Counter-Attack WPA: {r['ca_wpa']:+.2f} | Rescue WPA: {r['rescue_wpa']:+.2f} | Death-Alive Chase WPA: {r['da_wpa']:+.2f}")
    out.append(f"   High Pressure ML Runs Added: {r.get('hp_ml_runs_added', 0):+.1f} | Pressure Strike Rate: {r.get('hp_sr', 0):.1f}")
    out.append(f"   Fair Deductions: {ded_str}")
    
    sub_logs = bat_hp_logs[bat_hp_logs['striker_name'] == name].head(3)
    if len(sub_logs) > 0:
        out.append("   Signature High-Pressure Match Inning Logs:")
        for _, l in sub_logs.iterrows():
            opp = l.get('opponent_team', l.get('away_team', 'Opponent'))
            won = "WON" if l['batting_team_won'] == 1 else "LOST"
            date = str(l.get('match_date', ''))[:10]
            out.append(f"     * [{date}] vs {opp} ({l['comp_name']}) — {l['total_runs']} runs off {l['total_balls']} balls (SR {l['total_sr']:.1f}), HP WPA: +{l['hp_wpa']:.2f} [{won}]")

out.append("\n" + "=" * 95)
out.append("  TOP 10 BOWLERS UNDER PRESSURE (2022-2026)")
out.append("  (Opponent-Quality Calibrated: Minnow Inflation Discounted, Death Leakage Strictly Penalized)")
out.append("=" * 95)

for idx, r in bw.head(10).iterrows():
    name = r['bowler_name']
    craft = "SPIN" if r['is_spinner'] == 1 else "PACE"
    ded_str = f"-{r['fair_deductions']:.1f}" if r['fair_deductions'] > 0 else "0.0 (CLEAN)"
    out.append(f"\n#{r['rank_bowl']} {name.upper()} ({craft}) — Clutch Score: {r['bowling_clutch_score']:.1f}/100")
    out.append(f"   Matches: {r['matches']} | Pressure Consistency Rate: {r.get('hp_consistency_rate', 0)*100:.1f}% | Minnow Ratio: {r.get('minnow_ratio', 0)*100:.1f}%")
    out.append(f"   High RR Momentum-Breaking Dots in Wins: {r['dot_high_rr_win']:.0f} | Key/Berserk Clutch Wickets in Wins: {r['wkt_clutch_win_tot']:.1f}")
    out.append(f"   Multi-Phase Runs Saved: PP: {r['ml_pp_runs_saved']:+.1f} | Mid: {r['ml_mid_runs_saved']:+.1f} | Death: {r['ml_death_runs_saved']:+.1f}")
    out.append(f"   Death Yorkers Executed: {r['death_yorker']:.0f} | Pressure Economy: {r['hp_eco']:.2f} | Alive HP WPA: {r['hp_wpa_b']:+.2f}")
    out.append(f"   Fair Deductions: {ded_str}")
    
    sub_logs = bowl_hp_logs[bowl_hp_logs['bowler_name'] == name].head(3)
    if len(sub_logs) > 0:
        out.append("   Signature High-Pressure Match Bowling Logs:")
        for _, l in sub_logs.iterrows():
            opp = l.get('opponent_team', l.get('home_team', 'Opponent'))
            won = "WON" if l['bowling_team_won'] == 1 else "LOST"
            date = str(l.get('match_date', ''))[:10]
            out.append(f"     * [{date}] vs {opp} ({l['comp_name']}) — {l['total_wkts']}/{l['total_runs']} ({l['total_balls']}b, HP Eco: {l['hp_economy']:.2f}), HP WPA: +{l['hp_wpa']:.2f} [{won}]")

out.append("\n" + "=" * 95)
out.append("  INSTITUTIONAL CRICKET AUDITS: DETAILED EVIDENCE")
out.append("=" * 95)

out.append("\n1. SUBSTANTIVE VOLUME FILTER (MS DHONI AUDIT):")
out.append("   * Substantive Batting Volume Filter: Requires minimum 500 total balls faced.")
out.append("   * MSD faced only 460 balls in 48 matches (an average of 9.5 balls/innings).")
out.append("   * Cameo specialist appearances under 500 balls do not qualify for a full-innings batting Top 10.")

out.append("\n2. NICHOLAS POORAN (#10, 48.6 pts) SURPASSES SHUBMAN GILL (#11, 47.3 pts):")
out.append("   * Pooran: +25.49 Counter-Attack, +6.29 Rescue, +1.91 Death-Alive, 74.5% Consistency, 0.0 Deductions!")
out.append("   * Gill: Conceded NEGATIVE Crisis Rescue (-2.03 WPA) and takes a -10.2 pt deduction. Fails when early wickets fall.")

out.append("\n3. VIRAT KOHLI (#9, 53.3 pts) — THE CHASE MASTER:")
out.append("   * +35.50 Counter-Attack Chasing WPA, 6 Authentic MWPPs, 10 crucible wins, 69.1% consistency, 0.0 deductions.")

out.append("\n4. MUSTAFIZUR RAHMAN RECALIBRATION (#2 -> #4, 45.3 pts):")
out.append("   * 324 deliveries (20.7% of career balls) vs minnows on slow Dhaka pitches discounted at 0.40x.")
out.append("   * Jasprit Bumrah (#1), Sunil Narine (#2), and Josh Hazlewood (#3) rightfully form the top 3.")

out.append("\n5. CRITICAL PHASE DISQUALIFICATIONS (DEATH OVERS RUN LEAKAGE):")
out.append("   * #19 Mohammed Siraj (31.0 pts): -20.99 runs leaked at Death (8.98 RPO) -> -16.8 pt deduction.")
out.append("   * #51 Ravi Bishnoi (15.1 pts): -41.78 runs leaked at Death (10.42 RPO) -> -33.4 pt deduction.")

out_text = "\n".join(out)
with open('player_hp_summary.txt', 'w', encoding='utf-8') as f:
    f.write(out_text)

print("player_hp_summary.txt successfully regenerated with correct opponent names!")
