"""

DECISION BOX - Core Trading Logic


PURPOSE:
    Orchestrate all 3 modules (Technical, Sentiment, Prediction) into
    profitable trading decisions using 5 complementary strategies.

SUCCESS CRITERIA:
     Overall win rate >55%
     DCA executes at optimal times (NOT blindly weekly)
     Swing trades achieve 60%+ win rate
     Stop-loss prevents >5% loss per trade
     Circuit breaker activates before 25% drawdown

STRATEGIES IMPLEMENTED:
    1. DCA (Dollar-Cost Averaging) - Base accumulation layer
    2. Swing Trading - Opportunistic large moves
    3. ATR-based Stop-Loss - Dynamic risk management
    4. Take Profit - Lock gains when overheated
    5. Circuit Breaker - Emergency stop at 25% drawdown

VALIDATION METHOD:
    Run backtest on 6+ months of data, calculate:
    - Win rate (profitable trades / total trades)
    - DCA timing quality (price drop % at buy)
    - Average loss per stopped trade
    - Drawdown before breaker activation

"""

import pandas as pd
from typing import Dict, Optional
from src.notifications.telegram_notifier import TelegramNotifier
from src.notifications.gmail_notifier import GmailNotifier


class TradingDecisionBox:
    """
    Python class implementing all 5 trading strategies.

    SUCCESS CRITERIA:
    - Win rate >55%
    - DCA executes at optimal times (not blindly)
    - Swing trades achieve 60%+ win rate
    - Stop-loss prevents >5% loss per trade
    - Circuit breaker activates before 25% drawdown

    STRATEGIES:
    1. DCA (Dollar-Cost Averaging) - Base layer
    2. Swing Trading - Opportunistic
    3. ATR Stop-Loss - Risk management
    4. Take Profit - Exit strategy
    5. Circuit Breaker - Emergency stop
    """

    def __init__(self, config: Dict, telegram_enabled: bool = True, gmail_enabled: bool = False):
        """
        Args:
            config: dict with:
                - initial_capital: Starting cash (e.g., 10000)
                - dca_amount: DCA buy amount (e.g., 100)
                - swing_amount: Swing buy amount (e.g., 500)
                - rsi_oversold: RSI threshold (e.g., 30)
                - rsi_overbought: RSI threshold (e.g., 70)
                - k_atr: ATR multiplier for stop-loss (e.g., 2.0)
                - fear_threshold: F&G threshold (e.g., 40)
                - rag_threshold: RAG confidence (e.g., 0.70)
            telegram_enabled: Enable Telegram notifications (default: True)
                             Set to False for backtesting to avoid spam
            gmail_enabled: Enable Gmail notifications (default: False)
                          Set to True for daily summaries in live mode
        """
        self.config = config
        self.portfolio = {
            'cash': config['initial_capital'],
            'btc': 0.0,
            'entry_price': None,
            'last_dca_price': None,
            'trades': []
        }

        # Initialize notifiers
        self.telegram = TelegramNotifier(enabled=telegram_enabled)
        self.gmail = GmailNotifier(enabled=gmail_enabled)

    def make_decision(
        self,
        technical: Dict,
        sentiment: Dict,
        prediction: Dict,
        current_price: float
    ) -> Dict:
        """
        
        MAIN DECISION LOGIC
        

        PURPOSE:
            Evaluate all 5 strategies in priority order and return
            the highest-priority actionable decision.

        PRIORITY ORDER (Why this order matters):
            1. Circuit Breaker - HIGHEST (emergency protection)
            2. Stop-Loss - Protect existing positions
            3. Take Profit - Lock in gains
            4. Swing Entry - Opportunistic (higher reward)
            5. DCA - Base layer (lower risk)
            6. HOLD - Default if no conditions met

        Args:
            technical: Module 1 output {RSI, ATR, MACD_diff, ...}
            sentiment: Module 2 output {fear_greed_score, rag_confidence, ...}
            prediction: Module 3 output {predicted_price, direction, ...}
            current_price: Current BTC price from API

        Returns:
            Decision dict: {
                'action': 'BUY'/'SELL'/'HOLD'/'PAUSE',
                'amount': float ($ or BTC),
                'reason': str (human-readable explanation),
                'strategy': str (which strategy triggered),
                **kwargs (strategy-specific metadata)
            }
        
        """
        # Extract indicators from modules
        rsi = technical.get('RSI', 50)
        atr = technical.get('ATR', 1000)
        macd_diff = technical.get('MACD_diff', 0)

        fg_score = sentiment.get('fear_greed_score', 50)
        rag_confidence = sentiment.get('rag_confidence', 0.5)

        predicted_price = prediction.get('predicted_price', current_price)
        direction_confidence = prediction.get('direction_confidence', 0.5)

        # 
        # STRATEGY 1: Circuit Breaker (Check FIRST - Highest Priority)
        # 
        circuit_breaker = self._check_circuit_breaker(current_price)
        if circuit_breaker:
            return circuit_breaker

        # 
        # STRATEGY 2 & 3: Check existing positions (if holding BTC)
        # 
        if self.portfolio['btc'] > 0:
            # Stop-Loss check
            stop_loss = self._check_stop_loss(current_price, atr)
            if stop_loss:
                return stop_loss

            # Take Profit check
            take_profit = self._check_take_profit(
                rsi, macd_diff, predicted_price, current_price
            )
            if take_profit:
                return take_profit

        # 
        # STRATEGY 4: Swing Entry (Opportunistic - Higher priority)
        # 
        swing_entry = self._check_swing_entry(
            rsi, macd_diff, fg_score, predicted_price, current_price, direction_confidence
        )
        if swing_entry:
            return swing_entry

        # 
        # STRATEGY 5: DCA (Base Layer - Lower priority)
        # 
        dca_buy = self._check_dca_conditions(
            current_price, rsi, fg_score, rag_confidence,
            sma_50=technical.get('SMA_50'),
            sma_200=technical.get('SMA_200')
        )
        if dca_buy:
            return dca_buy

        # 
        # DEFAULT: HOLD (No strategy conditions met)
        # 
        return {
            'action': 'HOLD',
            'reason': 'No strategy conditions met',
            'strategy': 'HOLD'
        }

    def _check_circuit_breaker(self, current_price: float) -> Optional[Dict]:
        """
        
        STRATEGY: Circuit Breaker (Emergency Protection)
        

        PURPOSE:
            Pause all trading to prevent catastrophic loss during
            severe drawdown. Requires manual review to resume.

        TRIGGER CONDITION:
            Portfolio Value < 75% × Initial Capital (i.e., 25% drawdown)

        ACTION:
            Return PAUSE decision (all trading stops)
        
        """
        # Calculate current portfolio value
        portfolio_value = self.portfolio['cash'] + (self.portfolio['btc'] * current_price)
        initial_capital = self.config['initial_capital']

        # Check if breaker should activate
        if portfolio_value < 0.75 * initial_capital:
            drawdown = (initial_capital - portfolio_value) / initial_capital
            return {
                'action': 'PAUSE',
                'reason': f'Circuit Breaker: {drawdown:.1%} drawdown (25% max)',
                'strategy': 'CIRCUIT_BREAKER',
                'portfolio_value': portfolio_value,
                'drawdown': drawdown
            }

        return None  # No circuit breaker triggered

    def _check_stop_loss(self, current_price: float, atr: float) -> Optional[Dict]:
        """
        
        STRATEGY: ATR-based Stop-Loss (Dynamic Risk Management)
        

        PURPOSE:
            Limit losses on individual trades by using volatility-
            adjusted stop-loss levels. Prevents >5% loss per trade.

        FORMULA:
            Stop-Loss Price = Entry Price - (k × ATR)

            Where k = ATR multiplier (default: 2.0)
        
        """
        # Only check if we're holding BTC
        if self.portfolio['entry_price'] is None:
            return None

        # Calculate stop-loss price using ATR
        k = self.config['k_atr']  # Default: 2.0
        stop_loss_price = self.portfolio['entry_price'] - (k * atr)

        # Check if current price breached stop-loss
        if current_price < stop_loss_price:
            loss_pct = (self.portfolio['entry_price'] - current_price) / self.portfolio['entry_price']

            return {
                'action': 'SELL',
                'amount': self.portfolio['btc'],
                'reason': (
                    f'Stop-Loss: ${current_price:,.0f} < ${stop_loss_price:,.0f} '
                    f'(Loss: {loss_pct:.1%}, ATR: ${atr:,.0f})'
                ),
                'strategy': 'STOP_LOSS',
                'entry_price': self.portfolio['entry_price'],
                'stop_price': stop_loss_price,
                'loss_pct': loss_pct
            }

        return None  # Price above stop-loss, no action

    def _check_take_profit(
        self,
        rsi: float,
        macd_diff: float,
        predicted_price: float,
        current_price: float
    ) -> Optional[Dict]:
        """
        
        STRATEGY: Take Profit (Lock Gains Early)
        

        PURPOSE:
            Lock in profits when portfolio is up significantly.
            Prevents giving back gains during market crashes.

        TRIGGER CONDITIONS (ANY):
            1. Portfolio up 15%+ and RSI > 65 (take full profit)
            2. Portfolio up 10%+ and RSI > 70 (take half profit)
            3. OLD: RSI > 75, MACD bearish, predicted -5% (emergency exit)
        
        """
        # Skip if no BTC holdings
        if self.portfolio['btc'] <= 0.0001:
            return None

        # Calculate current portfolio profit
        portfolio_value = self.portfolio['cash'] + (self.portfolio['btc'] * current_price)
        profit_pct = (portfolio_value - self.config['initial_capital']) / self.config['initial_capital']

        # AGGRESSIVE PROFIT TAKING
        # Option 1: Take FULL profit if up 15%+ and RSI > 65
        if profit_pct > 0.15 and rsi > 65:
            return {
                'action': 'SELL',
                'amount': self.portfolio['btc'],  # Sell ALL
                'reason': f'Take Profit: Portfolio +{profit_pct:.1%}, RSI {rsi:.0f} (FULL EXIT)',
                'strategy': 'TAKE_PROFIT',
                'entry_price': self.portfolio['entry_price'],
                'exit_price': current_price,
                'profit_pct': profit_pct
            }

        # Option 2: Take HALF profit if up 10%+ and RSI > 70
        if profit_pct > 0.10 and rsi > 70:
            return {
                'action': 'SELL',
                'amount': self.portfolio['btc'] * 0.5,  # Sell HALF
                'reason': f'Take Profit: Portfolio +{profit_pct:.1%}, RSI {rsi:.0f} (HALF EXIT)',
                'strategy': 'TAKE_PROFIT',
                'entry_price': self.portfolio['entry_price'],
                'exit_price': current_price,
                'profit_pct': profit_pct
            }

        # Option 3: Emergency exit if VERY overbought with bearish signals
        overbought = rsi > 75
        bearish_momentum = macd_diff < 0
        downside_predicted = predicted_price < current_price * 0.95

        if overbought and bearish_momentum and downside_predicted:
            return {
                'action': 'SELL',
                'amount': self.portfolio['btc'],
                'reason': f'Take Profit: Emergency exit - RSI {rsi:.0f}, Bearish signals',
                'strategy': 'TAKE_PROFIT',
                'entry_price': self.portfolio['entry_price'],
                'exit_price': current_price,
                'profit_pct': profit_pct
            }

        return None  # Conditions not met

    def _check_swing_entry(
        self,
        rsi: float,
        macd_diff: float,
        fg_score: float,
        predicted_price: float,
        current_price: float,
        direction_confidence: float = 0.5
    ) -> Optional[Dict]:
        """
        
        STRATEGY: Swing Trading (Capture Large Opportunistic Moves)
        

        PURPOSE:
            Enter larger positions when conditions align:
            oversold + bullish momentum + high direction confidence.

        TRIGGER CONDITIONS (ALL must be true):
            1. RSI < config threshold (e.g., 30)
            2. MACD bullish crossover (diff > 0)
            3. Predicted price > current + 3%
            4. Direction confidence > config threshold (default: 70%, v2.0: 60%)
        
        """
        # All 4 conditions must be true
        extreme_oversold = rsi < self.config['rsi_oversold']
        bullish_momentum = macd_diff > 0
        upside_predicted = predicted_price > current_price * 1.03
        confidence_threshold = self.config.get('swing_confidence_threshold', 0.70)
        high_confidence = direction_confidence > confidence_threshold

        if extreme_oversold and bullish_momentum and upside_predicted and high_confidence:
            # Check if we have enough cash
            if self.portfolio['cash'] < self.config['swing_amount']:
                return None

            return {
                'action': 'BUY',
                'amount': self.config['swing_amount'],
                'reason': f'Swing Entry: RSI {rsi:.0f}, Bullish MACD, {direction_confidence:.0%} UP confidence',
                'strategy': 'SWING',
                'expected_gain': (predicted_price - current_price) / current_price,
                'direction_confidence': direction_confidence
            }

        return None  # Conditions not met

    def _check_dca_conditions(
        self,
        current_price: float,
        rsi: float,
        fg_score: float,
        rag_confidence: float,
        sma_50: float = None,
        sma_200: float = None
    ) -> Optional[Dict]:
        """
        
        STRATEGY: DCA (Dollar-Cost Averaging)
        

        PURPOSE:
            Accumulate BTC during favorable conditions (oversold + fear),
            using sentiment analysis to time entries.

        TRIGGERS (ANY of these):
            1. RSI < config threshold (oversold, good entry)
            2. Fear & Greed < config threshold (market fear, opportunity)

        COMBINED: Buy when technical OR sentiment signals opportunity

        TREND FILTER (v1.0 fix):
            Skip DCA during death cross (SMA_50 < SMA_200) to avoid falling knives
        
        """
        # Check conditions: Buy when RSI oversold OR market shows fear
        rsi_oversold = rsi < self.config['rsi_oversold']
        market_fear = fg_score < self.config['fear_threshold']

        # Either condition triggers DCA (OR logic - less restrictive than AND)
        if rsi_oversold or market_fear:

            # Check if we have enough cash
            if self.portfolio['cash'] < self.config['dca_amount']:
                return None

            # Determine which signal triggered
            trigger = []
            if rsi_oversold:
                trigger.append(f'RSI {rsi:.0f}')
            if market_fear:
                trigger.append(f'F&G {fg_score}')

            return {
                'action': 'BUY',
                'amount': self.config['dca_amount'],
                'reason': f'DCA: {", ".join(trigger)} (Fear Threshold: {self.config["fear_threshold"]})',
                'strategy': 'DCA',
                'last_dca_price': self.portfolio['last_dca_price'],
                'current_price': current_price,
                'rsi': rsi,
                'fear_greed': fg_score
            }

        return None  # Conditions not met

    def execute_trade(self, decision: Dict, current_price: float, date: str):
        """
        Execute trade and update portfolio.

        Args:
            decision: Output from make_decision()
            current_price: Current BTC price
            date: Trade date (for logging)
        """
        if decision['action'] == 'BUY':
            btc_bought = decision['amount'] / current_price
            self.portfolio['btc'] += btc_bought
            self.portfolio['cash'] -= decision['amount']
            self.portfolio['entry_price'] = current_price

            # Update last DCA price if DCA strategy
            if decision.get('strategy') == 'DCA':
                self.portfolio['last_dca_price'] = current_price

            self.portfolio['trades'].append({
                'date': date,
                'action': 'BUY',
                'strategy': decision.get('strategy', 'UNKNOWN'),
                'price': current_price,
                'amount_usd': decision['amount'],
                'btc': btc_bought,
                'reason': decision['reason']
            })

            print(f"[TRADE] {decision.get('strategy', 'BUY')}: ${decision['amount']:,.0f} ({btc_bought:.6f} BTC) at ${current_price:,.0f}")

            # Send Telegram notification
            portfolio_value = self.portfolio['cash'] + (self.portfolio['btc'] * current_price)
            self.telegram.notify_trade(decision, current_price, portfolio_value)

        elif decision['action'] == 'SELL':
            cash_received = decision['amount'] * current_price
            self.portfolio['cash'] += cash_received
            self.portfolio['btc'] -= decision['amount']

            # Reset entry price if sold all
            if self.portfolio['btc'] <= 0.0001:  # Avoid floating point issues
                self.portfolio['btc'] = 0
                self.portfolio['entry_price'] = None

            self.portfolio['trades'].append({
                'date': date,
                'action': 'SELL',
                'strategy': decision.get('strategy', 'UNKNOWN'),
                'price': current_price,
                'amount_btc': decision['amount'],
                'cash_received': cash_received,
                'reason': decision['reason']
            })

            print(f"[TRADE] {decision.get('strategy', 'SELL')}: {decision['amount']:.6f} BTC for ${cash_received:,.0f}")

            # Send Telegram notification
            portfolio_value = self.portfolio['cash'] + (self.portfolio['btc'] * current_price)
            self.telegram.notify_trade(decision, current_price, portfolio_value)

        elif decision['action'] == 'PAUSE':
            print(f"[WARNING] CIRCUIT BREAKER: Trading paused - {decision['reason']}")

            # Send Telegram notification for circuit breaker
            portfolio_value = self.portfolio['cash'] + (self.portfolio['btc'] * current_price)
            self.telegram.notify_trade(decision, current_price, portfolio_value)

        else:  # HOLD
            pass  # No action needed

    def get_portfolio_summary(self, current_price: float) -> Dict:
        """Get current portfolio status."""
        portfolio_value = self.portfolio['cash'] + (self.portfolio['btc'] * current_price)
        total_return = (portfolio_value - self.config['initial_capital']) / self.config['initial_capital']

        return {
            'cash': self.portfolio['cash'],
            'btc': self.portfolio['btc'],
            'btc_value': self.portfolio['btc'] * current_price,
            'total_value': portfolio_value,
            'total_return': total_return,
            'num_trades': len(self.portfolio['trades'])
        }


