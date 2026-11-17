import pandas as pd
import numpy as np

valid = pd.read_parquet('valid_v7_ml.parquet')
valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['bowling_team_won'] = 1 - valid['batting_team_won']
valid['stakes'] = valid['match_importance'].fillna(1.0).clip(lower=1.0)

# Check run rate indicators
print('Current RR quantiles:')
print(valid['current_rr'].quantile([0.5, 0.75, 0.85, 0.90]))

# Batter going berserk definition
valid['striker_runs_cum'] = valid.groupby(['match_id', 'innings', 'striker_id'])['runs'].cumsum() - valid['runs']
valid['striker_balls_cum'] = valid.groupby(['match_id', 'innings', 'striker_id'])['valid_flag'].cumsum() - valid['valid_flag']
valid['striker_sr_cum'] = valid['striker_runs_cum'] / valid['striker_balls_cum'].clip(lower=1) * 100.0

is_berserk = (
    ((valid['striker_runs_cum'] >= 20) & (valid['striker_sr_cum'] >= 140.0)) |
    ((valid['striker_runs_cum'] >= 15) & (valid['striker_balls_cum'] <= 8)) |
    (valid['striker_runs_cum'] >= 35)
)

# High RR context: Batting team scoring fast (current_rr >= 9.0 or required_rr >= 9.5 or recent_avg_rr >= 9.5)
is_high_rr = (
    (valid['current_rr'] >= 9.0) |
    (valid['required_rr'] >= 9.5) |
    (valid['recent_avg_rr'] >= 9.5)
)

print(f'Total balls where batting team is at high RR: {is_high_rr.sum()}')
print(f'Total balls where batter is berserk: {is_berserk.sum()}')

# Dot balls under high RR in alive matches
dot_under_high_rr = (valid['bowler_runs'] == 0) & (valid['valid_flag'] == 1) & (valid['match_alive'] == True) & (is_high_rr | is_berserk)
print(f'Dot balls under High RR / Berserk in alive matches: {dot_under_high_rr.sum()}')

# Wickets in PP & Middle of key / berserk batters
is_key_batter = valid['batting_order'].fillna(9) <= 5
wkt_pp_key = valid['is_valid_wicket'] & is_key_batter & (valid['over_num'] <= 6) & (valid['match_alive'] == True)
wkt_mid_berserk = valid['is_valid_wicket'] & (is_berserk | is_key_batter) & valid['over_num'].between(7, 16) & (valid['match_alive'] == True)

print(f'Powerplay key batter wickets in alive matches: {wkt_pp_key.sum()}')
print(f'Middle overs key/berserk batter wickets in alive matches: {wkt_mid_berserk.sum()}')
