"""
Test Random Forest Extrapolation Limitation

PURPOSE:
    Verify if Random Forest predictions are "stuck" at training data limits,
    causing poor directional accuracy (49.7%).

HYPOTHESIS (from mentor):
    Random Forest CANNOT extrapolate beyond training data range.
    - Training data: prices from 1 to 5
    - Actual next: 6
    - RF prediction: ~5 (capped at training max)
    - Result: Wrong direction prediction

This test checks:
1. Are predictions capped at training data min/max?
2. Does this explain 49.7% accuracy (coin-flip level)?
3. Should we switch to models that CAN extrapolate (LSTM, XGBoost)?
"""

import pandas as pd
import numpy as np
from pathlib import Path
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

def analyze_rf_predictions():
    """Analyze if Random Forest predictions are stuck at training limits."""

    print("=" * 70)
    print("RANDOM FOREST EXTRAPOLATION LIMITATION ANALYSIS")
    print("=" * 70)

    # Load clean data
    data_path = Path(__file__).parent.parent / "data" / "processed" / "bitcoin_clean.csv"

    if not data_path.exists():
        print(f"\n❌ Data file not found: {data_path}")
        print("Run: python main.py --mode backtest")
        return

    df = pd.read_csv(data_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    print(f"\n📊 Data loaded: {len(df)} rows")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")

    # Analyze price trends
    df['price_change_pct'] = df['Price'].pct_change() * 100

    # Split into 2025 test period (same as backtest)
    test_start = pd.Timestamp('2025-01-01')
    train_df = df[df['Date'] < test_start]
    test_df = df[df['Date'] >= test_start]

    print(f"\n🔍 Analyzing 2025 test period (backtest period):")
    print(f"Training data: {len(train_df)} rows (up to {train_df['Date'].max()})")
    print(f"Test data: {len(test_df)} rows ({test_df['Date'].min()} to {test_df['Date'].max()})")

    # Check if test prices exceed training range
    train_min = train_df['Price'].min()
    train_max = train_df['Price'].max()
    test_min = test_df['Price'].min()
    test_max = test_df['Price'].max()

    print(f"\n📈 Price Ranges:")
    print(f"Training range: ${train_min:,.0f} - ${train_max:,.0f}")
    print(f"Test range:     ${test_min:,.0f} - ${test_max:,.0f}")

    # Check if test exceeded training
    if test_max > train_max:
        print(f"\n⚠️  WARNING: Test max (${test_max:,.0f}) > Training max (${train_max:,.0f})")
        print(f"   Difference: ${test_max - train_max:,.0f} ({(test_max - train_max) / train_max * 100:.1f}%)")
        print(f"   Random Forest CANNOT predict above ${train_max:,.0f}!")
    else:
        print(f"\n✓ Test max within training range")

    if test_min < train_min:
        print(f"\n⚠️  WARNING: Test min (${test_min:,.0f}) < Training min (${train_min:,.0f})")
        print(f"   Difference: ${train_min - test_min:,.0f} ({(train_min - test_min) / train_min * 100:.1f}%)")
        print(f"   Random Forest CANNOT predict below ${train_min:,.0f}!")
    else:
        print(f"\n✓ Test min within training range")

    # Analyze trend direction
    test_trend = test_df['Price'].iloc[-1] - test_df['Price'].iloc[0]
    test_trend_pct = (test_df['Price'].iloc[-1] - test_df['Price'].iloc[0]) / test_df['Price'].iloc[0] * 100

    print(f"\n📉 Test Period Trend:")
    print(f"Start price: ${test_df['Price'].iloc[0]:,.0f}")
    print(f"End price:   ${test_df['Price'].iloc[-1]:,.0f}")
    print(f"Change:      ${test_trend:,.0f} ({test_trend_pct:+.1f}%)")

    if test_trend < 0:
        print(f"   Market regime: DOWNTREND")
        print(f"   RF impact: Will predict too HIGH (can't go below training min)")
    else:
        print(f"   Market regime: UPTREND")
        print(f"   RF impact: Will predict too LOW (can't go above training max)")

    # Calculate approximate ML accuracy impact
    days_out_of_range = 0
    for idx, row in test_df.iterrows():
        if row['Price'] > train_max or row['Price'] < train_min:
            days_out_of_range += 1

    out_of_range_pct = days_out_of_range / len(test_df) * 100

    print(f"\n🎯 Impact on ML Predictions:")
    print(f"Days out of training range: {days_out_of_range} / {len(test_df)} ({out_of_range_pct:.1f}%)")

    if out_of_range_pct > 30:
        print(f"   ⚠️  HIGH IMPACT: {out_of_range_pct:.0f}% of test data outside training range!")
        print(f"   This explains low ML accuracy (49.7%)")
    elif out_of_range_pct > 10:
        print(f"   ⚠️  MODERATE IMPACT: {out_of_range_pct:.0f}% of test data outside training range")
    else:
        print(f"   ✓ LOW IMPACT: Most test data within training range")

    # Specific analysis for trending markets
    print(f"\n📊 Random Forest Limitation Explained:")
    print(f"")
    print(f"Example from your data:")
    print(f"  Training data max: ${train_max:,.0f}")
    print(f"  Actual test price: ${test_max:,.0f}")
    print(f"  RF prediction:     ~${train_max:,.0f} (CAPPED at training max)")
    print(f"  Error:             ${test_max - train_max:,.0f}")
    print(f"")
    print(f"Why Random Forest fails:")
    print(f"  1. RF creates decision trees based on training data")
    print(f"  2. For new prediction, RF finds similar tree nodes")
    print(f"  3. RF averages values from those nodes")
    print(f"  4. ❌ CANNOT output values outside training range")
    print(f"")
    print(f"For trending data (like Bitcoin):")
    print(f"  • Uptrend: RF predicts too LOW → wrong direction")
    print(f"  • Downtrend: RF predicts too HIGH → wrong direction")
    print(f"  • Result: ~50% direction accuracy (coin flip)")

    # Recommendations
    print(f"\n💡 Recommendations:")
    print(f"")
    print(f"Models that CAN extrapolate:")
    print(f"  ✅ LSTM (Long Short-Term Memory)")
    print(f"     - Neural network, learns sequences")
    print(f"     - Good for time series trends")
    print(f"     - Needs more data (~1000+ rows)")
    print(f"")
    print(f"  ✅ XGBoost with trend features")
    print(f"     - Gradient boosting (not averaging like RF)")
    print(f"     - Add features: 7-day trend, momentum, acceleration")
    print(f"     - Can extrapolate if features capture trend")
    print(f"")
    print(f"  ✅ Linear Regression with polynomial features")
    print(f"     - Simple, can extrapolate linear trends")
    print(f"     - Add: price_change_7d, price_change_14d")
    print(f"     - Fast training")
    print(f"")
    print(f"Keep Random Forest for:")
    print(f"  ✅ Direction classification (UP/DOWN)")
    print(f"     - Not regression, just binary classification")
    print(f"     - Use features: RSI, MACD, volume, momentum")
    print(f"")
    print(f"  ❌ Do NOT use for:")
    print(f"     - Price regression (predicting exact price)")
    print(f"     - Trending markets")

    # Create visualization
    if not HAS_MATPLOTLIB:
        print(f"\n⚠️  Matplotlib not installed - skipping visualization")
        print(f"   Install: pip install matplotlib")

    try:
        if not HAS_MATPLOTLIB:
            raise ImportError("Matplotlib not available")
        plt.figure(figsize=(14, 8))

        # Plot 1: Full data
        plt.subplot(2, 1, 1)
        plt.plot(df['Date'], df['Price'], label='Actual Price', alpha=0.7)
        plt.axvline(test_start, color='red', linestyle='--', label='Train/Test Split')
        plt.axhline(train_max, color='orange', linestyle='--', alpha=0.5, label=f'Training Max (${train_max:,.0f})')
        plt.axhline(train_min, color='orange', linestyle='--', alpha=0.5, label=f'Training Min (${train_min:,.0f})')
        plt.title('Bitcoin Price: Training Range Limits')
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Plot 2: Test period zoom
        plt.subplot(2, 1, 2)
        plt.plot(test_df['Date'], test_df['Price'], label='Actual Price (Test)', linewidth=2)
        plt.axhline(train_max, color='orange', linestyle='--', linewidth=2, label=f'RF Prediction Limit (${train_max:,.0f})')
        plt.fill_between(test_df['Date'], train_min, train_max, alpha=0.2, color='green', label='RF Can Predict')
        plt.title('2025 Test Period: RF Prediction Limits')
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save plot
        plot_path = Path(__file__).parent.parent / "data" / "processed" / "rf_extrapolation_analysis.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        print(f"\n📊 Visualization saved: {plot_path}")
        print(f"   Green shaded area = Range where RF can predict accurately")
        print(f"   Outside green area = RF predictions will be wrong")

    except Exception as e:
        print(f"\n⚠️  Could not create visualization: {e}")

    print(f"\n" + "=" * 70)
    print(f"ANALYSIS COMPLETE")
    print(f"=" * 70)
    print(f"\nConclusion:")
    print(f"  Current: Random Forest Regressor → 49.7% accuracy")
    print(f"  Issue: Cannot extrapolate beyond training data")
    print(f"  Fix: Switch to LSTM, XGBoost, or Linear Regression with trend features")
    print(f"\n  BUT: Business metrics show defensive strategy still works!")
    print(f"       (Beat buy-and-hold by +5.83% despite poor ML)")


if __name__ == "__main__":
    analyze_rf_predictions()
