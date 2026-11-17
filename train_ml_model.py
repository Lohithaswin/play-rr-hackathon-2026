import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import KFold

print("Loading dataset...")
valid = pd.read_parquet('valid_v6.parquet')
valid['over_num'] = (valid['innings_ball_num'] - 1) // 6 + 1
valid['bowling_team_won'] = 1 - valid['batting_team_won']

print("Training XGBoost Model for Ball-by-Ball Expected Runs...")

# Prepare features for ML Expected Runs
features = [
    'innings', 'over_num', 'over_ball_num', 'balls_remaining', 'wickets_remaining',
    'current_rr', 'leverage_index', 'wp_before', 'match_importance', 'is_knockout'
]

# Clean up features
X = valid[features].copy()
X['balls_remaining'] = X['balls_remaining'].fillna(60)
X['wickets_remaining'] = X['wickets_remaining'].fillna(7)
X['current_rr'] = X['current_rr'].fillna(7.5).clip(0, 20)
X['leverage_index'] = X['leverage_index'].fillna(1.0).clip(0, 5)
X['wp_before'] = X['wp_before'].fillna(0.50).clip(0, 1)
X['match_importance'] = X['match_importance'].fillna(1.0).clip(1, 2)
X['is_knockout'] = X['is_knockout'].fillna(0).astype(int)

y = valid['bowler_runs'].fillna(0).values

# 5-fold cross-validation out-of-fold predictions to prevent overfitting
kf = KFold(n_splits=5, shuffle=True, random_state=42)
valid['ml_expected_runs'] = 0.0

dtrain_full = xgb.DMatrix(X, label=y)
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
    X_train, y_train = X.iloc[train_idx], y[train_idx]
    X_val, y_val = X.iloc[val_idx], y[val_idx]
    
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)
    
    bst = xgb.train(params, dtrain, num_boost_round=120, evals=[(dval, 'val')], verbose_eval=False)
    valid.loc[val_idx, 'ml_expected_runs'] = bst.predict(dval)

print("ML Expected Runs model trained. Mean ML Expected Runs per ball:", valid['ml_expected_runs'].mean())
print("Expected runs by phase:")
for ph in ['powerplay', 'middle', 'death']:
    sub = valid[valid['phase'] == ph]
    print(f"  {ph:10}: ML Expected RR = {sub['ml_expected_runs'].mean()*6.0:.2f}, Actual RR = {sub['bowler_runs'].mean()*6.0:.2f}")

valid.to_parquet('valid_v7_ml.parquet', index=False)
print("Saved valid_v7_ml.parquet")
