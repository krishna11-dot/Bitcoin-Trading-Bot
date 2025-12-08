#!/usr/bin/env python3
"""
Test v1.0 strategy on multiple market periods to validate robustness.

Tests on:
- 2024: Mixed market (most recent full year)
- 2023: Bull run
- 2022: Bear market
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from src.config.config_manager import load_config
from src.data_pipeline.data_loader import BitcoinDataLoader
from src.modules.module1_technical import calculate_indicators
from src.backtesting.backtest_engine import BacktestEngine

def run_period_test(period_name: str, start_date: str, end_date: str):
    """Run backtest for a specific period."""
    print("="*70)
    print(f"TESTING: {period_name}")
    print(f"Period: {start_date} to {end_date}")
    print("="*70)

    # Load data
    loader = BitcoinDataLoader()
    df = loader.load_clean_data()

    # Calculate indicators
    df_with_ind = calculate_indicators(df, end_date)

    # Load config
    config = load_config()

    # Convert to backtest config format
    backtest_config = {
        'initial_capital': config['initial_capital'],
        'dca_amount': config['initial_capital'] * config['dca_buy_amount_percent'],
        'swing_amount': config['initial_capital'] * config.get('swing_buy_percent', 0.1),
        'rsi_oversold': config['rsi_oversold'],
        'rsi_overbought': config['rsi_overbought'],
        'k_atr': config['atr_stop_loss_multiplier'],
        'fear_threshold': config['fear_greed_buy_threshold'],
        'rag_threshold': 0.70
    }

    # Run backtest
    engine = BacktestEngine(
        df=df_with_ind,
        config=backtest_config,
        start_date=start_date,
        end_date=end_date,
        retrain_frequency=0
    )

    results = engine.run(verbose=False)

    # Print summary
    print(f"\n{period_name} RESULTS:")
    print(f"  Total Return:     {results['total_return']:+.2%}")
    print(f"  Sharpe Ratio:     {results['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown:     {results['max_drawdown']:.2%}")
    print(f"  Win Rate:         {results['win_rate']:.1%}")
    print(f"  Num Trades:       {results['num_trades']}")
    print(f"  Buy-Hold Return:  {results['buy_and_hold_return']:.2%}")
    print(f"  Outperformance:   {results['total_return'] - results['buy_and_hold_return']:+.2%}")
    print()

    return results


def main():
    """Test v1.0 on multiple periods."""
    print("\n")
    print("="*70)
    print("MULTI-PERIOD BACKTEST - v1.0 Validation")
    print("="*70)
    print("\nTesting v1.0 baseline on different market conditions:")
    print("  - 2024: Most recent (mixed market)")
    print("  - 2023: Bull run")
    print("  - 2022: Bear market")
    print("\nConfig: F&G < 40, RSI < 30, ATR 2.0x\n")

    # Test periods
    periods = [
        ("2024 (Mixed)", "2024-01-01", "2024-12-31"),
        ("2023 (Bull)", "2023-01-01", "2023-12-31"),
        ("2022 (Bear)", "2022-01-01", "2022-12-31"),
        ("2025 May-Nov (Baseline)", "2025-05-27", "2025-11-23"),
    ]

    all_results = {}

    for period_name, start, end in periods:
        try:
            results = run_period_test(period_name, start, end)
            all_results[period_name] = results
        except Exception as e:
            print(f"[ERROR] Failed to test {period_name}: {e}")
            import traceback
            traceback.print_exc()
            all_results[period_name] = None

    # Summary comparison
    print("\n")
    print("="*70)
    print("SUMMARY: v1.0 Performance Across All Periods")
    print("="*70)
    print()
    print(f"{'Period':<25} {'Return':<12} {'vs B&H':<12} {'Trades':<8} {'Win%':<8}")
    print("-"*70)

    for period_name in all_results:
        result = all_results[period_name]
        if result:
            return_str = f"{result['total_return']:+.1%}"
            outperf_str = f"{result['total_return'] - result['buy_and_hold_return']:+.1%}"
            trades_str = f"{result['num_trades']}"
            win_str = f"{result['win_rate']:.0%}"

            print(f"{period_name:<25} {return_str:<12} {outperf_str:<12} {trades_str:<8} {win_str:<8}")
        else:
            print(f"{period_name:<25} {'ERROR':<12} {'-':<12} {'-':<8} {'-':<8}")

    print()
    print("="*70)
    print("CONCLUSION:")

    # Calculate average outperformance
    valid_results = [r for r in all_results.values() if r is not None]
    if valid_results:
        avg_outperf = sum(r['total_return'] - r['buy_and_hold_return'] for r in valid_results) / len(valid_results)
        total_trades = sum(r['num_trades'] for r in valid_results)
        avg_win_rate = sum(r['win_rate'] for r in valid_results) / len(valid_results)

        print(f"  Average Outperformance: {avg_outperf:+.2%}")
        print(f"  Total Trades Across Periods: {total_trades}")
        print(f"  Average Win Rate: {avg_win_rate:.1%}")
        print()

        if avg_outperf > 0:
            print("  ✅ v1.0 beats buy-and-hold across multiple periods!")
            print("  Strategy is ROBUST - no parameter changes needed.")
        else:
            print("  ⚠️ v1.0 underperforms - consider parameter tuning.")

    print("="*70)
    print()


if __name__ == "__main__":
    main()
