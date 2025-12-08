"""

LIVE TRADER - Real-Time Paper Trading


PURPOSE:
    Run live paper trading on Binance Spot Testnet with real-time
    market data and decision-making.

SUCCESS CRITERIA:
     Signal execution rate >95%
     Total return >15% (30-day test period)
     Sharpe ratio >1.0
     Max drawdown <25%
     System uptime >99.5%

ARCHITECTURE:
    1. Fetch live market data (price, F&G, blockchain metrics)
    2. Calculate technical indicators (RSI, ATR, MACD)
    3. Analyze sentiment (F&G + RAG)
    4. Make predictions (ML models)
    5. Get trading decision (Decision Box)
    6. Execute signal (Binance Testnet)
    7. Track performance

VALIDATION METHOD:
    - Run for 24 hours, verify all signals execute
    - Compare performance to backtest results
    - Monitor error rate and API reliability

"""

import os
import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
from dotenv import load_dotenv
import traceback

# Force unbuffered output (critical for live trading visibility)
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_pipeline.api_client import APIClient
from modules.module1_technical import calculate_indicators
from modules.module2_sentiment import SentimentAnalyzer
from modules.module3_prediction import BitcoinPricePredictor
from decision_box.trading_logic import TradingDecisionBox
from execution.binance_executor import BinanceExecutor

# Load environment variables
load_dotenv()


