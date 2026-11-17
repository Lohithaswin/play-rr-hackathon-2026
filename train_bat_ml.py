import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import KFold

valid = pd.read_parquet('valid_v7_ml.parquet')
valid['stakes'] = valid['match_importance'].fillna(1.0).clip(lower=1.0)
valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1

# Batting features
features = [
    'innings', 'over_num', 'over_ball_num', 'balls_remaining', 'wickets_remaining',
    'current_rr', 'leverage_index', 'wp_before', 'match_importance', 'is_knockout'
]
X = valid[features].copy()
X['balls_remaining'] = X['balls_remaining'].fillna(60)
X['wickets_remaining'] = X['wickets_remaining'].fillna(7)
X['current_rr'] = X['current_rr'].fillna(7.5).clip(0, 20)
X['leverage_index'] = X['leverage_index'].fillna(1.0).clip(0, 5)
X['wp_before'] = X['wp_before'].fillna(0.50).clip(0, 1)
X['match_importance'] = X['match_importance'].fillna(1.0).clip(1, 2)
X['is_knockout'] = X['is_knockout'].fillna(0).astype(int)

y_bat = valid['runs'].fillna(0).values

kf = KFold(n_splits=5, shuffle=True, random_state=42)
valid['ml_expected_bat_runs'] = 0.0

params = {
    'objective': 'reg:squarederror',
    'eval_metric': 'rmse',
    'max_depth': 5,
    'learning_rate': 0.08,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'tree_method': 'hist',
    'seed': 42
}

for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
    X_train, y_train = X.iloc[train_idx], y_bat[train_idx]
    X_val, y_val = X.iloc[val_idx], y_bat[val_idx]
    
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)
    
    bst = xgb.train(params, dtrain, num_boost_round=120, evals=[(dval, 'val')], verbose_eval=False)
    valid.loc[val_idx, 'ml_expected_bat_runs'] = bst.predict(dval)

valid['ml_runs_added_bat'] = (valid['runs'] - valid['ml_expected_bat_runs']) * valid['valid_flag'] * valid['stakes']
valid['is_alive_hp'] = (valid['match_alive'] == True) & (
    (valid['is_high_pressure'] == 1) | (valid['over_num'] >= 17) | (valid['leverage_index'] >= 1.20)
)
valid['ml_hp_runs_added_bat'] = valid['ml_runs_added_bat'] * (valid['is_alive_hp'] == 1)

bat_ml = valid.groupby(['striker_id', 'striker_name'], as_index=False).agg({
    'match_id': 'nunique',
    'valid_flag': 'sum',
    'runs': 'sum',
    'ml_hp_runs_added_bat': 'sum'
}).rename(columns={'match_id': 'matches', 'valid_flag': 'balls'})

bat_ml = bat_ml[bat_ml['matches'] >= 45].sort_values('ml_hp_runs_added_bat', ascending=False)
print("Top 15 Batters by ML High-Pressure Runs Added:")
print(bat_ml.head(15).to_string())

valid.to_parquet('valid_v7_ml.parquet', index=False)
print("Updated valid_v7_ml.parquet with batting ML")
