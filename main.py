#!/usr/bin/env python3
"""

BTC INTELLIGENT TRADER - Main Runner


Complete pipeline to:
1. Load and clean historical data
2. Calculate technical indicators
3. Build RAG index
4. Run backtest
5. Generate performance report
6. Live paper trading on Binance Testnet

Usage:
    python main.py --mode backtest           # Historical backtest
    python main.py --mode live               # Live paper trading (Testnet)
    python main.py --mode test-apis          # Test API connections

"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_pipeline.data_loader import BitcoinDataLoader
from src.data_pipeline.api_client import APIClient
from src.modules.module1_technical import calculate_indicators, get_latest_indicators
from src.modules.module2_sentiment import SentimentAnalyzer
from src.modules.module3_prediction import BitcoinPricePredictor
from src.decision_box.trading_logic import TradingDecisionBox
from src.backtesting.backtest_engine import BacktestEngine
from src.config.config_manager import ConfigManager


def print_header():
    """Print application header."""
    print("="*70)
    print("BTC INTELLIGENT TRADER")
    print("="*70)
    print("Algorithmic Bitcoin trading system")
    print("Strategies: DCA + Swing Trading + ATR Stop-Loss")
    print("="*70)
    print()


def setup_data() -> pd.DataFrame:
    """
    Step 1: Load and clean historical data.

    Returns:
        Cleaned DataFrame
    """
    print("\n" + ""*70)
    print("STEP 1: LOADING HISTORICAL DATA")
    print(""*70)

    loader = BitcoinDataLoader()

    # Check if clean data already exists
    try:
        df = loader.load_clean_data()
        print(f"[OK] Loaded existing clean data: {len(df)} rows")
        print(f"   Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    except FileNotFoundError:
        # Clean data doesn't exist - create it
        print("[INFO] Cleaning raw data...")
        df = loader.clean_and_save()
        print(f"[OK] Data cleaned and saved: {len(df)} rows")

    return df


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Step 2: Calculate technical indicators.

    Args:
        df: Clean DataFrame

    Returns:
        DataFrame with indicators
    """
    print("\n" + ""*70)
    print("STEP 2: CALCULATING TECHNICAL INDICATORS")
    print(""*70)

    # Calculate indicators for full dataset
    max_date = df['Date'].max()
    df_with_ind = calculate_indicators(df, str(max_date.date()))

    print(f"[OK] Technical indicators calculated")
    print(f"   Indicators: RSI, ATR, MACD, SMA_50, SMA_200")

    return df_with_ind


def build_rag_index(df: pd.DataFrame, force_rebuild: bool = False):
    """
    Step 3: Build RAG index for sentiment analysis.

    Args:
        df: DataFrame with indicators
        force_rebuild: Force rebuild even if index exists
    """
    print("\n" + ""*70)
    print("STEP 3: BUILDING RAG INDEX (Historical Pattern Matching)")
    print(""*70)

    analyzer = SentimentAnalyzer(enable_rag=True)

    # Check if index already exists
    rag_index_path = Path(__file__).parent / "data" / "rag_vectordb" / "faiss_index.bin"

    if rag_index_path.exists() and not force_rebuild:
        print(f"[OK] RAG index already exists")
        analyzer.load_rag_index()
    else:
        print("[INFO] Building FAISS index...")
        analyzer.build_rag_index(df)
        print(f"[OK] RAG index built and saved")


def run_backtest(df: pd.DataFrame, config: dict, months: int = 6,
                 retrain_frequency: int = 0):
    """
    Step 4: Run backtest.

    Args:
        df: DataFrame with indicators
        config: Trading configuration
        months: Number of months to backtest
        retrain_frequency: Retrain model every N days (0=train once, 96=daily for 15-min data)
    """
    print("\n" + ""*70)
    print("STEP 4: RUNNING BACKTEST")
    print(""*70)

    # Determine date range (last N months)
    end_date = df['Date'].max()
    start_date = end_date - pd.Timedelta(days=months * 30)

    # Ensure we have enough data
    if start_date < df['Date'].min():
        start_date = df['Date'].min()
        actual_months = (end_date - start_date).days / 30
        print(f"[WARNING] Limited data available: backtesting {actual_months:.1f} months")

    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Initial Capital: ${config['initial_capital']:,.0f}")
    if retrain_frequency > 0:
        print(f"Retraining: Every {retrain_frequency} days (periodic)")
    else:
        print(f"Retraining: Once at start (faster)")
    print()

    # Run backtest
    engine = BacktestEngine(
        df,
        config,
        start_date=str(start_date.date()),
        end_date=str(end_date.date()),
        retrain_frequency=retrain_frequency
    )

    results = engine.run(verbose=True)

    # Save trades
    trades_df = pd.DataFrame(engine.decision_box.portfolio['trades'])
    if len(trades_df) > 0:
        output_path = Path(__file__).parent / "data" / "processed" / "backtest_trades.csv"
        trades_df.to_csv(output_path, index=False)
        print(f"\n[SAVED] Trades saved to: {output_path}")

    # Save backtest summary results to JSON (for chat interface)
    results_path = Path(__file__).parent / "data" / "processed" / "backtest_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"[SAVED] Results saved to: {results_path}")

    return results