class LiveTrader:
    """
    Real-time trading bot for Binance Spot Testnet.

    Integrates all modules to execute live paper trading.
    """

    def __init__(
        self,
        initial_capital: float = 10000,
        check_interval: int = 300,  # 5 minutes
        use_testnet: bool = True
    ):
        """
        Initialize live trader.

        Args:
            initial_capital: Starting capital in USD
            check_interval: Seconds between trading checks (default: 300 = 5 min)
            use_testnet: Use Binance Testnet (recommended)
        """
        print("="*60, flush=True)
        print("LIVE TRADER - Initializing", flush=True)
        print("="*60, flush=True)

        # Configuration
        self.initial_capital = initial_capital
        self.check_interval = check_interval
        self.use_testnet = use_testnet

        # Load trading parameters from .env
        self.config = {
            'initial_capital': float(os.getenv('INITIAL_CAPITAL', 10000)),
            'dca_amount': float(os.getenv('DCA_AMOUNT', 100)),
            'swing_amount': float(os.getenv('SWING_AMOUNT', 500)),
            'rsi_oversold': float(os.getenv('RSI_OVERSOLD', 30)),
            'rsi_overbought': float(os.getenv('RSI_OVERBOUGHT', 70)),
            'k_atr': float(os.getenv('K_ATR', 2.0)),
            'fear_threshold': float(os.getenv('FEAR_THRESHOLD', 40)),
            'rag_confidence_threshold': float(os.getenv('RAG_CONFIDENCE_THRESHOLD', 0.70))
        }

        # Initialize components
        print("\n[INIT] Initializing components...", flush=True)
        try:
            self.api_client = APIClient()
            self.executor = BinanceExecutor(use_testnet=use_testnet)
            self.sentiment_analyzer = SentimentAnalyzer(self.api_client)
            self.predictor = BitcoinPricePredictor(
                window_size=7,
                horizon=7,
                use_direction_classifier=True
            )
            self.decision_box = TradingDecisionBox(config=self.config, telegram_enabled=True, gmail_enabled=True)
            print("[OK] All components initialized", flush=True)
        except Exception as e:
            print(f"[ERROR] Initialization failed: {e}", flush=True)
            raise

        # Performance tracking
        self.performance = {
            'start_time': datetime.now(),
            'start_value': 0.0,
            'current_value': 0.0,
            'peak_value': 0.0,
            'total_return': 0.0,
            'max_drawdown': 0.0,
            'trades': [],
            'signals_received': 0,
            'signals_executed': 0,
            'errors': 0
        }

        # Historical price data for indicators
        self.price_history = []

        # Track predictions vs actuals for technical metrics
        self.prediction_history = []  # ML predictions vs actual prices
        self.signal_history = []      # Which signals triggered trades

        # Gmail daily summary tracking
        self.last_gmail_date = None  # Track when we last sent Gmail summary

        # Pre-load recent historical data for immediate trading
        self._preload_price_history()

        # Train ML model on historical data
        self.ml_enabled = False
        self._train_ml_model()

        print(f"\n[CONFIG] Trading Parameters:", flush=True)
        print(f"   - Initial Capital: ${self.config['initial_capital']:,.2f}", flush=True)
        print(f"   - DCA Amount: ${self.config['dca_amount']:,.2f}", flush=True)
        print(f"   - RSI Oversold: {self.config['rsi_oversold']}", flush=True)
        print(f"   - Fear Threshold: {self.config['fear_threshold']}", flush=True)
        print(f"   - Check Interval: {self.check_interval}s ({self.check_interval/60:.1f} min)", flush=True)
        print(f"   - Environment: {'TESTNET' if use_testnet else 'PRODUCTION'}", flush=True)
        print(f"   - Price History: {len(self.price_history)} data points loaded", flush=True)
        print(f"   - ML Models: {'ENABLED' if self.ml_enabled else 'DISABLED'}", flush=True)

    def _preload_price_history(self):
        """
        Pre-load recent historical prices to enable immediate trading.

        Loads the last 200 days of historical data from the clean CSV
        so that indicators can be calculated immediately without waiting
        for 50+ cycles.
        """
        try:
            from data_pipeline.data_loader import BitcoinDataLoader

            print("\n[PRELOAD] Loading recent price history...", flush=True)
            loader = BitcoinDataLoader()
            df = loader.load_clean_data()

            # Get last 210 rows (buffer for data cleaning, ensures 200+ remain for SMA_200)
            recent_data = df.tail(210)

            # Convert to price_history format
            for _, row in recent_data.iterrows():
                self.price_history.append({
                    'timestamp': row['Date'],
                    'price': row['Price']
                })

            print(f"[OK] Pre-loaded {len(self.price_history)} historical prices", flush=True)
            print(f"   Date range: {recent_data['Date'].min().date()} to {recent_data['Date'].max().date()}", flush=True)
            print(f"   [READY] Can start trading immediately!", flush=True)

        except Exception as e:
            print(f"[WARNING] Failed to preload history: {e}", flush=True)
            print(f"   Will collect price history from live data (slower startup)", flush=True)

    def _train_ml_model(self):
        """
        Train ML price prediction model on historical data.

        This enables ML predictions in live mode by pre-training the model
        on all available historical data.
        """
        try:
            from data_pipeline.data_loader import BitcoinDataLoader
            from modules.module1_technical import calculate_indicators

            print("\n[ML] Training price prediction model...", flush=True)

            # Load full historical data
            loader = BitcoinDataLoader()
            df = loader.load_clean_data()

            # Calculate indicators for full dataset
            latest_date = df['Date'].max().strftime('%Y-%m-%d')
            df_with_indicators = calculate_indicators(df, latest_date)

            # Train predictor on all available data
            print(f"   Training on {len(df_with_indicators)} days of data...", flush=True)
            self.predictor.train(df_with_indicators, latest_date)

            self.ml_enabled = True
            print(f"   [OK] ML model trained and ready", flush=True)

        except Exception as e:
            print(f"   [WARNING] Failed to train ML model: {e}", flush=True)
            print(f"   ML predictions will be disabled (using current price)", flush=True)
            self.ml_enabled = False

    def _update_price_history(self, current_price: float):
        """
        Update rolling price history for indicator calculation.

        Args:
            current_price: Latest BTC price
        """
        self.price_history.append({
            'timestamp': datetime.now(),
            'price': current_price
        })

        # Keep last 220 data points (buffer for indicator calculation + SMA_200)
        # After filtering and warmup, this ensures 200+ rows remain
        if len(self.price_history) > 220:
            self.price_history = self.price_history[-220:]

    def _calculate_indicators(self) -> Optional[Dict]:
        """
        Calculate technical indicators from price history.

        Returns:
            dict with RSI, ATR, MACD, SMA or None if insufficient data
        """
        if len(self.price_history) < 50:
            print(f"[WARNING] Insufficient price history ({len(self.price_history)}/50 points)")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(self.price_history)
        df['Date'] = df['timestamp']
        df['Price'] = df['price']  # Use 'Price' column name (as expected by calculate_indicators)
        df['High'] = df['price']  # Simplified (real: track high/low)
        df['Low'] = df['price']
        df['Volume'] = 0  # Not tracked in live mode

        # Calculate indicators
        try:
            # Use the latest date in price history (keep full timestamp for live mode)
            current_date = df['Date'].max()
            df_with_indicators = calculate_indicators(df, current_date)

            # Get latest values
            latest = df_with_indicators.iloc[-1]

            return {
                'RSI': latest['RSI'],
                'ATR': latest['ATR'],
                'MACD': latest['MACD'],
                'MACD_signal': latest['MACD_signal'],
                'MACD_diff': latest['MACD_diff'],
                'SMA_50': latest['SMA_50'],
                'SMA_200': latest['SMA_200']
            }

        except Exception as e:
            print(f"[ERROR] Indicator calculation failed: {e}")
            return None

    def _get_portfolio_state(self, current_price: float) -> Dict:
        """
        Get current portfolio state from Binance account.

        Args:
            current_price: Current BTC price

        Returns:
            dict: {
                'cash': float (USDT),
                'btc': float (BTC holdings),
                'last_dca_price': float,
                'entry_price': float,
                'trades': list
            }
        """
        try:
            portfolio_data = self.executor.get_portfolio_value(current_price)

            return {
                'cash': portfolio_data['usdt_balance'],
                'btc': portfolio_data['btc_balance'],
                'last_dca_price': current_price,  # Simplified
                'entry_price': current_price,  # Simplified
                'trades': []  # Tracked separately
            }

        except Exception as e:
            print(f"[ERROR] Failed to get portfolio state: {e}")
            # Return default state
            return {
                'cash': self.initial_capital,
                'btc': 0.0,
                'last_dca_price': 0.0,
                'entry_price': 0.0,
                'trades': []
            }

    def _calculate_technical_metrics(self) -> Dict:
        """
        Calculate technical performance metrics.

        PURPOSE: Debug model/signal performance when profit drops

        Returns:
            dict: Technical metrics for model evaluation
        """
        pred_df = pd.DataFrame(self.prediction_history)
        signal_df = pd.DataFrame(self.signal_history)
        trades_df = pd.DataFrame(self.performance['trades'])

        # Default metrics (if no data)
        if len(pred_df) == 0:
            return {
                'ml_direction_accuracy': 0,
                'ml_price_rmse': 0,
                'rsi_signal_win_rate': 0,
                'macd_signal_win_rate': 0,
                'fg_correlation': 0,
                'dca_win_rate': 0,
                'swing_win_rate': 0,
                'stop_loss_win_rate': 0
            }

        # 1. ML Direction Accuracy (% times predicted UP/DOWN correctly)
        pred_df['actual_direction'] = 'FLAT'
        for i in range(1, len(pred_df)):
            if pred_df.iloc[i]['actual_price'] > pred_df.iloc[i-1]['actual_price']:
                pred_df.loc[pred_df.index[i], 'actual_direction'] = 'UP'
            elif pred_df.iloc[i]['actual_price'] < pred_df.iloc[i-1]['actual_price']:
                pred_df.loc[pred_df.index[i], 'actual_direction'] = 'DOWN'

        correct_predictions = (pred_df['predicted_direction'] == pred_df['actual_direction']).sum()
        ml_direction_accuracy = correct_predictions / len(pred_df) if len(pred_df) > 0 else 0

        # 2. ML Price RMSE (prediction error in dollars)
        price_errors = (pred_df['predicted_price'] - pred_df['actual_price']) ** 2
        ml_price_rmse = np.sqrt(price_errors.mean()) if len(price_errors) > 0 else 0

        # 3. RSI Signal Win Rate (when RSI < 30, did trades profit?)
        rsi_trades = signal_df[signal_df['rsi'] < 30]
        rsi_wins = self._calculate_signal_win_rate(rsi_trades, trades_df)

        # 4. MACD Signal Win Rate (when MACD > 0, did trades profit?)
        macd_trades = signal_df[signal_df['macd_diff'] > 0]
        macd_wins = self._calculate_signal_win_rate(macd_trades, trades_df)

        # 5. Fear & Greed Correlation with next-day returns
        fg_correlation = 0
        if len(pred_df) > 1:
            pred_df['next_return'] = pred_df['actual_price'].pct_change().shift(-1)
            fg_correlation = pred_df['fear_greed'].corr(pred_df['next_return'])
            if pd.isna(fg_correlation):
                fg_correlation = 0

        # 6. Strategy-specific win rates
        dca_win_rate = self._calculate_strategy_win_rate('DCA', signal_df, trades_df)
        swing_win_rate = self._calculate_strategy_win_rate('SWING', signal_df, trades_df)
        stop_loss_win_rate = self._calculate_strategy_win_rate('STOP_LOSS', signal_df, trades_df)

        return {
            'ml_direction_accuracy': ml_direction_accuracy,
            'ml_price_rmse': ml_price_rmse,
            'rsi_signal_win_rate': rsi_wins,
            'macd_signal_win_rate': macd_wins,
            'fg_correlation': fg_correlation,
            'dca_win_rate': dca_win_rate,
            'swing_win_rate': swing_win_rate,
            'stop_loss_win_rate': stop_loss_win_rate
        }

    def _calculate_signal_win_rate(self, signal_df, trades_df) -> float:
        """Calculate win rate for trades triggered by a specific signal."""
        if len(signal_df) == 0 or len(trades_df) == 0:
            return 0

        # Convert trades_df timestamps to datetime if needed
        trades_df = trades_df.copy()
        if len(trades_df) > 0 and isinstance(trades_df.iloc[0]['timestamp'], str):
            trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])

        # Match signal dates to trades
        buys = signal_df[signal_df['action'] == 'BUY']
        wins = 0
        total = 0

        for _, buy_signal in buys.iterrows():
            # Find corresponding sell after this buy
            buy_time = buy_signal['timestamp']
            entry_price = buy_signal.get('entry_price')

            if entry_price is None:
                continue

            future_sells = trades_df[(trades_df['timestamp'] > buy_time) & (trades_df['action'] == 'SELL')]

            if len(future_sells) > 0:
                sell = future_sells.iloc[0]
                profit = (sell['price'] - entry_price) / entry_price
                if profit > 0:
                    wins += 1
                total += 1

        return wins / total if total > 0 else 0

    def _calculate_strategy_win_rate(self, strategy_name: str, signal_df, trades_df) -> float:
        """Calculate win rate for a specific strategy."""
        strategy_trades = signal_df[signal_df['strategy'] == strategy_name]
        return self._calculate_signal_win_rate(strategy_trades, trades_df)

    def _update_performance(self, current_value: float):
        """
        Update performance metrics.

        Args:
            current_value: Current portfolio value in USD
        """
        # Initialize start value
        if self.performance['start_value'] == 0.0:
            self.performance['start_value'] = current_value
            self.performance['peak_value'] = current_value

        # Update current value
        self.performance['current_value'] = current_value

        # Update peak
        if current_value > self.performance['peak_value']:
            self.performance['peak_value'] = current_value

        # Calculate total return
        self.performance['total_return'] = (
            (current_value - self.performance['start_value']) /
            self.performance['start_value'] * 100
        )

        # Calculate max drawdown
        drawdown = (
            (self.performance['peak_value'] - current_value) /
            self.performance['peak_value'] * 100
        )
        if drawdown > self.performance['max_drawdown']:
            self.performance['max_drawdown'] = drawdown

        # Calculate execution rate
        if self.performance['signals_received'] > 0:
            execution_rate = (
                self.performance['signals_executed'] /
                self.performance['signals_received'] * 100
            )
        else:
            execution_rate = 0

        # Calculate technical metrics
        tech_metrics = self._calculate_technical_metrics()

        # Print performance update
        runtime = datetime.now() - self.performance['start_time']
        print(f"\n{'='*60}")
        print(f"PERFORMANCE UPDATE")
        print(f"{'='*60}")

        # BUSINESS METRICS (What customers care about)
        print(f"\n[BUSINESS METRICS - Profit & Risk]")
        print(f"Runtime: {runtime}")
        print(f"Portfolio Value: ${current_value:,.2f}")
        print(f"Total Return: {self.performance['total_return']:+.2f}%")
        print(f"Max Drawdown: -{self.performance['max_drawdown']:.2f}%")
        print(f"Trades Executed: {len(self.performance['trades'])}")
        print(f"Signal Execution Rate: {execution_rate:.1f}%")
        print(f"Errors: {self.performance['errors']}")

        # TECHNICAL METRICS (Why we made/lost money)
        if len(self.prediction_history) > 5:  # Only show if we have enough data
            print(f"\n[TECHNICAL METRICS - Model Performance]")
            print(f"ML Direction Accuracy:  {tech_metrics['ml_direction_accuracy']:.1%}")
            print(f"ML Price Error (RMSE):  ${tech_metrics['ml_price_rmse']:,.0f}")
            print(f"RSI Signal Win Rate:    {tech_metrics['rsi_signal_win_rate']:.1%}")
            print(f"MACD Signal Win Rate:   {tech_metrics['macd_signal_win_rate']:.1%}")
            print(f"F&G Correlation:        {tech_metrics['fg_correlation']:.2f}")

            print(f"\n[STRATEGY WIN RATES]")
            print(f"DCA Strategy:       {tech_metrics['dca_win_rate']:.1%}")
            print(f"Swing Strategy:     {tech_metrics['swing_win_rate']:.1%}")
            print(f"Stop-Loss Strategy: {tech_metrics['stop_loss_win_rate']:.1%}")

        print(f"\n{'='*60}\n")

    def trading_cycle(self):
        """
        Execute one trading cycle (fetch data, decide, execute).

        This is called every check_interval seconds.
        """
        print(f"\n{'='*60}")
        print(f"TRADING CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        try:
            # Step 1: Get current market data
            print("\n[1/6] Fetching market data...")
            current_price = self.executor.get_current_price()
            print(f"   BTC Price: ${current_price:,.2f}")

            # Get Fear & Greed Index
            try:
                fng_data = self.api_client.get_fear_greed_index()
                fg_score = fng_data['value']
                print(f"   Fear & Greed: {fg_score}/100 ({fng_data['classification']})")
            except Exception as e:
                print(f"   [WARNING] Failed to fetch F&G: {e}")
                fg_score = 50  # Default to neutral

            # Step 2: Update price history and calculate indicators
            print("\n[2/6] Calculating technical indicators...")
            self._update_price_history(current_price)
            indicators = self._calculate_indicators()

            if indicators is None:
                print("   [SKIP] Insufficient data for indicators (need 50+ data points)")
                return

            print(f"   RSI: {indicators['RSI']:.2f}")
            print(f"   ATR: ${indicators['ATR']:,.2f}")
            print(f"   MACD: {indicators['MACD']:.2f}")

            # Step 3: Get portfolio state
            print("\n[3/6] Getting portfolio state...")
            portfolio = self._get_portfolio_state(current_price)
            portfolio_value = portfolio['cash'] + (portfolio['btc'] * current_price)
            print(f"   Cash: ${portfolio['cash']:,.2f}")
            print(f"   BTC: {portfolio['btc']:.6f} (${portfolio['btc'] * current_price:,.2f})")
            print(f"   Total: ${portfolio_value:,.2f}")

            # Step 4: Make prediction (using trained ML model)
            print("\n[4/6] Making price prediction...")

            if self.ml_enabled:
                # Use trained ML model for prediction
                try:
                    # Prepare DataFrame for prediction
                    df = pd.DataFrame(self.price_history)
                    df['Date'] = df['timestamp']
                    df['Price'] = df['price']
                    df['High'] = df['price']
                    df['Low'] = df['price']
                    df['Volume'] = 0

                    # Get current date
                    current_date = df['Date'].max().strftime('%Y-%m-%d')

                    # Calculate indicators
                    from modules.module1_technical import calculate_indicators
                    df_with_indicators = calculate_indicators(df, current_date)

                    # Make prediction
                    prediction_result = self.predictor.predict(df_with_indicators, current_date)
                    predicted_price = prediction_result['predicted_price']
                    direction_confidence = prediction_result['direction_confidence']

                    print(f"   [ML] Predicted Price: ${predicted_price:,.2f}")
                    print(f"   [ML] Direction: {prediction_result.get('direction', 'NEUTRAL')}")
                    print(f"   [ML] Confidence: {direction_confidence:.2%}")

                except Exception as e:
                    print(f"   [WARNING] ML prediction failed: {e}")
                    predicted_price = current_price
                    direction_confidence = 0.5
                    prediction_result = {
                        'predicted_price': current_price,
                        'direction': 'FLAT',
                        'direction_confidence': 0.5
                    }
                    print(f"   Fallback to current price: ${predicted_price:,.2f}")
            else:
                # ML disabled - use current price
                predicted_price = current_price
                direction_confidence = 0.5
                prediction_result = {
                    'predicted_price': current_price,
                    'direction': 'FLAT',
                    'direction_confidence': 0.5
                }
                print(f"   [SKIP] ML disabled, using current price: ${predicted_price:,.2f}")

            # Step 5: Get trading decision
            print("\n[5/6] Getting trading decision...")
            self.decision_box.portfolio = portfolio  # Update decision box state

            # Prepare inputs in correct format
            technical_data = {
                'RSI': indicators['RSI'],
                'ATR': indicators['ATR'],
                'MACD_diff': indicators['MACD_diff']
            }

            sentiment_data = {
                'fear_greed_score': fg_score,
                'rag_confidence': 0.0  # RAG not used in live mode
            }

            prediction_data = {
                'predicted_price': predicted_price,
                'direction_confidence': direction_confidence
            }

            decision = self.decision_box.make_decision(
                technical=technical_data,
                sentiment=sentiment_data,
                prediction=prediction_data,
                current_price=current_price
            )

            self.performance['signals_received'] += 1

            # Record prediction for technical metrics
            self.prediction_history.append({
                'timestamp': datetime.now(),
                'predicted_price': prediction_data.get('predicted_price', current_price),
                'predicted_direction': prediction_result.get('direction', 'FLAT') if self.ml_enabled else 'FLAT',
                'direction_confidence': prediction_data.get('direction_confidence', 0.5),
                'actual_price': current_price,
                'rsi': technical_data.get('RSI', 50),
                'macd_diff': technical_data.get('MACD_diff', 0),
                'fear_greed': sentiment_data.get('fear_greed_score', 50)
            })

            # Record signal history (which indicator triggered)
            self.signal_history.append({
                'timestamp': datetime.now(),
                'action': decision['action'],
                'strategy': decision.get('strategy', 'HOLD'),
                'rsi': technical_data.get('RSI', 50),
                'macd_diff': technical_data.get('MACD_diff', 0),
                'fear_greed': sentiment_data.get('fear_greed_score', 50),
                'entry_price': current_price if decision['action'] == 'BUY' else None,
                'exit_price': current_price if decision['action'] == 'SELL' else None
            })

            print(f"   Decision: {decision['action']}")
            print(f"   Reason: {decision['reason']}")

            # Step 6: Execute signal
            print("\n[6/6] Executing signal...")
            result = self.executor.execute_signal(decision, current_price)

            if result:
                self.performance['signals_executed'] += 1
                self.performance['trades'].append({
                    'timestamp': datetime.now(),
                    'action': decision['action'],
                    'price': current_price,
                    'amount': result.get('executed_qty', 0),
                    'value': result.get('executed_value', 0),
                    'reason': decision['reason']
                })

            # Update performance metrics
            self._update_performance(portfolio_value)

            # Send daily Gmail summary (once per day)
            self._send_daily_gmail_summary(current_price, portfolio_value)

        except Exception as e:
            print(f"\n[ERROR] Trading cycle failed: {e}")
            traceback.print_exc()
            self.performance['errors'] += 1

    def run(self, duration_hours: Optional[int] = None):
        """
        Run live trading bot.

        Args:
            duration_hours: Run for N hours then stop. If None, run indefinitely.
        """
        print(f"\n{'='*60}", flush=True)
        print("LIVE TRADER - Starting", flush=True)
        print(f"{'='*60}", flush=True)

        if duration_hours:
            print(f"\n[INFO] Will run for {duration_hours} hours", flush=True)
            end_time = datetime.now() + timedelta(hours=duration_hours)
        else:
            print(f"\n[INFO] Running indefinitely (press Ctrl+C to stop)", flush=True)
            end_time = None

        print(f"[INFO] Check interval: {self.check_interval}s ({self.check_interval/60:.1f} min)", flush=True)
        print(f"[INFO] Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

        try:
            while True:
                # Run trading cycle
                self.trading_cycle()

                # Check if we should stop
                if end_time and datetime.now() >= end_time:
                    print(f"\n[INFO] Duration limit reached ({duration_hours} hours)")
                    break

                # Wait for next cycle
                print(f"\n[SLEEP] Waiting {self.check_interval}s until next cycle...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print(f"\n\n[INFO] Stopped by user (Ctrl+C)")

        finally:
            # Print final performance report
            self._print_final_report()

    def _send_daily_gmail_summary(self, current_price: float, portfolio_value: float):
        """
        Send daily Gmail summary (once per day at end of day).

        Args:
            current_price: Current BTC price
            portfolio_value: Current portfolio value
        """
        try:
            # Check if we should send summary (once per day)
            today = datetime.now().date()

            if self.last_gmail_date == today:
                # Already sent today
                return

            # Check if it's end of day (configurable send time)
            # Change GMAIL_SEND_HOUR and GMAIL_SEND_MINUTE to your preferred time
            GMAIL_SEND_HOUR = 18  # Hour (0-23): 18 = 6 PM
            GMAIL_SEND_MINUTE = 15  # Minute (0-59): 15 = :15

            current_time = datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute

            # Check if it's past the target time
            target_passed = (
                current_hour > GMAIL_SEND_HOUR or
                (current_hour == GMAIL_SEND_HOUR and current_minute >= GMAIL_SEND_MINUTE)
            )

            if not target_passed:
                # Not yet time to send
                return

            # Prepare portfolio data
            portfolio_data = {
                'cash': self.decision_box.portfolio['cash'],
                'btc': self.decision_box.portfolio['btc'],
                'total_value': portfolio_value,
                'total_return': self.performance['total_return'] / 100,  # Convert to decimal
                'num_trades': len(self.performance['trades'])
            }

            # Trades from today
            today_trades = [
                trade for trade in self.performance['trades']
                if trade['timestamp'].date() == today
            ]

            # Performance metrics
            tech_metrics = self._calculate_technical_metrics()
            metrics_summary = {
                'total_return': self.performance['total_return'] / 100,
                'sharpe_ratio': 0,  # Not calculated in live mode yet
                'max_drawdown': self.performance['max_drawdown'] / 100,
                'win_rate': tech_metrics.get('rsi_signal_win_rate', 0),
                'total_trades': len(self.performance['trades'])
            }

            # Send email
            success = self.decision_box.gmail.send_daily_summary(
                portfolio=portfolio_data,
                trades_today=today_trades,
                metrics=metrics_summary,
                current_price=current_price,
                date=datetime.now()
            )

            if success:
                print(f"\n[GMAIL] Daily summary sent successfully")
                self.last_gmail_date = today
            else:
                print(f"\n[GMAIL] Failed to send daily summary (check credentials)")

        except Exception as e:
            print(f"\n[GMAIL] Error sending daily summary: {e}")
            # Don't fail trading if email fails

    def _print_final_report(self):
        """Print final performance report."""
        print(f"\n\n{'='*60}")
        print("LIVE TRADING - FINAL REPORT")
        print(f"{'='*60}")

        runtime = datetime.now() - self.performance['start_time']

        print(f"\nRuntime: {runtime}")
        print(f"Start Value: ${self.performance['start_value']:,.2f}")
        print(f"Final Value: ${self.performance['current_value']:,.2f}")
        print(f"Total Return: {self.performance['total_return']:+.2f}%")
        print(f"Peak Value: ${self.performance['peak_value']:,.2f}")
        print(f"Max Drawdown: -{self.performance['max_drawdown']:.2f}%")

        print(f"\nTrade Statistics:")
        print(f"   Total Trades: {len(self.performance['trades'])}")
        print(f"   Signals Received: {self.performance['signals_received']}")
        print(f"   Signals Executed: {self.performance['signals_executed']}")

        if self.performance['signals_received'] > 0:
            execution_rate = (
                self.performance['signals_executed'] /
                self.performance['signals_received'] * 100
            )
            print(f"   Execution Rate: {execution_rate:.1f}%")

        print(f"\nReliability:")
        print(f"   Errors: {self.performance['errors']}")

        if self.performance['signals_received'] > 0:
            error_rate = self.performance['errors'] / self.performance['signals_received'] * 100
            print(f"   Error Rate: {error_rate:.1f}%")

        print(f"\n{'='*60}")
        print("Live trading session complete")
        print(f"{'='*60}\n")


def main():
    """Main entry point for live trader."""
    import argparse

    parser = argparse.ArgumentParser(description='BTC Intelligent Trader - Live Mode')
    parser.add_argument('--duration', type=int, default=None,
                       help='Run for N hours (default: indefinite)')
    parser.add_argument('--interval', type=int, default=300,
                       help='Check interval in seconds (default: 300 = 5 min)')
    parser.add_argument('--capital', type=float, default=10000,
                       help='Initial capital in USD (default: 10000)')
    parser.add_argument('--production', action='store_true',
                       help='Use PRODUCTION Binance API (default: Testnet) - NOT RECOMMENDED')

    args = parser.parse_args()

    # Initialize live trader
    trader = LiveTrader(
        initial_capital=args.capital,
        check_interval=args.interval,
        use_testnet=not args.production
    )

    # Run
    trader.run(duration_hours=args.duration)


if __name__ == "__main__":
    main()
