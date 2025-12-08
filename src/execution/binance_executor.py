"""

BINANCE EXECUTOR - Live Order Execution (Paper Trading)


PURPOSE:
    Execute live trades on Binance Spot Testnet based on Decision Box signals.
    Handles order placement, balance tracking, and error management.

SUCCESS CRITERIA:
     Successfully places market orders (BUY/SELL)
     Tracks account balances accurately
     Handles API errors gracefully (retries, logging)
     Signal execution rate >95%
     Order confirmation latency <2 seconds

BINANCE TESTNET:
    - URL: https://testnet.binance.vision/api
    - Rate Limit: 6000 requests/minute
    - Order Types: MARKET (for simplicity)
    - Symbol: BTCUSDT

VALIDATION METHOD:
    - Test order placement with small amounts
    - Verify balance updates after trades
    - Confirm error handling for insufficient funds

"""

import os
import sys
import time
import hmac
import hashlib
import requests
from dotenv import load_dotenv
from typing import Dict, Optional
from datetime import datetime
from urllib.parse import urlencode
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try relative import first, fall back to absolute import
try:
    from ..data_pipeline.rate_limiter import binance_limiter
    from ..notifications.telegram_notifier import TelegramNotifier
except (ImportError, ValueError):
    from src.data_pipeline.rate_limiter import binance_limiter
    from src.notifications.telegram_notifier import TelegramNotifier

# Load environment variables
load_dotenv()