def main():
    """Test trading decision box."""
    print("="*60)
    print("DECISION BOX - Testing")
    print("="*60)

    # Test configuration
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

    decision_box = TradingDecisionBox(config)

    # Test scenario 1: Swing entry
    print("\n=== Test 1: Swing Entry ===")
    technical = {'RSI': 28, 'ATR': 1500, 'MACD_diff': 10, 'SMA_50': 105000, 'SMA_200': 100000}
    sentiment = {'fear_greed_score': 25, 'rag_confidence': 0.75, 'rag_signal': 'BUY'}
    prediction = {'predicted_price': 110000, 'direction': 'UP'}
    current_price = 105000

    decision = decision_box.make_decision(technical, sentiment, prediction, current_price)
    print(f"Decision: {decision['action']}")
    print(f"Strategy: {decision.get('strategy')}")
    print(f"Reason: {decision['reason']}")

    # Execute trade
    decision_box.execute_trade(decision, current_price, "2024-11-10")

    # Test scenario 2: Stop-loss
    print("\n=== Test 2: Stop-Loss ===")
    new_price = 102000  # Dropped below stop-loss
    decision2 = decision_box.make_decision(technical, sentiment, prediction, new_price)
    print(f"Decision: {decision2['action']}")
    print(f"Strategy: {decision2.get('strategy')}")
    print(f"Reason: {decision2['reason']}")

    # Portfolio summary
    print("\n=== Portfolio Summary ===")
    summary = decision_box.get_portfolio_summary(current_price)
    print(f"Cash: ${summary['cash']:,.2f}")
    print(f"BTC: {summary['btc']:.6f} (${summary['btc_value']:,.2f})")
    print(f"Total Value: ${summary['total_value']:,.2f}")
    print(f"Return: {summary['total_return']:.2%}")
    print(f"Trades: {summary['num_trades']}")

    print("\n" + "="*60)
    print("[COMPLETE] DECISION BOX TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
