"""
═══════════════════════════════════════════════════════════════
MODULE 2 INDIVIDUAL TEST - Sentiment & RAG Improvements
═══════════════════════════════════════════════════════════════

Tests all Module 2 improvements:
1. RAG index with 12 features (up from 3)
2. RAG querying with k=50 (up from 10)
3. Fear & Greed confidence multiplier (new)
4. Adjusted confidence calculation (new)

Expected Results:
- RAG index builds successfully with 12 dimensions
- Querying returns 50 similar patterns
- F&G multiplier adjusts confidence based on market sentiment
- All components work together correctly
═══════════════════════════════════════════════════════════════
"""

import sys
from pathlib import Path

# Add project root to path FIRST
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import SentimentAnalyzer FIRST to avoid DLL conflicts with FAISS
from src.modules.module2_sentiment import SentimentAnalyzer

# Import other modules after RAG imports
import pandas as pd
import numpy as np
from src.modules.module1_technical import calculate_indicators
from src.data_pipeline.api_client import APIClient
from src.data_pipeline.data_loader import BitcoinDataLoader


def test_module2():
    """Test Module 2 improvements individually."""

    print("="*70)
    print("MODULE 2 TEST - Sentiment & RAG Improvements")
    print("="*70)

    test_results = []

    # ─────────────────────────────────────────────────────────
    # SETUP: Load data and initialize modules
    # ─────────────────────────────────────────────────────────
    print("\n[SETUP] Loading data and initializing modules...")

    try:
        # Load cleaned data
        loader = BitcoinDataLoader()
        df = loader.load_clean_data()
        print(f"✓ Loaded {len(df)} rows")

        # Calculate technical indicators
        current_date = str(df['Date'].max().date())
        df = calculate_indicators(df, current_date)
        print(f"✓ Calculated technical indicators")

        # Initialize API client and sentiment analyzer
        api_client = APIClient()
        analyzer = SentimentAnalyzer(api_client=api_client, enable_rag=True)
        print(f"✓ Initialized SentimentAnalyzer")
        print(f"  - enable_rag: {analyzer.enable_rag}")

    except Exception as e:
        print(f"✗ SETUP FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    # ─────────────────────────────────────────────────────────
    # TEST 1: RAG Index Building with 12 Features
    # ─────────────────────────────────────────────────────────
    print("\n" + "─"*70)
    print("TEST 1: RAG Index Building (3 → 12 features)")
    print("─"*70)

    try:
        # Build RAG index
        analyzer.build_rag_index(df)

        # Verify index properties
        if analyzer.faiss_index is None:
            raise ValueError("FAISS index is None")

        index_dim = analyzer.faiss_index.d
        index_size = analyzer.faiss_index.ntotal

        print(f"✓ RAG index built successfully")
        print(f"  - Dimension: {index_dim} (expected: 12)")
        print(f"  - Patterns stored: {index_size}")
        print(f"  - Historical data shape: {analyzer.historical_data.shape}")

        # Verify dimension is 12
        if index_dim == 12:
            print(f"✓ Correct dimension: 12 features")
            test_results.append(("RAG Index 12D", True))
        else:
            print(f"✗ Wrong dimension: {index_dim} (expected 12)")
            test_results.append(("RAG Index 12D", False))

        # Verify feature columns
        expected_features = ['RSI', 'ATR', 'MACD_diff', 'momentum_oscillator',
                           'roc_7d', 'volume_spike', 'volume_trend',
                           'price_change_pct', 'sma_ratio', 'higher_highs',
                           'lower_lows', 'Price']

        missing_features = [f for f in expected_features if f not in df.columns]
        if missing_features:
            print(f"✗ Missing features in data: {missing_features}")
            test_results.append(("Feature Availability", False))
        else:
            print(f"✓ All 12 required features present in data")
            test_results.append(("Feature Availability", True))

    except Exception as e:
        print(f"✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("RAG Index 12D", False))

    # ─────────────────────────────────────────────────────────
    # TEST 2: RAG Querying with k=50
    # ─────────────────────────────────────────────────────────
    print("\n" + "─"*70)
    print("TEST 2: RAG Querying (k=10 → k=50)")
    print("─"*70)

    try:
        # Get latest indicators for querying
        latest_row = df.iloc[-1]
        current_indicators = {
            'RSI': latest_row['RSI'],
            'ATR': latest_row['ATR'],
            'MACD_diff': latest_row['MACD_diff'],
            'momentum_oscillator': latest_row.get('momentum_oscillator', 1.0),
            'roc_7d': latest_row.get('roc_7d', 0.0),
            'volume_spike': latest_row.get('volume_spike', 1.0),
            'volume_trend': latest_row.get('volume_trend', 0.0),
            'price_change_pct': latest_row.get('price_change_pct', 0.0),
            'sma_ratio': latest_row.get('sma_ratio', 1.0),
            'higher_highs': latest_row.get('higher_highs', 0),
            'lower_lows': latest_row.get('lower_lows', 0),
            'Price': latest_row['Price']
        }

        print(f"Query indicators:")
        for key, val in list(current_indicators.items())[:5]:
            print(f"  - {key}: {val:.2f}")
        print(f"  ... (and 7 more features)")

        # Query with default k=50
        rag_result = analyzer.get_rag_confidence(current_indicators)

        similar_count = rag_result['similar_count']
        confidence = rag_result['confidence']
        signal = rag_result['signal']
        bullish_pct = rag_result['bullish_pct']

        print(f"\n✓ RAG query successful")
        print(f"  - Similar patterns retrieved: {similar_count} (expected: 50)")
        print(f"  - Confidence: {confidence:.2%}")
        print(f"  - Signal: {signal}")
        print(f"  - Bullish percentage: {bullish_pct:.2%}")

        if similar_count == 50:
            print(f"✓ Correct k value: 50 patterns retrieved")
            test_results.append(("RAG k=50", True))
        else:
            print(f"✗ Wrong k value: {similar_count} patterns (expected 50)")
            test_results.append(("RAG k=50", False))

    except Exception as e:
        print(f"✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("RAG k=50", False))

    # ─────────────────────────────────────────────────────────
    # TEST 3: Fear & Greed Confidence Multiplier
    # ─────────────────────────────────────────────────────────
    print("\n" + "─"*70)
    print("TEST 3: Fear & Greed Confidence Multiplier")
    print("─"*70)

    try:
        # Test all multiplier ranges
        test_cases = [
            (10, 1.2, "Extreme Fear"),
            (30, 1.1, "Fear"),
            (50, 1.0, "Neutral"),
            (65, 0.9, "Greed"),
            (85, 0.7, "Extreme Greed")
        ]

        all_passed = True
        for fg_score, expected_mult, label in test_cases:
            actual_mult = analyzer.calculate_fg_confidence_multiplier(fg_score)
            if actual_mult == expected_mult:
                print(f"✓ F&G={fg_score} ({label}): {actual_mult}× multiplier")
            else:
                print(f"✗ F&G={fg_score} ({label}): {actual_mult}× (expected {expected_mult}×)")
                all_passed = False

        if all_passed:
            print(f"✓ All F&G multiplier ranges correct")
            test_results.append(("F&G Multiplier", True))
        else:
            test_results.append(("F&G Multiplier", False))

    except Exception as e:
        print(f"✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("F&G Multiplier", False))

    # ─────────────────────────────────────────────────────────
    # TEST 4: Adjusted Confidence Calculation
    # ─────────────────────────────────────────────────────────
    print("\n" + "─"*70)
    print("TEST 4: Adjusted Confidence (RAG × F&G multiplier)")
    print("─"*70)

    try:
        # Get full sentiment analysis
        sentiment = analyzer.analyze_sentiment(current_indicators)

        fg_score = sentiment['fear_greed_score']
        fg_mult = sentiment['fear_greed_multiplier']
        rag_conf = sentiment['rag_confidence']
        adjusted_conf = sentiment['adjusted_confidence']
        combined_signal = sentiment['combined_signal']

        print(f"✓ Sentiment analysis complete")
        print(f"  - Fear & Greed: {fg_score}/100")
        print(f"  - F&G Multiplier: {fg_mult}×")
        print(f"  - RAG Confidence (original): {rag_conf:.2%}")
        print(f"  - Adjusted Confidence: {adjusted_conf:.2%}")
        print(f"  - Combined Signal: {combined_signal}")

        # Verify calculation
        expected_adjusted = min(1.0, rag_conf * fg_mult)
        if abs(adjusted_conf - expected_adjusted) < 0.001:
            print(f"✓ Adjusted confidence calculated correctly")
            test_results.append(("Adjusted Confidence", True))
        else:
            print(f"✗ Adjusted confidence mismatch: {adjusted_conf:.4f} vs {expected_adjusted:.4f}")
            test_results.append(("Adjusted Confidence", False))

        # Verify new fields exist
        required_fields = ['fear_greed_multiplier', 'rag_confidence', 'adjusted_confidence']
        missing_fields = [f for f in required_fields if f not in sentiment]

        if not missing_fields:
            print(f"✓ All new fields present in sentiment output")
        else:
            print(f"✗ Missing fields: {missing_fields}")

    except Exception as e:
        print(f"✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("Adjusted Confidence", False))

    # ─────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n✓ MODULE 2 TEST: PASSED")
        print("\nAll Module 2 improvements working correctly:")
        print("  - RAG index with 12 features ✓")
        print("  - RAG querying with k=50 ✓")
        print("  - F&G confidence multiplier ✓")
        print("  - Adjusted confidence calculation ✓")
    else:
        print("\n✗ MODULE 2 TEST: FAILED")
        print(f"\n{total - passed} test(s) failed. Review errors above.")

    print("="*70)


if __name__ == "__main__":
    test_module2()