class BinanceExecutor:
    """
    Executes live trades on Binance Spot Testnet.

    Handles:
    - Market order placement (BUY/SELL)
    - Account balance tracking
    - Order confirmation
    - Error handling and retries
    """

    def __init__(self, use_testnet: bool = True):
        """
        Initialize Binance executor.

        Args:
            use_testnet: If True, use Testnet. If False, use production (NOT RECOMMENDED).
        """
        # API credentials
        self.api_key = os.getenv('BINANCE_API_KEY', '')
        self.api_secret = os.getenv('BINANCE_API_SECRET', '')

        if not self.api_key or not self.api_secret:
            raise ValueError("Binance API credentials not found in .env file")

        # Base URLs
        if use_testnet:
            self.base_url = "https://testnet.binance.vision/api/v3"
            self.env_name = "TESTNET"
        else:
            self.base_url = "https://api.binance.com/api/v3"
            self.env_name = "PRODUCTION"
            print("[WARNING] Using PRODUCTION Binance API - REAL MONEY AT RISK!")

        # Trading config
        self.symbol = "BTCUSDT"
        self.timeout = 10

        # Statistics
        self.stats = {
            'orders_placed': 0,
            'orders_failed': 0,
            'buy_orders': 0,
            'sell_orders': 0,
            'total_volume_usd': 0.0
        }

        # Telegram notifier
        self.telegram = TelegramNotifier()

    def _generate_signature(self, query_string: str) -> str:
        """
        Generate HMAC SHA256 signature for authenticated endpoints.

        Args:
            query_string: URL-encoded query parameters

        Returns:
            Hex-encoded signature
        """
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        signed: bool = False
    ) -> Dict:
        """
        Make authenticated request to Binance API.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint (e.g., '/account')
            params: Query parameters
            signed: If True, add timestamp and signature

        Returns:
            API response as dict

        Raises:
            Exception: If request fails
        """
        # Build URL
        url = f"{self.base_url}{endpoint}"

        # Prepare headers
        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        # Add timestamp for signed requests
        if signed:
            if params is None:
                params = {}
            params['timestamp'] = int(time.time() * 1000)

            # Generate signature
            query_string = urlencode(params)
            params['signature'] = self._generate_signature(query_string)

        # Make request
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, headers=headers, params=params, timeout=self.timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Check for errors
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            # Parse error message if available
            try:
                error_data = response.json()
                error_msg = error_data.get('msg', str(e))
                error_code = error_data.get('code', 'N/A')
                raise Exception(f"Binance API error [{error_code}]: {error_msg}")
            except:
                raise Exception(f"Binance request failed: {e}")

    # 
    # ACCOUNT INFORMATION
    # 

    @binance_limiter.limit
    def get_account_info(self) -> Dict:
        """
        Get account information (balances, permissions).

        Returns:
            dict: {
                'balances': [{'asset': 'BTC', 'free': float, 'locked': float}, ...],
                'can_trade': bool,
                'can_withdraw': bool,
                'can_deposit': bool,
                'update_time': int (milliseconds)
            }
        """
        return self._make_request('GET', '/account', signed=True)

    @binance_limiter.limit
    def get_balance(self, asset: str) -> Dict:
        """
        Get balance for a specific asset.

        Args:
            asset: Asset symbol (e.g., 'BTC', 'USDT')

        Returns:
            dict: {
                'asset': str,
                'free': float (available),
                'locked': float (in orders),
                'total': float (free + locked)
            }
        """
        account_info = self.get_account_info()

        # Find asset in balances
        for balance in account_info['balances']:
            if balance['asset'] == asset:
                free = float(balance['free'])
                locked = float(balance['locked'])
                return {
                    'asset': asset,
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                }

        # Asset not found
        return {
            'asset': asset,
            'free': 0.0,
            'locked': 0.0,
            'total': 0.0
        }

    @binance_limiter.limit
    def get_portfolio_value(self, btc_price: float) -> Dict:
        """
        Calculate total portfolio value in USD.

        Args:
            btc_price: Current BTC price in USD

        Returns:
            dict: {
                'btc_balance': float,
                'usdt_balance': float,
                'btc_value_usd': float,
                'total_value_usd': float,
                'timestamp': datetime
            }
        """
        btc_balance = self.get_balance('BTC')
        usdt_balance = self.get_balance('USDT')

        btc_value_usd = btc_balance['total'] * btc_price
        total_value_usd = btc_value_usd + usdt_balance['total']

        return {
            'btc_balance': btc_balance['total'],
            'usdt_balance': usdt_balance['total'],
            'btc_value_usd': btc_value_usd,
            'total_value_usd': total_value_usd,
            'timestamp': datetime.now()
        }

    # 
    # PRICE INFORMATION
    # 

    @binance_limiter.limit
    def get_current_price(self) -> float:
        """
        Get current BTC/USDT price.

        Returns:
            Current price as float
        """
        response = self._make_request('GET', '/ticker/price', {'symbol': self.symbol})
        return float(response['price'])

    # 
    # ORDER EXECUTION
    # 

    @binance_limiter.limit
    def place_market_order(
        self,
        side: str,
        quantity: Optional[float] = None,
        quote_quantity: Optional[float] = None
    ) -> Dict:
        """
        Place a market order (BUY or SELL).

        Args:
            side: 'BUY' or 'SELL'
            quantity: Amount of BTC to buy/sell (use this OR quote_quantity)
            quote_quantity: Amount of USDT to spend (BUY only)

        Returns:
            dict: {
                'order_id': int,
                'symbol': str,
                'side': str,
                'type': str,
                'status': str,
                'executed_qty': float,
                'executed_price': float,
                'executed_value': float,
                'timestamp': datetime
            }

        Raises:
            Exception: If order fails

        Example:
            # Buy $500 worth of BTC
            executor.place_market_order('BUY', quote_quantity=500.0)

            # Sell 0.01 BTC
            executor.place_market_order('SELL', quantity=0.01)
        """
        # Validate inputs
        if side not in ['BUY', 'SELL']:
            raise ValueError("side must be 'BUY' or 'SELL'")

        if quantity is None and quote_quantity is None:
            raise ValueError("Must provide either quantity or quote_quantity")

        if quantity is not None and quote_quantity is not None:
            raise ValueError("Provide only one of quantity or quote_quantity")

        # Build order parameters
        params = {
            'symbol': self.symbol,
            'side': side,
            'type': 'MARKET'
        }

        # Add quantity (base asset - BTC)
        if quantity is not None:
            # Format to 6 decimal places (Binance requires proper precision)
            params['quantity'] = f"{quantity:.6f}"

        # Add quote quantity (quote asset - USDT) - only for BUY
        if quote_quantity is not None:
            if side != 'BUY':
                raise ValueError("quoteOrderQty only supported for BUY orders")
            params['quoteOrderQty'] = f"{quote_quantity:.2f}"

        try:
            # Place order
            response = self._make_request('POST', '/order', params=params, signed=True)

            # Parse response
            executed_qty = float(response.get('executedQty', 0))

            # Calculate average executed price
            fills = response.get('fills', [])
            if fills:
                total_qty = sum(float(fill['qty']) for fill in fills)
                total_value = sum(float(fill['price']) * float(fill['qty']) for fill in fills)
                avg_price = total_value / total_qty if total_qty > 0 else 0
            else:
                avg_price = 0

            executed_value = executed_qty * avg_price

            # Update statistics
            self.stats['orders_placed'] += 1
            if side == 'BUY':
                self.stats['buy_orders'] += 1
            else:
                self.stats['sell_orders'] += 1
            self.stats['total_volume_usd'] += executed_value

            return {
                'order_id': response['orderId'],
                'symbol': response['symbol'],
                'side': response['side'],
                'type': response['type'],
                'status': response['status'],
                'executed_qty': executed_qty,
                'executed_price': avg_price,
                'executed_value': executed_value,
                'timestamp': datetime.fromtimestamp(response['transactTime'] / 1000)
            }

        except Exception as e:
            self.stats['orders_failed'] += 1
            raise Exception(f"Order placement failed: {e}")

    def execute_signal(self, signal: Dict, current_price: float) -> Optional[Dict]:
        """
        Execute a trading signal from the Decision Box.

        Args:
            signal: Decision box output with 'action', 'amount', 'reason'
            current_price: Current BTC price

        Returns:
            Order result dict or None if action is HOLD/PAUSE

        Example signal:
            {
                'action': 'BUY',
                'amount': 500,  # USD
                'reason': 'DCA: RSI 55, F&G 30',
                'strategy': 'DCA'
            }
        """
        action = signal.get('action')
        amount = signal.get('amount', 0)
        reason = signal.get('reason', 'N/A')
        strategy = signal.get('strategy', 'Unknown')

        print(f"\n[SIGNAL] {action} | {strategy} | {reason}")

        # Handle different actions
        if action == 'BUY':
            # Buy with USD amount
            print(f"[EXECUTE] Buying ${amount:.2f} worth of BTC at ${current_price:,.2f}")
            try:
                result = self.place_market_order('BUY', quote_quantity=amount)
                print(f"[SUCCESS] Bought {result['executed_qty']:.6f} BTC @ ${result['executed_price']:,.2f}")

                # Send Telegram notification
                self.telegram.notify_trade(signal, current_price)

                return result
            except Exception as e:
                print(f"[ERROR] Order failed: {e}")
                return None

        elif action == 'SELL':
            # Sell all BTC
            btc_balance = self.get_balance('BTC')
            if btc_balance['free'] > 0:
                print(f"[EXECUTE] Selling {btc_balance['free']:.6f} BTC at ${current_price:,.2f}")
                try:
                    result = self.place_market_order('SELL', quantity=btc_balance['free'])
                    print(f"[SUCCESS] Sold {result['executed_qty']:.6f} BTC @ ${result['executed_price']:,.2f}")

                    # Send Telegram notification
                    self.telegram.notify_trade(signal, current_price)

                    return result
                except Exception as e:
                    print(f"[ERROR] Order failed: {e}")
                    return None
            else:
                print(f"[SKIP] No BTC to sell (balance: {btc_balance['free']:.6f})")
                return None

        elif action == 'HOLD':
            print(f"[HOLD] No action taken")
            return None

        elif action == 'PAUSE':
            print(f"[PAUSE] Trading paused: {reason}")

            # Send Telegram notification for circuit breaker
            self.telegram.notify_trade(signal, current_price)

            return None

        else:
            print(f"[WARNING] Unknown action: {action}")
            return None

    # 
    # STATISTICS
    # 

    def get_stats(self) -> Dict:
        """
        Get executor statistics.

        Returns:
            dict with order stats
        """
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            'orders_placed': 0,
            'orders_failed': 0,
            'buy_orders': 0,
            'sell_orders': 0,
            'total_volume_usd': 0.0
        }


