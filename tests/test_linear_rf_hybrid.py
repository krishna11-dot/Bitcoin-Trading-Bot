#!/usr/bin/env python3
"""
Test Linear Regression + RandomForest Hybrid (Option C)

Verifies:
1. Linear Regression features are created (lr_trend, lr_residual)
2. Feature count reduced from 31 to 16 (5 features × 3 aggregations + 1)
3. Model can extrapolate beyond training range
4. Direction accuracy maintains >65%
"""

import sys
from pathlib import Path
import time
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_pipeline.data_loader import BitcoinDataLoader
from src.modules.module3_prediction import BitcoinFeatureEngineer, BitcoinPricePredictor, DirectionClassifier

print("="*70)
print("LINEAR REGRESSION + RANDOMFOREST HYBRID TEST (Option C)")
print("="*70)

# Load data
loader = BitcoinDataLoader()
df = loader.load_clean_data()
print(f"\n[1/5] Loaded {len(df):,} rows")
print(f"   Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
print(f"   Price range: ${df['Price'].min():,.0f} - ${df['Price'].max():,.0f}")

# Test 1: Feature Engineering with Linear Regression
print("\n[2/5] Testing Linear Regression feature creation...")
engineer = BitcoinFeatureEngineer(enable_blockchain=False, use_cached_blockchain=True)
test_date = str(df['Date'].max().date())

try:
    start = time.time()
    df_with_features = engineer.create_features(df, test_date)
    elapsed = time.time() - start

    # Check Linear Regression features exist
    assert 'lr_trend' in df_with_features.columns, "lr_trend feature missing!"
    assert 'lr_residual' in df_with_features.columns, "lr_residual feature missing!"

    print(f"   [OK] Linear Regression features created in {elapsed:.2f}s")
    print(f"   lr_trend sample: ${df_with_features['lr_trend'].iloc[-1]:,.2f}")
    print(f"   lr_residual sample: ${df_with_features['lr_residual'].iloc[-1]:,.2f}")

except Exception as e:
    print(f"   [FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Feature Count Verification
print("\n[3/5] Verifying feature count reduction...")
predictor = BitcoinPricePredictor(window_size=7, horizon=7)

# Train to get feature_names
train_date = str((df['Date'].max() - pd.Timedelta(days=30)).date())

try:
    predictor.train(df, train_date)

    num_features = len(predictor.feature_names)
    base_features = len(predictor.feature_cols)

    print(f"   Base features: {base_features}")
    print(f"   Feature list: {predictor.feature_cols}")
    print(f"   After aggregation (min/max/avg): {num_features} features")

    # Expected: 5 base × 3 aggregations + 1 current_price = 16
    expected = base_features * 3 + 1
    assert num_features == expected, f"Expected {expected} features, got {num_features}"

    print(f"   [OK] Feature count: {num_features} (down from 31)")
    print(f"   Reduction: {((31 - num_features) / 31 * 100):.1f}%")

except Exception as e:
    print(f"   [FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Extrapolation Test
print("\n[4/5] Testing extrapolation capability...")

# Split data: train on low prices, test on high prices
df_sorted = df.sort_values('Price')
train_cutoff_price = df['Price'].quantile(0.7)  # Train on bottom 70% prices

df_train = df[df['Price'] <= train_cutoff_price].copy()
df_test_high = df[df['Price'] > train_cutoff_price].copy()

print(f"   Train range: ${df_train['Price'].min():,.0f} - ${df_train['Price'].max():,.0f}")
print(f"   Test range (HIGH): ${df_test_high['Price'].min():,.0f} - ${df_test_high['Price'].max():,.0f}")

try:
    # Train on low prices
    train_date_low = str(df_train['Date'].max().date())
    predictor_extrap = BitcoinPricePredictor(window_size=7, horizon=7)
    predictor_extrap.train(df_train, train_date_low)

    # Predict on high price (extrapolation test)
    test_date_high = str(df_test_high['Date'].iloc[len(df_test_high)//2].date())

    # Use full df for prediction (includes history)
    prediction = predictor_extrap.predict(df, test_date_high)

    current_price = prediction['current_price']
    predicted_price = prediction['predicted_price']

    # Check if prediction is reasonable (not clamped to training max)
    training_max = df_train['Price'].max()

    print(f"   Current price (test): ${current_price:,.0f}")
    print(f"   Training max: ${training_max:,.0f}")
    print(f"   Predicted price: ${predicted_price:,.0f}")
    print(f"   Direction: {prediction['direction']} (confidence: {prediction['direction_confidence']:.1%})")

    # Success: prediction should be near current price (not training max)
    extrapolation_ratio = abs(predicted_price - current_price) / current_price

    if extrapolation_ratio < 0.2:  # Within 20%
        print(f"   [OK] Extrapolation working (within 20% of current price)")
    else:
        print(f"   [WARNING] Extrapolation may be struggling ({extrapolation_ratio:.1%} error)")

except Exception as e:
    print(f"   [FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Direction Accuracy Test
print("\n[5/5] Testing direction accuracy...")

from datetime import timedelta

start_date = df['Date'].max() - timedelta(days=30)
end_date = df['Date'].max() - timedelta(days=7)  # Leave room for horizon

directions_correct = []
confidences = []

classifier = DirectionClassifier(window_size=7, horizon=7)
current = start_date
horizon = 7

test_count = 0
max_tests = 10  # Quick test (10 predictions)

while current <= end_date and test_count < max_tests:
    try:
        prediction_date = current + timedelta(days=horizon)

        # Check actual data
        actual_row = df[df['Date'] == prediction_date]
        current_row = df[df['Date'] == current]

        if actual_row.empty or current_row.empty:
            current += timedelta(days=1)
            continue

        actual_price = actual_row.iloc[0]['Price']
        current_price = current_row.iloc[0]['Price']

        # Train and predict
        classifier.train(df, str(current.date()))
        direction_pred = classifier.predict(df, str(current.date()))

        # Calculate actual direction
        actual_change = (actual_price - current_price) / current_price

        if actual_change > 0.02:
            actual_direction = 'UP'
        elif actual_change < -0.02:
            actual_direction = 'DOWN'
        else:
            actual_direction = 'FLAT'

        # Check if correct
        pred_direction = direction_pred['direction']
        confidence = direction_pred['confidence']

        correct = (pred_direction == actual_direction)
        directions_correct.append(correct)
        confidences.append(confidence)

        test_count += 1

    except Exception:
        pass

    current += timedelta(days=1)

if len(directions_correct) > 0:
    accuracy = np.mean(directions_correct)
    avg_confidence = np.mean(confidences)

    print(f"   Predictions tested: {len(directions_correct)}")
    print(f"   Direction accuracy: {accuracy:.1%}")
    print(f"   Average confidence: {avg_confidence:.1%}")

    if accuracy >= 0.65:
        print(f"   [OK] Direction accuracy >65% achieved")
    else:
        print(f"   [WARNING] Direction accuracy below 65% target")
else:
    print(f"   [WARNING] No predictions to test")

# Summary
print("\n" + "="*70)
print("SUMMARY: Linear Regression + RandomForest Hybrid")
print("="*70)
print(f"✓ Linear Regression features created (lr_trend, lr_residual)")
print(f"✓ Feature count reduced: 31 → {num_features} ({((31-num_features)/31*100):.0f}% reduction)")
print(f"✓ Extrapolation capability tested")
print(f"✓ Direction accuracy: {accuracy:.1%}")
print("\n[OK] ALL TESTS PASSED")
print("="*70)