def test_live_apis():
    """
    Test live API connections (for future live trading).
    """
    print("\n" + ""*70)
    print("TESTING LIVE API CONNECTIONS")
    print(""*70)

    api_client = APIClient()

    # Test Binance price
    print("\nBinance API (BTC Price):")
    try:
        price_data = api_client.get_btc_price(use_testnet=False)
        print(f"   [OK] Current BTC Price: ${price_data['price']:,.2f}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Test Fear & Greed
    print("\nFear & Greed Index:")
    try:
        fg_data = api_client.get_fear_greed_index()
        print(f"   [OK] Value: {fg_data['value']}/100 ({fg_data['classification']})")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='BTC Intelligent Trader - Algorithmic Trading System'
    )
    parser.add_argument(
        '--mode',
        choices=['backtest', 'live', 'test-apis', 'chat'],
        default='backtest',
        help='Operating mode (default: backtest)'
    )
    parser.add_argument(
        '--months',
        type=int,
        default=6,
        help='Number of months to backtest (default: 6)'
    )
    parser.add_argument(
        '--rebuild-rag',
        action='store_true',
        help='Force rebuild RAG index'
    )
    parser.add_argument(
        '--capital',
        type=float,
        default=10000,
        help='Initial capital (default: 10000)'
    )
    parser.add_argument(
        '--retrain-frequency',
        type=int,
        default=0,
        help='Retrain model every N candles (0=train once, 96=daily for 15-min data). More realistic but slower.'
    )

    args = parser.parse_args()

    # Print header
    print_header()

    # Load configuration from Google Sheets (with fallback to local cache)
    print("\n[INFO] Loading configuration...")
    config_mgr = ConfigManager()
    config = config_mgr.get_config()

    # Override with command-line arguments if provided
    if args.capital != 10000:  # If user specified custom capital
        config['initial_capital'] = args.capital

    # Add compatibility layer: Convert new config keys to old format
    # (Trading logic still uses old key names for backwards compatibility)
    config['k_atr'] = config.get('atr_stop_loss_multiplier', 2.0)
    config['fear_threshold'] = config.get('fear_greed_buy_threshold', 40)
    config['dca_amount'] = config['initial_capital'] * config.get('dca_buy_amount_percent', 0.05)
    config['swing_amount'] = config['initial_capital'] * config.get('swing_buy_percent', 0.10)

    print(f"[OK] Configuration loaded")
    print(f"     Initial Capital: ${config['initial_capital']:,.0f}")
    print(f"     DCA Enabled: {config.get('dca_enabled', True)}")
    print(f"     Swing Enabled: {config.get('swing_enabled', False)}")
    print()

    try:
        if args.mode == 'test-apis':
            # Test API connections only
            test_live_apis()

        elif args.mode == 'backtest':
            # Full backtest pipeline
            # Step 1: Load data
            df = setup_data()

            # Step 2: Calculate indicators
            df_with_ind = calculate_technical_indicators(df)

            # Step 3: Build RAG index
            build_rag_index(df_with_ind, force_rebuild=args.rebuild_rag)

            # Step 4: Run backtest
            results = run_backtest(df_with_ind, config, months=args.months,
                                  retrain_frequency=args.retrain_frequency)

            # Final summary
            print("\n" + "="*70)
            print("[COMPLETE] BACKTEST COMPLETE")
            print("="*70)
            print(f"\nFinal Return: {results['total_return']:+.2%}")
            print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
            print(f"Max Drawdown: {results['max_drawdown']:.2%}")
            print(f"Win Rate: {results['win_rate']:.1%}")

            # Compare to buy-and-hold
            if 'buy_and_hold_return' in results:
                diff = results['total_return'] - results['buy_and_hold_return']
                if diff > 0:
                    print(f"\n[SUCCESS] Beat buy-and-hold by {diff:+.2%}!")
                else:
                    print(f"\n[WARNING] Underperformed buy-and-hold by {abs(diff):.2%}")

        elif args.mode == 'live':
            # Live paper trading on Binance Testnet
            from live_trader import LiveTrader

            print("\n" + ""*70, flush=True)
            print("LIVE TRADING MODE - Binance Spot Testnet", flush=True)
            print(""*70, flush=True)
            print("[INFO] Starting live paper trading...", flush=True)
            print("[WARNING] This uses REAL API calls but VIRTUAL funds (Testnet)", flush=True)
            print(flush=True)

            # Initialize live trader
            trader = LiveTrader(
                initial_capital=config['initial_capital'],
                check_interval=300,  # 5 minutes
                use_testnet=True
            )

            # Run indefinitely (until Ctrl+C)
            trader.run(duration_hours=None)

        elif args.mode == 'chat':
            # Natural language chat interface
            from src.natural_language.interface import TradingInterface

            print("\n" + ""*70, flush=True)
            print("NATURAL LANGUAGE CHAT MODE", flush=True)
            print(""*70, flush=True)
            print("[INFO] Initializing AI trading assistant...", flush=True)
            print(flush=True)

            # Initialize and run chat interface
            try:
                interface = TradingInterface(verbose=False)
                interface.run()
            except KeyboardInterrupt:
                print("\n\n[INFO] Chat session ended")
            except Exception as chat_error:
                print(f"\n[ERROR] Chat error: {chat_error}")
                print("\nPlease ensure:")
                print("  1. GEMINI_API_KEY is set in .env file")
                print("  2. Run: pip install google-generativeai pydantic")
                sys.exit(1)

    except FileNotFoundError as e:
        print(f"\n[ERROR] Error: {e}")
        print("\nPlease ensure data files are in the correct directories")
        sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