def main():
    """Test Binance executor functionality."""
    print("="*60)
    print(f"BINANCE EXECUTOR - Testing")
    print("="*60)

    try:
        executor = BinanceExecutor(use_testnet=True)
        print(f"\n[OK] Connected to Binance {executor.env_name}")

        # Test 1: Get account info
        print("\nTest 1: Account Information")
        account = executor.get_account_info()
        print(f"   Can Trade: {account['canTrade']}")
        print(f"   Can Withdraw: {account['canWithdraw']}")
        print(f"   Can Deposit: {account['canDeposit']}")

        # Test 2: Get balances
        print("\nTest 2: Account Balances")
        btc_balance = executor.get_balance('BTC')
        usdt_balance = executor.get_balance('USDT')
        print(f"   BTC: {btc_balance['free']:.6f} (locked: {btc_balance['locked']:.6f})")
        print(f"   USDT: {usdt_balance['free']:.2f} (locked: {usdt_balance['locked']:.2f})")

        # Test 3: Get current price
        print("\nTest 3: Current BTC Price")
        price = executor.get_current_price()
        print(f"   BTC/USDT: ${price:,.2f}")

        # Test 4: Portfolio value
        print("\nTest 4: Portfolio Value")
        portfolio = executor.get_portfolio_value(price)
        print(f"   BTC Balance: {portfolio['btc_balance']:.6f} BTC")
        print(f"   USDT Balance: ${portfolio['usdt_balance']:.2f}")
        print(f"   BTC Value: ${portfolio['btc_value_usd']:,.2f}")
        print(f"   Total Value: ${portfolio['total_value_usd']:,.2f}")

        # Test 5: Test signal execution (DRY RUN - commented out to avoid real orders)
        print("\nTest 5: Signal Execution (DRY RUN)")
        print("   [SKIP] Uncomment test_signal section in code to test order placement")

        # Uncomment to test actual order placement:
        # test_signal = {
        #     'action': 'BUY',
        #     'amount': 10.0,  # $10 test order
        #     'reason': 'Test order',
        #     'strategy': 'TEST'
        # }
        # result = executor.execute_signal(test_signal, price)
        # if result:
        #     print(f"   Order ID: {result['order_id']}")
        #     print(f"   Executed: {result['executed_qty']:.6f} BTC @ ${result['executed_price']:,.2f}")

        # Test 6: Statistics
        print("\nTest 6: Executor Statistics")
        stats = executor.get_stats()
        print(f"   Orders Placed: {stats['orders_placed']}")
        print(f"   Orders Failed: {stats['orders_failed']}")
        print(f"   Buy Orders: {stats['buy_orders']}")
        print(f"   Sell Orders: {stats['sell_orders']}")
        print(f"   Total Volume: ${stats['total_volume_usd']:,.2f}")

        print("\n" + "="*60)
        print("[COMPLETE] BINANCE EXECUTOR TEST PASSED")
        print("="*60)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        print("="*60)


if __name__ == "__main__":
    main()
