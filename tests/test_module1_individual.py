#!/usr/bin/env python3
"""
Individual Test Script for Module 1: Technical Indicators
Tests RSI, ATR, MACD calculations with new Binance 15m dataset
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_pipeline.data_loader import BitcoinDataLoader
from src.modules.module1_technical import calculate_indicators
import pandas as pd


def test_module1():
    """Test Module 1: Technical Indicators with new dataset."""
    print("="*70)
    print("MODULE 1 INDIVIDUAL TEST: Technical Indicators")
    print("="*70)
    print("\nDataset: btc_15m_data_2018_to_2025.csv (Binance 15-minute data)")
    print()

    # Step 1: Load clean data
    print("[1/4] Loading cleaned data...")
    loader = BitcoinDataLoader(dataset_type='binance_15m')

    try:
        df = loader.load_clean_data()
        print(f"✓ Loaded {len(df):,} rows")
        print(f"  Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
        print(f"  Columns: {list(df.columns)}")
    except FileNotFoundError:
        print("  Cleaned data not found. Loading and cleaning raw data...")
        df = loader.clean_and_save()
        print(f"✓ Loaded and cleaned {len(df):,} rows")

    # Step 2: Verify data structure
    print("\n[2/4] Verifying data structure...")
    required_cols = ['Date', 'Price', 'High', 'Low', 'Volume']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        print(f"✗ ERROR: Missing columns: {missing_cols}")
        return False
    else:
        print(f"✓ All required columns present")

    # Print data sample
    print(f"\n  Sample data (first 3 rows):")
    print(df[['Date', 'Price', 'High', 'Low', 'Volume']].head(3).to_string(index=False))

    # Step 3: Calculate indicators
    print("\n[3/4] Calculating technical indicators...")
    test_date = '2024-11-01'  # Test with recent date

    try:
        df_with_indicators = calculate_indicators(df, test_date)
        print(f"✓ Indicators calculated up to {test_date}")
        print(f"  Rows with indicators: {len(df_with_indicators):,}")

        # Check which indicators were added
        new_cols = [col for col in df_with_indicators.columns if col not in df.columns]
        print(f"  New indicator columns: {new_cols}")

    except Exception as e:
        print(f"✗ ERROR calculating indicators: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: Validate indicators
    print("\n[4/4] Validating indicators...")

    validation_results = {
        'RSI': False,
        'ATR': False,
        'MACD': False,
        'SMA': False
    }

    # Check RSI (should be 0-100)
    if 'RSI' in df_with_indicators.columns:
        rsi_min = df_with_indicators['RSI'].min()
        rsi_max = df_with_indicators['RSI'].max()
        rsi_valid = (0 <= rsi_min <= 100) and (0 <= rsi_max <= 100)

        if rsi_valid:
            print(f"✓ RSI: Valid range [{rsi_min:.2f}, {rsi_max:.2f}]")
            validation_results['RSI'] = True
        else:
            print(f"✗ RSI: Invalid range [{rsi_min:.2f}, {rsi_max:.2f}]")
    else:
        print("✗ RSI: Column not found")

    # Check ATR (should be positive)
    if 'ATR' in df_with_indicators.columns:
        atr_min = df_with_indicators['ATR'].min()
        atr_max = df_with_indicators['ATR'].max()
        atr_mean = df_with_indicators['ATR'].mean()
        atr_valid = atr_min >= 0

        if atr_valid:
            print(f"✓ ATR: Valid (min={atr_min:.2f}, max={atr_max:.2f}, avg={atr_mean:.2f})")
            validation_results['ATR'] = True
        else:
            print(f"✗ ATR: Negative values found (min={atr_min:.2f})")
    else:
        print("✗ ATR: Column not found")

    # Check MACD
    macd_cols = ['MACD', 'MACD_signal', 'MACD_diff']
    if all(col in df_with_indicators.columns for col in macd_cols):
        macd_mean = df_with_indicators['MACD'].mean()
        macd_signal_mean = df_with_indicators['MACD_signal'].mean()
        macd_diff_mean = df_with_indicators['MACD_diff'].mean()

        print(f"✓ MACD: Calculated (avg MACD={macd_mean:.2f}, signal={macd_signal_mean:.2f}, diff={macd_diff_mean:.2f})")
        validation_results['MACD'] = True
    else:
        missing_macd = [col for col in macd_cols if col not in df_with_indicators.columns]
        print(f"✗ MACD: Missing columns {missing_macd}")

    # Check SMA
    sma_cols = [col for col in df_with_indicators.columns if 'SMA' in col]
    if sma_cols:
        print(f"✓ SMA: Found {sma_cols}")
        validation_results['SMA'] = True
    else:
        print(f"  SMA: No SMA columns found (optional)")

    # Display sample indicators
    print("\n  Sample indicators (last 5 rows):")
    indicator_cols = ['Date', 'Price', 'RSI', 'ATR', 'MACD', 'MACD_signal', 'MACD_diff']
    available_indicator_cols = [col for col in indicator_cols if col in df_with_indicators.columns]
    print(df_with_indicators[available_indicator_cols].tail(5).to_string(index=False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(validation_results.values())
    total = len(validation_results)

    print(f"Validation Results: {passed}/{total} passed")
    for indicator, result in validation_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {indicator}: {status}")

    # Overall result
    critical_indicators = ['RSI', 'ATR', 'MACD']
    all_critical_passed = all(validation_results.get(ind, False) for ind in critical_indicators)

    if all_critical_passed:
        print("\n✓ MODULE 1 TEST: PASSED")
        print("  All critical indicators are working correctly with new dataset")
        return True
    else:
        print("\n✗ MODULE 1 TEST: FAILED")
        print("  Some critical indicators failed validation")
        return False


if __name__ == "__main__":
    success = test_module1()
    sys.exit(0 if success else 1)
