import pandas as pd

bat = pd.read_parquet('bat_rankings_final.parquet').head(10)
bowl = pd.read_parquet('bowl_rankings_final.parquet').head(10)

print("=== TOP 10 BATTERS ===")
for _, r in bat.iterrows():
    print(f"{r['rank_bat']}. {r['striker_name']}: Score={r['batting_clutch_score']:.1f}, CA_WPA={r['ca_wpa']:.2f}, Rescue={r['rescue_wpa']:.2f}, DA_WPA={r['da_wpa']:.2f}, MWPP={r['authentic_mwpp']}, Cons={r['hp_consistency_rate']*100:.1f}%, Ded={r['fair_deductions']:.1f}")

print("\n=== TOP 10 BOWLERS ===")
for _, r in bowl.iterrows():
    print(f"{r['rank_bowl']}. {r['bowler_name']}: Score={r['bowling_clutch_score']:.1f}, PP={r['ml_pp_runs_saved']:.1f}, Mid={r['ml_mid_runs_saved']:.1f}, Death={r['ml_death_runs_saved']:.1f}, Eco={r['hp_eco']:.2f}, Cons={r['hp_consistency_rate']*100:.1f}%, Ded={r['fair_deductions']:.1f}")
