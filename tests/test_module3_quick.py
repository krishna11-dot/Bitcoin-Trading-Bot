#!/usr/bin/env python3
"""
Quick Module 3 Test - Tests on recent data only (last 30 days)
"""

import sys
from pathlib import Path
import time
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from src.data_pipeline.data_loader import BitcoinDataLoader
from src.modules.module3_prediction import BitcoinFeatureEngineer, BitcoinPricePredictor

print("="*70)
print("MODULE 3 QUICK TEST - Recent Data Only")
print("="*70)

# Load data
loader = BitcoinDataLoader(dataset_type='binance_15m')
df = loader.load_clean_data()
print(f"\n[1/3] Loaded {len(df):,} rows total")

# Use only last 10,000 rows (recent data) for speed
df_recent = df.tail(10000).copy()
df_recent = df_recent.reset_index(drop=True)
print(f"   Using recent {len(df_recent):,} rows for testing")
print(f"   Date range: {df_recent['Date'].min().date()} to {df_recent['Date'].max().date()}")

# Test feature engineering
print("\n[2/3] Testing feature engineering...")
engineer = BitcoinFeatureEngineer(enable_blockchain=False, use_cached_blockchain=True)
test_date = str(df_recent['Date'].max().date())

try:
    start = time.time()
    df_with_features = engineer.create_features(df_recent, test_date)
    elapsed = time.time() - start

    print(f"   [OK] Features created in {elapsed:.2f}s")
    print(f"   Features: {[col for col in df_with_features.columns if col not in df_recent.columns]}")
    print(f"   Rows with features: {len(df_with_features):,}")
except Exception as e:
    print(f"   [FAIL] Error: {e}")
    sys.exit(1)

# Test model training and prediction
print("\n[3/3] Testing model training and prediction...")
predictor = BitcoinPricePredictor(window_size=7, horizon=7)

train_date = str((df_recent['Date'].max() - pd.Timedelta(days=7)).date())
pred_date = str(df_recent['Date'].max().date())

try:
    # Train
    start = time.time()
    predictor.train(df_recent, train_date)
    train_time = time.time() - start
    print(f"   [OK] Model trained in {train_time:.2f}s")

    # Predict
    prediction = predictor.predict(df_recent, pred_date)
    print(f"   [OK] Prediction generated")
    print(f"      Current: ${prediction['current_price']:,.0f}")
    print(f"      Predicted (7d): ${prediction['predicted_price']:,.0f}")
    print(f"      Change: {prediction['price_change_pct']:+.2%}")
    print(f"      Direction: {prediction['direction']} (confidence: {prediction['direction_confidence']:.1%})")

    print("\n" + "="*70)
    print("[OK] MODULE 3 QUICK TEST PASSED")
    print("="*70)

except Exception as e:
    print(f"   [FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
