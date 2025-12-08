"""

TELEGRAM NOTIFIER - Real-time Trade Alerts


PURPOSE:
    Send immediate Telegram notifications for all executed trades
    (BUY, SELL, PAUSE events).

SUCCESS CRITERIA:
     Notifications sent within 1 second of trade execution
     Message includes: action, strategy, price, amount, reason
     Graceful fallback if Telegram fails (doesn't break trading)
     Circuit breaker alerts sent immediately

SETUP:
    1. Create Telegram bot via @BotFather
    2. Get bot token from BotFather
    3. Get your chat_id by messaging @userinfobot
    4. Add to .env file:
       TELEGRAM_BOT_TOKEN=your_token_here
       TELEGRAM_CHAT_ID=your_chat_id_here


"""

import os
import requests
from typing import Dict, Optional
from pathlib import Path
from dotenv import load_dotenv


class TelegramNotifier:
    """
    Send trade notifications via Telegram Bot API.

    Features:
    - Real-time trade alerts (BUY/SELL)
    - Circuit breaker warnings
    - Portfolio summaries
    - Graceful error handling (won't break trading if Telegram fails)
    """

    def __init__(self, bot_token: str = None, chat_id: str = None, enabled: bool = True):
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token (from @BotFather)
            chat_id: Your Telegram chat ID (from @userinfobot)
            enabled: Enable/disable notifications (useful for backtesting)

        If bot_token or chat_id not provided, loads from .env file.
        """
        # Load .env file if exists
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)

        # Get credentials
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = enabled

        # Disable if credentials missing
        if not self.bot_token or not self.chat_id:
            self.enabled = False
            if enabled:  # Only warn if user wanted it enabled
                print("[TELEGRAM] Warning: Bot token or chat ID not configured. Notifications disabled.")
                print("[TELEGRAM] To enable: Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env file")

        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None

    def send_message(self, message: str) -> bool:
        """
        Send a message to Telegram.

        Args:
            message: Text message to send

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.api_url:
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'  # Enables bold, italic formatting
            }

            response = requests.post(self.api_url, json=payload, timeout=5)

            if response.status_code == 200:
                return True
            else:
                print(f"[TELEGRAM] Error: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.Timeout:
            print("[TELEGRAM] Error: Request timeout (>5 seconds)")
            return False
        except requests.exceptions.RequestException as e:
            print(f"[TELEGRAM] Error: {str(e)}")
            return False
        except Exception as e:
            print(f"[TELEGRAM] Unexpected error: {str(e)}")
            return False

    def notify_trade(self, decision: Dict, current_price: float, portfolio_value: float = None) -> bool:
        """
        Send trade notification.

        Args:
            decision: Trade decision dict from TradingDecisionBox
            current_price: Current BTC price
            portfolio_value: Optional current portfolio value

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        action = decision.get('action', 'UNKNOWN')
        strategy = decision.get('strategy', 'UNKNOWN')
        reason = decision.get('reason', 'No reason provided')
        amount = decision.get('amount', 0)

        # Format message based on action
        if action == 'BUY':
            btc_bought = amount / current_price
            message = f"""
 *BUY SIGNAL EXECUTED*

*Strategy:* {strategy}
*Price:* ${current_price:,.2f}
*Amount:* ${amount:,.2f}
*BTC Acquired:* {btc_bought:.6f} BTC

*Reason:* {reason}
"""
            if portfolio_value:
                message += f"\n*Portfolio Value:* ${portfolio_value:,.2f}"

        elif action == 'SELL':
            cash_received = amount * current_price
            message = f"""
 *SELL SIGNAL EXECUTED*

*Strategy:* {strategy}
*Price:* ${current_price:,.2f}
*BTC Sold:* {amount:.6f} BTC
*Cash Received:* ${cash_received:,.2f}

*Reason:* {reason}
"""
            if portfolio_value:
                message += f"\n*Portfolio Value:* ${portfolio_value:,.2f}"

        elif action == 'PAUSE':
            message = f"""
 *CIRCUIT BREAKER ACTIVATED*

*Trading has been PAUSED*

*Reason:* {reason}

*Current Price:* ${current_price:,.2f}
"""
            if portfolio_value:
                message += f"*Portfolio Value:* ${portfolio_value:,.2f}"

        else:
            # HOLD or unknown - don't send notification
            return False

        return self.send_message(message)

    def notify_portfolio_summary(self, portfolio_summary: Dict, current_price: float) -> bool:
        """
        Send portfolio summary notification.

        Args:
            portfolio_summary: Portfolio dict from get_portfolio_summary()
            current_price: Current BTC price

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        cash = portfolio_summary.get('cash', 0)
        btc = portfolio_summary.get('btc', 0)
        total_value = portfolio_summary.get('total_value', 0)
        total_return = portfolio_summary.get('total_return', 0)
        num_trades = portfolio_summary.get('num_trades', 0)

        message = f"""
 *PORTFOLIO SUMMARY*

*BTC Holdings:* {btc:.6f} BTC
*BTC Value:* ${btc * current_price:,.2f}
*Cash:* ${cash:,.2f}
*Total Value:* ${total_value:,.2f}

*Total Return:* {total_return * 100:+.2f}%
*Total Trades:* {num_trades}

*Current BTC Price:* ${current_price:,.2f}
"""

        return self.send_message(message)

    def notify_error(self, error_message: str) -> bool:
        """
        Send error notification.

        Args:
            error_message: Error description

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        message = f"""
 *ERROR ALERT*

{error_message}

Please check the trading bot immediately.
"""

        return self.send_message(message)

    def test_connection(self) -> bool:
        """
        Test Telegram connection.

        Returns:
            True if connection successful
        """
        if not self.enabled:
            print("[TELEGRAM] Notifications are disabled.")
            return False

        message = " *BTC Intelligent Trader Bot Connected*\n\nTelegram notifications are active!"
        success = self.send_message(message)

        if success:
            print("[TELEGRAM]  Test message sent successfully!")
        else:
            print("[TELEGRAM]  Failed to send test message.")

        return success


def main():
    """Test Telegram notifier."""
    print("=" * 60)
    print("TELEGRAM NOTIFIER - Testing")
    print("=" * 60)

    # Create notifier
    notifier = TelegramNotifier()

    if not notifier.enabled:
        print("\n Telegram not configured.")
        print("\nTo set up:")
        print("1. Message @BotFather on Telegram")
        print("2. Use /newbot command to create a bot")
        print("3. Copy the bot token")
        print("4. Message @userinfobot to get your chat_id")
        print("5. Create .env file with:")
        print("   TELEGRAM_BOT_TOKEN=your_token_here")
        print("   TELEGRAM_CHAT_ID=your_chat_id_here")
        return

    # Test connection
    print("\n[TEST 1] Testing connection...")
    notifier.test_connection()

    # Test BUY notification
    print("\n[TEST 2] Testing BUY notification...")
    buy_decision = {
        'action': 'BUY',
        'amount': 1000,
        'reason': 'DCA: RSI < 30 (Fear Threshold: 40)',
        'strategy': 'DCA'
    }
    notifier.notify_trade(buy_decision, current_price=95000, portfolio_value=10000)

    # Test SELL notification
    print("\n[TEST 3] Testing SELL notification...")
    sell_decision = {
        'action': 'SELL',
        'amount': 0.01,
        'reason': 'Take Profit: +15% gain, RSI > 65',
        'strategy': 'Take Profit'
    }
    notifier.notify_trade(sell_decision, current_price=97000, portfolio_value=11500)

    # Test PAUSE notification
    print("\n[TEST 4] Testing CIRCUIT BREAKER notification...")
    pause_decision = {
        'action': 'PAUSE',
        'reason': 'Portfolio value below 75% of initial capital',
        'strategy': 'Circuit Breaker'
    }
    notifier.notify_trade(pause_decision, current_price=90000, portfolio_value=7500)

    # Test portfolio summary
    print("\n[TEST 5] Testing portfolio summary...")
    portfolio = {
        'cash': 5000,
        'btc': 0.05,
        'total_value': 9750,
        'total_return': -0.025,
        'num_trades': 12
    }
    notifier.notify_portfolio_summary(portfolio, current_price=95000)

    print("\n" + "=" * 60)
    print(" All tests complete! Check your Telegram for messages.")
    print("=" * 60)


if __name__ == "__main__":
    main()
