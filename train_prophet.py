import pandas as pd
from prophet import Prophet
import pickle
from pathlib import Path

# 1) Load & prepare
df = pd.read_csv('data/synthetic_fabrics_4years.csv', parse_dates=['Week'])
df.rename(columns={
    'Week': 'ds',
    'Sales Volume': 'y',
    'Fabric Type': 'fabric_type'
}, inplace=True)

# 1a) Normalize
df.fabric_type = df.fabric_type.str.strip().str.lower()

# 2) Ensure models directory exists
models_dir = Path('models')
models_dir.mkdir(exist_ok=True)

# 3) Loop through each fabric
for fabric in df.fabric_type.unique():
    sub = (
        df[df.fabric_type == fabric]
          [['ds','y']]
          .sort_values('ds')
          .dropna()
    )
    # Need at least 2 points to train
    if len(sub) < 2:
        print(f"Skipping {fabric!r}: only {len(sub)} rows")
        continue

    # 4) Split: leave last 24 periods (months) for testing/validation
    train = sub.iloc[:-24]

    # 5) Fit Prophet
    m = Prophet(yearly_seasonality=True, weekly_seasonality=True)
    m.fit(train)

    # 6) Pickle the trained model
    out_path = models_dir / f"{fabric}.pkl"
    with open(out_path, 'wb') as f:
        pickle.dump(m, f)

    print(f"Trained & saved model for '{fabric}' ({len(train)} points) → {out_path}")

