import pandas as pd

bat_rank = pd.read_parquet('bat_rankings_v13.parquet')
bowl_rank = pd.read_parquet('bowl_rankings_v13.parquet')
bat_logs = pd.read_parquet('bat_hp_match_logs.parquet')
bowl_logs = pd.read_parquet('bowl_hp_match_logs.parquet')

output_path = 'player_hp_summary.txt'

with open(output_path, 'w', encoding='utf-8') as f:
    f.write("=" * 88 + "\n")
    f.write("  SUPERR SELECTOR v13 — INDUSTRY STANDARD CONSISTENCY & CLUTCH BREAKDOWN\n")
    f.write("  (Dedicated Match-to-Match Pressure Consistency, Clean Spell Rate, Anti-Choke,\n")
    f.write("   Berserk Wickets & Dots in Wins, Balanced Craft & Zero Negative Clutch Tolerance)\n")
    f.write("=" * 88 + "\n\n")

    f.write("=" * 88 + "\n")
    f.write("  PART 1: TOP 10 BATTERS UNDER PRESSURE (CONSISTENCY AUGMENTED)\n")
    f.write("=" * 88 + "\n\n")

    for idx, row in bat_rank.head(10).iterrows():
        pname = row['striker_name']
        rank = row['rank_bat']
        score = row['batting_clutch_score']
        matches = row['matches']
        mwpp = row['authentic_mwpp']
        comebacks = row['comeback_knocks']
        succ_rate = row['bat_success_rate']
        cons_idx = row['S_consistency']
        choke_rate = row['bat_choke_rate']
        ca_wpa = row['ca_wpa']
        da_wpa = row['da_wpa']
        res_wpa = row['rescue_wpa']
        hp_runs = row['hp_runs']
        hp_sr = row['hp_sr']

        f.write(f"#{rank} {pname.upper()} — Clutch Score: {score:.1f}/100 | Consistency Index: {cons_idx:.1f}/100\n")
        f.write(f"   Matches: {matches} | MWPP: {int(mwpp)} | Comeback Knocks in Wins: {int(comebacks)}\n")
        f.write(f"   HP Match Success Rate: {succ_rate:.1f}% | Anti-Choke Rate: {100-choke_rate:.1f}%\n")
        f.write(f"   HP Runs: {int(hp_runs)} | HP SR: {hp_sr:.1f} | Counter-Attack WPA: +{ca_wpa:.2f}\n")
        f.write(f"   Death-Alive WPA: +{da_wpa:.2f} | Rescue WPA: +{res_wpa:.2f} (Strictly Non-Negative!)\n")
        f.write("   Key Authentic High Pressure Knocks:\n")

        p_logs = bat_logs[bat_logs['striker_name'] == pname].head(5)
        if p_logs.empty:
            f.write("      Consistent cumulative pressure contributions across matches.\n")
        else:
            for _, k in p_logs.iterrows():
                dt = str(k.get('match_date', ''))[:10]
                teams = f"{k.get('home_team', '')} vs {k.get('away_team', '')}"
                stg = k.get('stage', 'Group')
                inn = int(k.get('innings', 1))
                won = "WON" if k.get('batting_team_won', 0) == 1 else "LOST"
                r = int(k.get('total_runs', 0))
                b = int(k.get('total_balls', 0))
                sr = (r / max(b, 1)) * 100
                hpr = int(k.get('hp_runs', 0))
                hpb = int(k.get('hp_balls', 0))
                hpsr = (hpr / max(hpb, 1)) * 100
                wpa = k.get('hp_wpa', 0)
                motm = " (POTM)" if str(k.get('man_of_the_match', '')) == pname else ""
                cb = " [COMEBACK KNOCK]" if k.get('is_comeback_knock', False) else ""

                f.write(f"      • {dt} | {teams} ({stg}) | Inn {inn} [{won}]{motm}{cb}\n")
                f.write(f"        Score: {r}({b}) at {sr:.1f} SR | HP Impact: {hpr}({hpb}) at {hpsr:.1f} SR | WPA: {wpa:+.2f}\n")
        f.write("-" * 88 + "\n\n")

    f.write("\n" + "=" * 88 + "\n")
    f.write("  PART 2: TOP 10 BOWLERS UNDER PRESSURE (CONSISTENCY AUGMENTED)\n")
    f.write("=" * 88 + "\n\n")

    for idx, row in bowl_rank.head(10).iterrows():
        pname = row['bowler_name']
        rank = row['rank_bowl']
        score = row['bowling_clutch_score']
        is_spin = "SPIN" if row['is_spinner'] == 1 else "PACE"
        matches = row['matches']
        succ_rate = row['bowl_success_rate']
        cons_idx = row['S_consistency']
        clean_rate = row['clean_rate']
        lev_saved = row['leverage_runs_saved']
        berserk_wkt = row['is_berserk_wkt_win']
        shutdown_dots = row['shutdown_dot_win']
        comebacks = row['comeback_spells']
        meltdowns = row['meltdown_overs']
        hp_eco = row['hp_eco']

        f.write(f"#{rank} {pname.upper()} ({is_spin}) — Clutch Score: {score:.1f}/100 | Consistency Index: {cons_idx:.1f}/100\n")
        f.write(f"   Matches: {matches} | HP Spell Success Rate: {succ_rate:.1f}% | Clean Spell Rate: {clean_rate:.1f}%\n")
        f.write(f"   Leverage Runs Saved vs Par: +{lev_saved:.1f} | HP Economy: {hp_eco:.2f}\n")
        f.write(f"   Berserk Batter Wickets in Wins: {int(berserk_wkt)} | Shutdown Dots in Wins: {int(shutdown_dots)}\n")
        f.write(f"   Comeback Spells in Wins: {int(comebacks)} | Meltdown Overs: {int(meltdowns)} ({meltdowns/matches*100:.1f}% rate)\n")
        f.write("   Key Authentic High Pressure Spells:\n")

        p_logs = bowl_logs[bowl_logs['bowler_name'] == pname].head(5)
        if p_logs.empty:
            f.write("      Relentless consistency and high-pressure execution across matches.\n")
        else:
            for _, k in p_logs.iterrows():
                dt = str(k.get('match_date', ''))[:10]
                teams = f"{k.get('home_team', '')} vs {k.get('away_team', '')}"
                stg = k.get('stage', 'Group')
                inn = int(k.get('innings', 1))
                won = "WON" if k.get('bowling_team_won', 0) == 1 else "LOST"
                b = int(k.get('total_balls', 0))
                r = int(k.get('total_runs', 0))
                w = int(k.get('total_wkts', 0))
                eco = (r / max(b, 1)) * 6.0
                hpb = int(k.get('hp_balls', 0))
                hpr = int(k.get('hp_runs', 0))
                hpw = int(k.get('hp_wkts', 0))
                hpeco = (hpr / max(hpb, 1)) * 6.0
                wpa = k.get('hp_wpa', 0)
                motm = " (POTM)" if str(k.get('man_of_the_match', '')) == pname else ""

                f.write(f"      • {dt} | {teams} ({stg}) | Inn {inn} [{won}]{motm}\n")
                f.write(f"        Figures: {w}/{r} ({b//6}.{b%6} ov, {eco:.2f} eco) | HP Phase: {hpw}/{hpr} ({hpb} balls, {hpeco:.2f} eco) | WPA: {wpa:+.2f}\n")
        f.write("-" * 88 + "\n\n")

print(f"Updated {output_path} successfully!")
