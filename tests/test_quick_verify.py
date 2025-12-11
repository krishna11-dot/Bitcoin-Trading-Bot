#!/usr/bin/env python3
"""Quick verification that Option C changes work"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.module3_prediction import BitcoinFeatureEngineer, BitcoinPricePredictor
from src.data_pipeline.data_loader import BitcoinDataLoader
import pandas as pd

print("="*60)
print("QUICK VERIFICATION - Option C Implementation")
print("="*60)

# Test 1: Load small dataset
loader = BitcoinDataLoader()
df = loader.load_clean_data()
df_small = df.tail(100).copy()  # Use only last 100 rows for speed
print(f"\n[1/3] Loaded {len(df_small)} rows")

# Test 2: Feature engineering with Linear Regression
print("\n[2/3] Testing Linear Regression feature creation...")
engineer = BitcoinFeatureEngineer(enable_blockchain=False)
test_date = str(df_small['Date'].max().date())

try:
    df_features = engineer.create_features(df_small, test_date)

    # Verify Linear Regression features exist
    assert 'lr_trend' in df_features.columns, "❌ lr_trend missing!"
    assert 'lr_residual' in df_features.columns, "❌ lr_residual missing!"

    print(f"   ✓ Linear Regression features created")
    print(f"   ✓ lr_trend: ${df_features['lr_trend'].iloc[-1]:,.2f}")
    print(f"   ✓ lr_residual: ${df_features['lr_residual'].iloc[-1]:,.2f}")

except Exception as e:
    print(f"   ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Model training with new features
print("\n[3/3] Testing model with 5 features...")
predictor = BitcoinPricePredictor(window_size=7, horizon=7)

train_date = str((df_small['Date'].max() - pd.Timedelta(days=7)).date())

try:
    predictor.train(df_small, train_date)

    num_features = len(predictor.feature_names)
    base_features = len(predictor.feature_cols)

    print(f"   ✓ Base features: {base_features}")
    print(f"   ✓ Features: {predictor.feature_cols}")
    print(f"   ✓ After aggregation: {num_features} features")

    # Verify feature count
    expected = base_features * 3 + 1  # 5 * 3 + 1 = 16
    assert num_features == expected, f"Expected {expected}, got {num_features}"

    print(f"   ✓ Feature count correct: {num_features} (down from 31)")

    # Make a prediction
    pred_date = str(df_small['Date'].max().date())
    prediction = predictor.predict(df_small, pred_date)

    print(f"\n   ✓ Prediction successful:")
    print(f"     Current: ${prediction['current_price']:,.0f}")
    print(f"     Predicted: ${prediction['predicted_price']:,.0f}")
    print(f"     Direction: {prediction['direction']} ({prediction['direction_confidence']:.1%})")

except Exception as e:
    print(f"   ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL QUICK TESTS PASSED")
print("="*60)
print("\n Summary:")
print(" ✓ Linear Regression features created (lr_trend, lr_residual)")
print(f" ✓ Feature count reduced: 31 → {num_features}")
print(" ✓ Model training successful")
print(" ✓ Prediction working")
print("\n✅ Option C implementation verified!")
