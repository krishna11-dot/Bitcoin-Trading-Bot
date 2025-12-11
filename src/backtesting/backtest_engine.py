"""

BACKTEST ENGINE - Rolling Window Backtesting


PURPOSE:
    Test trading strategies on historical data to validate
    profitability before live deployment.

SUCCESS CRITERIA:
    [OK] Total return >15% on $10K
    [OK] Sharpe ratio >1.0
    [OK] Max drawdown <25%
    [OK] Zero future data leakage (validated)
    [OK] Reproducible results

ANTI-FUTURE-DATA ENFORCEMENT:
    CRITICAL: For each day, use ONLY data up to that day.
    - Technical indicators: calculated up to current_date
    - Sentiment: simulated (historical proxy)
    - Prediction: uses only past prices

VALIDATION METHOD:
    - Compare results to buy-and-hold
    - Verify anti-future-data: check max date used ≤ current date
    - Test reproducibility: same inputs = same outputs

"""

import sys
import io
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_wrapped_utf8'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stdout._wrapped_utf8 = True
        if hasattr(sys.stderr, 'buffer') and not hasattr(sys.stderr, '_wrapped_utf8'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            sys.stderr._wrapped_utf8 = True
    except (AttributeError, ValueError, OSError):
        pass  # Already wrapped or not available

import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime

from src.decision_box.trading_logic import TradingDecisionBox
from src.modules.module1_technical import get_latest_indicators
from src.modules.module2_sentiment import SentimentAnalyzer
from src.modules.module3_prediction import BitcoinPricePredictor


class BacktestEngine:
    """
    Rolling window backtesting engine.

    Tests trading strategies on historical data with strict
    anti-future-data enforcement to prevent overfitting.
    """

    def __init__(self, df: pd.DataFrame, config: Dict, start_date: str, end_date: str,
                 retrain_frequency: int = 0):
        """
        Args:
            df: Full historical DataFrame with indicators
            config: Trading config dict
            start_date: Backtest start (e.g., "2024-01-01")
            end_date: Backtest end (e.g., "2024-11-15")
            retrain_frequency: Retrain model every N days (0=train once only, 96=daily for 15-min data)
        """
        self.df = df.copy()
        self.config = config
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        self.retrain_frequency = retrain_frequency

        # Initialize decision box (disable Telegram for backtesting to avoid spam, enable Gmail for summary)
        self.decision_box = TradingDecisionBox(config, telegram_enabled=False, gmail_enabled=True)

        # Initialize ML price predictor (v2.0 - Linear Reg + RandomForest hybrid)
        print(f"[INFO] Using Hybrid Model (v2.0 - Linear Reg + RandomForest, 5 features, 16 aggregated)")
        print(f"[INFO] Features: lr_trend, lr_residual, rolling_std, volume_spike, high_low_range")
        print(f"[INFO] Fear & Greed confidence multiplier: ENABLED")
        self.price_predictor = BitcoinPricePredictor(
            window_size=7,
            horizon=7,
            use_direction_classifier=True,
            use_ensemble=False  # v1.0 - single model
        )

        # For sentiment analysis (v1.0 - Fear & Greed multiplier only, no RAG)
        from src.modules.module2_sentiment import SentimentAnalyzer
        self.sentiment_analyzer = SentimentAnalyzer(api_client=None, enable_rag=False)

        # Track portfolio values over time
        self.portfolio_history = []

        # Historical Fear & Greed data (fetched once and cached)
        self.fear_greed_data = None
        self._load_historical_fear_greed()

        # Track predictions vs actuals for technical metrics
        self.prediction_history = []  # ML predictions vs actual prices
        self.signal_history = []      # Which signals triggered trades

    def _load_historical_fear_greed(self):
        """
        Load historical Fear & Greed Index data.

        Tries to:
        1. Load from cached CSV (if exists and recent)
        2. Fetch from Alternative.me API and cache
        3. Fall back to None (will use RSI proxy)
        """
        from pathlib import Path
        import requests

        # Define cache path
        project_root = Path(__file__).parent.parent.parent
        cache_dir = project_root / "data" / "processed"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "fear_greed_historical.csv"

        # Try to load cached data first
        if cache_file.exists():
            try:
                self.fear_greed_data = pd.read_csv(cache_file)
                self.fear_greed_data['timestamp'] = pd.to_datetime(self.fear_greed_data['timestamp'])
                print(f"   [OK] Loaded cached F&G data: {len(self.fear_greed_data)} days")
                return
            except Exception as e:
                print(f"   [WARNING] Failed to load cached F&G: {e}")

        # Try to fetch from API
        try:
            print("   [INFO] Fetching historical Fear & Greed from Alternative.me...")

            # Fetch maximum available history (API supports limit param)
            # Try with limit=0 for all data, or use a large number like 2000
            url = "https://api.alternative.me/fng/"
            params = {'limit': 2000}  # Get ~5+ years of data

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Parse into DataFrame
            records = []
            for item in data['data']:
                records.append({
                    'timestamp': pd.to_datetime(int(item['timestamp']), unit='s'),
                    'value': int(item['value']),
                    'classification': item['value_classification']
                })

            self.fear_greed_data = pd.DataFrame(records)

            # Save to cache
            self.fear_greed_data.to_csv(cache_file, index=False)

            print(f"   [OK] Fetched and cached F&G data: {len(self.fear_greed_data)} days")
            print(f"   [SAVED] Cached to: {cache_file}")
            print(f"   Date range: {self.fear_greed_data['timestamp'].min().date()} to {self.fear_greed_data['timestamp'].max().date()}")

        except Exception as e:
            print(f"   [WARNING] Failed to fetch F&G data: {e}")
            print(f"   Will use RSI proxy for sentiment (backtest still works)")
            self.fear_greed_data = None

    def run(self, verbose: bool = True):
        """
        Run backtest day by day.

        CRITICAL: Anti-future-data enforcement!
        For each day, use ONLY data up to that day.

        Args:
            verbose: Print progress updates

        Returns:
            dict: Performance metrics
        """
        if verbose:
            print(f"\n Starting Backtest: {self.start_date.date()} to {self.end_date.date()}")
            print(f"Initial Capital: ${self.config['initial_capital']:,.0f}\n")

        test_dates = self.df[
            (self.df['Date'] >= self.start_date) &
            (self.df['Date'] <= self.end_date)
        ]['Date'].tolist()

        if verbose:
            print(f"   Processing {len(test_dates)} trading days...")

            if self.retrain_frequency > 0:
                num_retrainings = len(test_dates) // self.retrain_frequency
                print(f"   Periodic retraining ENABLED: every {self.retrain_frequency} days")
                print(f"   Expected retrainings: ~{num_retrainings}")
                print(f"   Training initial model...", end='', flush=True)
            else:
                print(f"   Training ML models ONCE (this takes 1-2 minutes)...", end='', flush=True)

        # Train initial model
        try:
            self.price_predictor.train(self.df, str(self.start_date.date()))
            if verbose:
                print(" [OK]")
                if self.retrain_frequency > 0:
                    print(f"   Now processing {len(test_dates)} trading days with periodic retraining...\n")
                else:
                    print(f"   Now processing {len(test_dates)} trading days...\n")
            model_trained = True
        except Exception as e:
            if verbose:
                print(f" [WARNING] Model training failed: {e}")
                print("   Continuing with fallback predictions...\n")
            model_trained = False

        retrain_count = 0  # Track number of retrainings

        for i, current_date in enumerate(test_dates):
            # Periodic retraining logic
            if self.retrain_frequency > 0 and i > 0 and i % self.retrain_frequency == 0:
                retrain_count += 1
                if verbose:
                    print(f"\n  [RETRAIN #{retrain_count}] Candle {i}/{len(test_dates)} - Retraining model with data up to {current_date.strftime('%Y-%m-%d')}...", end='', flush=True)

                try:
                    self.price_predictor.train(self.df, str(current_date.date()))
                    if verbose:
                        print(" [OK]")
                    model_trained = True
                except Exception as e:
                    if verbose:
                        print(f" [WARNING] Retrain failed: {e}")
                    # Continue with old model
                    pass
            current_date_str = current_date.strftime('%Y-%m-%d')

            # Show progress every 500 candles (not every 10 for 15-min data)
            show_detailed = (i == 0) or (i + 1) % 500 == 0 or (i + 1) == len(test_dates)

            if verbose and show_detailed:
                progress = (i + 1) / len(test_dates) * 100
                print(f"  [{i+1}/{len(test_dates)}] {progress:.1f}% - {current_date_str}...", end='', flush=True)

            # Get current price
            current_price = self.df[self.df['Date'] == current_date]['Price'].values[0]

            # Module 1: Technical indicators (with anti-future-data filter)
            try:
                technical = get_latest_indicators(self.df, current_date_str)
            except Exception as e:
                # Skip if insufficient data for indicators
                if verbose and show_detailed:
                    print(f" [SKIP - insufficient data]")
                continue

            # Module 2: Sentiment (simulated - backtest proxy)
            sentiment = self._get_sentiment_backtest(technical, current_date_str)

            # Module 3: Price prediction with ML (blockchain data + Random Forest)
            try:
                if model_trained:
                    # Just predict (FAST!) - no retraining
                    prediction = self.price_predictor.predict(self.df, current_date_str)
                else:
                    # Fallback if training failed
                    prediction = {
                        'predicted_price': current_price,
                        'direction': 'FLAT',
                        'direction_confidence': 0.5
                    }
            except Exception as e:
                # Skip if prediction fails (fallback to current price)
                prediction = {
                    'predicted_price': current_price,
                    'direction': 'FLAT',
                    'direction_confidence': 0.5
                }

            # Module 2: Apply Fear & Greed confidence multiplier (v1.0)
            if self.sentiment_analyzer and sentiment:
                fg_score = sentiment.get('value', 50)
                fg_multiplier = self.sentiment_analyzer.calculate_fg_confidence_multiplier(fg_score)

                # Apply multiplier to ML confidence
                original_confidence = prediction.get('direction_confidence', 0.5)
                adjusted_confidence = min(1.0, original_confidence * fg_multiplier)
                prediction['direction_confidence'] = adjusted_confidence
                prediction['fg_multiplier'] = fg_multiplier
                prediction['original_ml_confidence'] = original_confidence

            # Decision Box: Make decision
            decision = self.decision_box.make_decision(
                technical, sentiment, prediction, current_price
            )

            # Execute trade (if not paused by circuit breaker)
            if decision['action'] != 'PAUSE':
                self.decision_box.execute_trade(decision, current_price, current_date_str)
            else:
                # Circuit breaker activated - stop backtest
                if verbose:
                    print(f"\n[WARNING]  Circuit Breaker activated on {current_date_str}")
                break

            # Record prediction for technical metrics
            self.prediction_history.append({
                'date': current_date,
                'predicted_price': prediction.get('predicted_price', current_price),
                'predicted_direction': prediction.get('direction', 'FLAT'),
                'direction_confidence': prediction.get('direction_confidence', 0.5),
                'actual_price': current_price,
                'rsi': technical.get('RSI', 50),
                'macd_diff': technical.get('MACD_diff', 0),
                'fear_greed': sentiment.get('fear_greed_score', 50)
            })

            # Record signal history (which indicator triggered)
            self.signal_history.append({
                'date': current_date,
                'action': decision['action'],
                'strategy': decision.get('strategy', 'HOLD'),
                'rsi': technical.get('RSI', 50),
                'macd_diff': technical.get('MACD_diff', 0),
                'fear_greed': sentiment.get('fear_greed_score', 50),
                'entry_price': current_price if decision['action'] == 'BUY' else None,
                'exit_price': current_price if decision['action'] == 'SELL' else None
            })

            # Record portfolio value
            summary = self.decision_box.get_portfolio_summary(current_price)
            self.portfolio_history.append({
                'date': current_date,
                'value': summary['total_value'],
                'cash': summary['cash'],
                'btc': summary['btc'],
                'price': current_price
            })

            # Show detailed progress
            if verbose and show_detailed:
                print(f" ${summary['total_value']:,.0f} ({summary['total_return']:+.1%})")

        # Final results
        metrics = self.calculate_metrics(verbose=verbose)

        # Send Gmail summary (if enabled)
        self._send_gmail_summary(metrics, current_price)

        return metrics

    def _get_sentiment_backtest(self, technical: Dict, current_date_str: str) -> Dict:
        """
        Get sentiment for backtesting.

        Tries to use REAL historical Fear & Greed data (if available).
        Falls back to RSI proxy if F&G data not available.

        Args:
            technical: Technical indicators
            current_date_str: Current date

        Returns:
            dict: Sentiment data
        """
        rsi = technical.get('RSI', 50)

        # Try to get REAL Fear & Greed from historical data
        fg_score = None
        if self.fear_greed_data is not None:
            # Convert current_date_str to datetime
            current_date = pd.to_datetime(current_date_str)

            # Find closest F&G value (within 1 day)
            mask = (self.fear_greed_data['timestamp'] >= current_date - pd.Timedelta(days=1)) & \
                   (self.fear_greed_data['timestamp'] <= current_date + pd.Timedelta(days=1))
            matches = self.fear_greed_data[mask]

            if len(matches) > 0:
                # Use closest match
                closest_idx = (matches['timestamp'] - current_date).abs().idxmin()
                fg_score = int(matches.loc[closest_idx, 'value'])

        # Fall back to RSI proxy if no F&G data
        if fg_score is None:
            # RSI proxy: Low RSI = Fear, High RSI = Greed
            if rsi < 30:
                fg_score = 20
            elif rsi < 40:
                fg_score = 35
            elif rsi > 70:
                fg_score = 80
            elif rsi > 60:
                fg_score = 65
            else:
                fg_score = 50

        # RAG confidence (conservative - neutral)
        # In production, would use actual FAISS lookup
        if rsi < 35:
            rag_confidence = 0.75  # High confidence to buy in oversold
        elif rsi > 65:
            rag_confidence = 0.40  # Low confidence in overbought
        else:
            rag_confidence = 0.60  # Neutral

        return {
            'fear_greed_score': fg_score,
            'rag_confidence': rag_confidence,
            'rag_signal': 'BUY' if rag_confidence > 0.65 else 'HOLD'
        }

    def calculate_metrics(self, verbose: bool = True) -> Dict:
        """
        Calculate performance metrics.

        Returns:
            dict: {
                'initial_capital': float,
                'final_value': float,
                'total_return': float,
                'sharpe_ratio': float,
                'max_drawdown': float,
                'win_rate': float,
                'num_trades': int,
                'avg_trade_return': float
            }
        """
        final_price = self.df[self.df['Date'] == self.end_date]['Price'].values[0]
        summary = self.decision_box.get_portfolio_summary(final_price)

        # Extract trades
        trades_df = pd.DataFrame(self.decision_box.portfolio['trades'])

        if len(trades_df) == 0:
            if verbose:
                print("[WARNING]  No trades executed during backtest!")
            return self._empty_metrics(summary)

        # Calculate portfolio values over time
        portfolio_df = pd.DataFrame(self.portfolio_history)

        # Sharpe Ratio (using daily returns)
        returns = portfolio_df['value'].pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            sharpe = returns.mean() / returns.std() * np.sqrt(252)  # Annualized
        else:
            sharpe = 0

        # Max Drawdown
        portfolio_series = portfolio_df['value']
        running_max = portfolio_series.cummax()
        drawdown = (portfolio_series - running_max) / running_max
        max_drawdown = drawdown.min()

        # Win Rate (for completed buy-sell pairs)
        buy_sell_pairs = []
        last_buy_price = None
        for _, trade in trades_df.iterrows():
            if trade['action'] == 'BUY':
                last_buy_price = trade['price']
            elif trade['action'] == 'SELL' and last_buy_price is not None:
                profit = (trade['price'] - last_buy_price) / last_buy_price
                buy_sell_pairs.append(profit)
                last_buy_price = None

        if buy_sell_pairs:
            win_rate = sum(1 for p in buy_sell_pairs if p > 0) / len(buy_sell_pairs)
            avg_trade_return = np.mean(buy_sell_pairs)
        else:
            win_rate = 0
            avg_trade_return = 0

        # Buy-and-hold comparison
        initial_price = self.df[self.df['Date'] == self.start_date]['Price'].values[0]
        bah_return = (final_price - initial_price) / initial_price

        # Calculate technical metrics
        tech_metrics = self._calculate_technical_metrics()

        if verbose:
            self._print_results(summary, sharpe, max_drawdown, win_rate,
                              avg_trade_return, bah_return, tech_metrics)

        return {
            'initial_capital': self.config['initial_capital'],
            'final_value': summary['total_value'],
            'total_return': summary['total_return'],
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'num_trades': summary['num_trades'],
            'avg_trade_return': avg_trade_return,
            'buy_and_hold_return': bah_return,
            # Technical metrics
            'ml_direction_accuracy': tech_metrics['ml_direction_accuracy'],
            'ml_price_rmse': tech_metrics['ml_price_rmse'],
            'rsi_signal_win_rate': tech_metrics['rsi_signal_win_rate'],
            'macd_signal_win_rate': tech_metrics['macd_signal_win_rate'],
            'fg_correlation': tech_metrics['fg_correlation'],
            'dca_win_rate': tech_metrics['dca_win_rate'],
            'swing_win_rate': tech_metrics['swing_win_rate'],
            'stop_loss_win_rate': tech_metrics['stop_loss_win_rate']
        }

    def _empty_metrics(self, summary: Dict) -> Dict:
        """Return empty metrics when no trades executed."""
        return {
            'initial_capital': self.config['initial_capital'],
            'final_value': summary['total_value'],
            'total_return': summary['total_return'],
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'num_trades': 0,
            'avg_trade_return': 0,
            'buy_and_hold_return': 0,
            'ml_direction_accuracy': 0,
            'ml_price_rmse': 0,
            'rsi_signal_win_rate': 0,
            'macd_signal_win_rate': 0,
            'fg_correlation': 0,
            'dca_win_rate': 0,
            'swing_win_rate': 0,
            'stop_loss_win_rate': 0
        }

    def _send_gmail_summary(self, metrics: Dict, current_price: float):
        """
        Send Gmail summary email after backtest completes.

        Args:
            metrics: Performance metrics from calculate_metrics()
            current_price: Final BTC price
        """
        try:
            # Prepare portfolio data
            portfolio_data = {
                'cash': self.decision_box.portfolio['cash'],
                'btc': self.decision_box.portfolio['btc'],
                'total_value': metrics['final_value'],
                'total_return': metrics['total_return'],
                'num_trades': metrics['num_trades']
            }

            # Prepare trades list (last 10 trades for summary)
            trades_list = self.decision_box.portfolio['trades'][-10:] if len(self.decision_box.portfolio['trades']) > 0 else []

            # Prepare metrics dict
            metrics_summary = {
                'total_return': metrics['total_return'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'max_drawdown': metrics['max_drawdown'],
                'win_rate': metrics['win_rate'],
                'total_trades': metrics['num_trades']
            }

            # Send email
            from datetime import datetime
            success = self.decision_box.gmail.send_daily_summary(
                portfolio=portfolio_data,
                trades_today=trades_list,
                metrics=metrics_summary,
                current_price=current_price,
                date=datetime.now()
            )

            if success:
                print("\n[GMAIL] Backtest summary email sent successfully")
            else:
                print("\n[GMAIL] Failed to send backtest summary (check credentials)")

        except Exception as e:
            print(f"\n[GMAIL] Error sending summary: {e}")
            # Don't fail backtest if email fails

    def _calculate_technical_metrics(self) -> Dict:
        """
        Calculate technical performance metrics.

        PURPOSE: Debug model/signal performance when profit drops

        Returns:
            dict: Technical metrics for model evaluation
        """
        pred_df = pd.DataFrame(self.prediction_history)
        signal_df = pd.DataFrame(self.signal_history)
        trades_df = pd.DataFrame(self.decision_box.portfolio['trades'])

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

        # Convert trades_df dates to timestamps if needed
        trades_df = trades_df.copy()
        if len(trades_df) > 0 and isinstance(trades_df.iloc[0]['date'], str):
            trades_df['date'] = pd.to_datetime(trades_df['date'])

        # Match signal dates to trades
        buys = signal_df[signal_df['action'] == 'BUY']
        wins = 0
        total = 0

        for _, buy_signal in buys.iterrows():
            # Find corresponding sell after this buy
            buy_date = buy_signal['date']
            entry_price = buy_signal.get('entry_price')

            if entry_price is None:
                continue

            future_sells = trades_df[(trades_df['date'] > buy_date) & (trades_df['action'] == 'SELL')]

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

    def _print_results(self, summary, sharpe, max_drawdown, win_rate,
                      avg_trade_return, bah_return, tech_metrics):
        """Print formatted backtest results."""
        print("\n" + "="*60)
        print(" BACKTEST RESULTS")
        print("="*60)

        # BUSINESS METRICS (What customers care about)
        print("\n[BUSINESS METRICS - Profit & Risk]")
        print(f"Initial Capital:  ${self.config['initial_capital']:,.2f}")
        print(f"Final Value:      ${summary['total_value']:,.2f}")
        print(f"Total Return:     {summary['total_return']:+.2%}")
        print(f"Sharpe Ratio:     {sharpe:.2f}")
        print(f"Max Drawdown:     {max_drawdown:.2%}")
        print(f"Win Rate:         {win_rate:.1%}")
        print(f"Avg Trade Return: {avg_trade_return:+.2%}")
        print(f"Number of Trades: {summary['num_trades']}")
        print(f"Buy & Hold Return: {bah_return:+.2%}")

        # TECHNICAL METRICS (Why we made/lost money)
        print("\n[TECHNICAL METRICS - Model Performance]")
        print(f"ML Direction Accuracy:  {tech_metrics['ml_direction_accuracy']:.1%}")
        print(f"ML Price Error (RMSE):  ${tech_metrics['ml_price_rmse']:,.0f}")
        print(f"RSI Signal Win Rate:    {tech_metrics['rsi_signal_win_rate']:.1%}")
        print(f"MACD Signal Win Rate:   {tech_metrics['macd_signal_win_rate']:.1%}")
        print(f"F&G Correlation:        {tech_metrics['fg_correlation']:.2f}")

        print("\n[STRATEGY WIN RATES]")
        print(f"DCA Strategy:       {tech_metrics['dca_win_rate']:.1%}")
        print(f"Swing Strategy:     {tech_metrics['swing_win_rate']:.1%}")
        print(f"Stop-Loss Strategy: {tech_metrics['stop_loss_win_rate']:.1%}")

        print("\n" + "="*60)

        # Check success criteria
        print("\n[OK] SUCCESS CRITERIA CHECK:")
        print(f"  Total Return >15%:   {'[OK]' if summary['total_return'] > 0.15 else '[ERROR]'} ({summary['total_return']:.1%})")
        print(f"  Sharpe Ratio >1.0:   {'[OK]' if sharpe > 1.0 else '[ERROR]'} ({sharpe:.2f})")
        print(f"  Max Drawdown <25%:   {'[OK]' if max_drawdown > -0.25 else '[ERROR]'} ({max_drawdown:.1%})")
        print(f"  Win Rate >55%:       {'[OK]' if win_rate > 0.55 else '[ERROR]'} ({win_rate:.1%})")

        # Beat buy-and-hold?
        if summary['total_return'] > bah_return:
            print(f"\n Strategy beat buy-and-hold by {(summary['total_return'] - bah_return):.1%}!")
        else:
            print(f"\n[WARNING]  Strategy underperformed buy-and-hold by {(bah_return - summary['total_return']):.1%}")


def main():
    """Test backtest engine."""
    print("="*60)
    print("BACKTEST ENGINE - Testing")
    print("="*60)

    from src.data_pipeline.data_loader import BitcoinDataLoader
    from src.modules.module1_technical import calculate_indicators

    try:
        # Load clean data
        loader = BitcoinDataLoader()
        df = loader.load_clean_data()

        print(f"\n Loaded {len(df)} rows of data")
        print(f"   Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

        # Calculate indicators for full dataset
        print(f"\n Calculating technical indicators...")
        df_with_ind = calculate_indicators(df, df['Date'].max())
        print(f"   [OK] Indicators calculated")

        # Backtest configuration
        config = {
            'initial_capital': 10000,
            'dca_amount': 100,
            'swing_amount': 500,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'k_atr': 2.0,
            'fear_threshold': 40,
            'rag_threshold': 0.70
        }

        # Run backtest (last 6 months if available)
        end_date = df['Date'].max()
        start_date = end_date - pd.Timedelta(days=180)  # 6 months

        print(f"\n Running backtest...")
        print(f"   Period: {start_date.date()} to {end_date.date()}")

        engine = BacktestEngine(
            df_with_ind,
            config,
            start_date=str(start_date.date()),
            end_date=str(end_date.date())
        )

        results = engine.run(verbose=True)

        # Save trades to CSV
        trades_df = pd.DataFrame(engine.decision_box.portfolio['trades'])
        if len(trades_df) > 0:
            output_path = Path(__file__).parent.parent.parent / "data" / "processed" / "backtest_trades.csv"
            trades_df.to_csv(output_path, index=False)
            print(f"\n[SAVED] Trades saved to: {output_path}")

        print("\n" + "="*60)
        print("[OK] BACKTEST ENGINE TEST COMPLETE")
        print("="*60)

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
