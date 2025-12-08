"""
CoinGecko MCP Client - Live Cryptocurrency Data

PURPOSE:
    Fetch live Bitcoin price and market data from CoinGecko API.
    Provides real-time data as alternative to historical CSV files.

RATE LIMITS (Demo API - FREE):
    - 30 calls per minute
    - 10,000 calls per month
    - Stable, not shared with other users

WHEN TO USE:
    - Natural language interface (chat mode) for live prices
    - Real-time market data queries
    - Current price, market cap, volume checks

WHEN NOT TO USE:
    - Backtesting (use CSV historical data)
    - Bulk historical data (use CSV)
    - High-frequency queries (respect rate limits)

FALLBACK STRATEGY:
    If CoinGecko API unavailable or rate limited:
    1. Return None
    2. Caller should fall back to latest CSV data
    3. Log warning but don't break the application

SUCCESS CRITERIA:
    - Fetches live BTC price successfully
    - Respects rate limits (30 calls/min)
    - Returns None gracefully on errors
    - Does not break app if API unavailable
    - Provides market data (price, volume, market cap)

"""

import os
import time
from typing import Dict, Optional, List
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()


class CoinGeckoMCP:
    """
    CoinGecko MCP client for live cryptocurrency data.

    Uses Demo API (FREE):
    - 30 calls/minute
    - 10,000 calls/month
    - No credit card required

    Example Usage:
        mcp = CoinGeckoMCP()

        # Get current price
        price_data = mcp.get_bitcoin_price()
        if price_data:
            print(f"BTC Price: ${price_data['price']:,.2f}")

        # Get market chart
        chart_data = mcp.get_market_chart(days=7)
    """

    def __init__(self):
        """
        Initialize CoinGecko MCP client.

        Checks for API key in environment variables:
        - COINGECKO_DEMO_API_KEY (Demo API - free)
        - COINGECKO_PRO_API_KEY (Pro API - paid)
        - COINGECKO_ENVIRONMENT (demo or pro)

        If no API key found, client is disabled but won't crash.
        """
        # Get API credentials from environment
        self.demo_api_key = os.getenv('COINGECKO_DEMO_API_KEY')
        self.pro_api_key = os.getenv('COINGECKO_PRO_API_KEY')
        self.environment = os.getenv('COINGECKO_ENVIRONMENT', 'demo').lower()

        # Determine which API to use
        if self.environment == 'pro' and self.pro_api_key:
            self.api_key = self.pro_api_key
            self.base_url = 'https://pro-api.coingecko.com/api/v3'
            self.rate_limit = 500  # calls per minute
            print("[COINGECKO] Using Pro API")
        elif self.demo_api_key:
            self.api_key = self.demo_api_key
            self.base_url = 'https://api.coingecko.com/api/v3'
            self.rate_limit = 30  # calls per minute
            print("[COINGECKO] Using Demo API (free tier)")
        else:
            self.api_key = None
            self.base_url = None
            self.rate_limit = 0
            print("[COINGECKO] No API key found - MCP disabled")
            print("[COINGECKO] To enable: Set COINGECKO_DEMO_API_KEY in .env")

        self.enabled = bool(self.api_key)

        # Rate limiting tracking
        self.last_request_time = 0
        self.min_request_interval = 60.0 / self.rate_limit if self.rate_limit > 0 else 2.0

    def _wait_for_rate_limit(self):
        """
        Wait if needed to respect rate limits.

        Rate limiting:
        - Demo: 30 calls/min = 1 call every 2 seconds
        - Pro: 500 calls/min = 1 call every 0.12 seconds
        """
        if not self.enabled:
            return

        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            time.sleep(wait_time)

        self.last_request_time = time.time()

    def get_bitcoin_price(self) -> Optional[Dict]:
        """
        Get current Bitcoin price and market data.

        Returns:
            {
                'price': 98234.56,           # Current price in USD
                'market_cap': 1934567890123,  # Market capitalization
                'volume_24h': 45678901234,    # 24h trading volume
                'price_change_24h': 2.5,      # 24h price change percentage
                'timestamp': '2025-12-07T...' # When data was fetched
            }

            None if API unavailable or error occurred

        Example:
            mcp = CoinGeckoMCP()
            data = mcp.get_bitcoin_price()
            if data:
                print(f"BTC: ${data['price']:,.2f} ({data['price_change_24h']:+.2f}%)")
        """
        if not self.enabled:
            return None

        try:
            self._wait_for_rate_limit()

            url = f"{self.base_url}/simple/price"
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'x_cg_demo_api_key': self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()['bitcoin']

            return {
                'price': data['usd'],
                'market_cap': data['usd_market_cap'],
                'volume_24h': data['usd_24h_vol'],
                'price_change_24h': data['usd_24h_change'],
                'timestamp': datetime.now().isoformat()
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("[COINGECKO] Rate limit exceeded - wait before retrying")
            else:
                print(f"[COINGECKO] HTTP error: {e}")
            return None

        except requests.exceptions.Timeout:
            print("[COINGECKO] Request timeout")
            return None

        except Exception as e:
            print(f"[COINGECKO] Error fetching price: {e}")
            return None

    def get_market_chart(self, days: int = 7) -> Optional[Dict]:
        """
        Get historical price chart data.

        Args:
            days: Number of days of history
                  Valid values: 1, 7, 14, 30, 90, 180, 365, max

        Returns:
            {
                'prices': [[timestamp, price], ...],
                'market_caps': [[timestamp, market_cap], ...],
                'total_volumes': [[timestamp, volume], ...]
            }

            None if API unavailable or error occurred

        Example:
            mcp = CoinGeckoMCP()
            chart = mcp.get_market_chart(days=7)
            if chart:
                latest_price = chart['prices'][-1][1]
                print(f"Latest price: ${latest_price:,.2f}")
        """
        if not self.enabled:
            return None

        try:
            self._wait_for_rate_limit()

            url = f"{self.base_url}/coins/bitcoin/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'x_cg_demo_api_key': self.api_key
            }

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("[COINGECKO] Rate limit exceeded - wait before retrying")
            else:
                print(f"[COINGECKO] HTTP error: {e}")
            return None

        except requests.exceptions.Timeout:
            print("[COINGECKO] Request timeout")
            return None

        except Exception as e:
            print(f"[COINGECKO] Error fetching market chart: {e}")
            return None

    def get_trending_coins(self, limit: int = 7) -> Optional[List[Dict]]:
        """
        Get trending coins on CoinGecko.

        Args:
            limit: Number of trending coins to return (max 7)

        Returns:
            List of trending coin data or None if error

        Example:
            mcp = CoinGeckoMCP()
            trending = mcp.get_trending_coins(limit=5)
            if trending:
                for coin in trending:
                    print(f"{coin['name']}: ${coin['price']:,.2f}")
        """
        if not self.enabled:
            return None

        try:
            self._wait_for_rate_limit()

            url = f"{self.base_url}/search/trending"
            params = {
                'x_cg_demo_api_key': self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            trending_coins = []

            for item in data.get('coins', [])[:limit]:
                coin = item.get('item', {})
                trending_coins.append({
                    'id': coin.get('id'),
                    'name': coin.get('name'),
                    'symbol': coin.get('symbol'),
                    'market_cap_rank': coin.get('market_cap_rank'),
                    'price': coin.get('data', {}).get('price')
                })

            return trending_coins

        except Exception as e:
            print(f"[COINGECKO] Error fetching trending coins: {e}")
            return None


def main():
    """
    Test CoinGecko MCP client.

    SUCCESS CRITERIA:
        - Connects to CoinGecko API
        - Fetches Bitcoin price successfully
        - Returns data in correct format
        - Respects rate limits
        - Handles errors gracefully
    """
    print("="*60)
    print("COINGECKO MCP CLIENT - Test Mode")
    print("="*60)

    # Initialize client
    mcp = CoinGeckoMCP()

    if not mcp.enabled:
        print("\n[ERROR] CoinGecko MCP disabled (no API key)")
        print("\nTo enable:")
        print("1. Get free Demo API key from: https://www.coingecko.com/en/api/pricing")
        print("2. Add to .env file:")
        print("   COINGECKO_DEMO_API_KEY=your_key_here")
        print("   COINGECKO_ENVIRONMENT=demo")
        return

    # Test 1: Get Bitcoin price
    print("\nTest 1: Fetching Bitcoin price...")
    price_data = mcp.get_bitcoin_price()

    if price_data:
        print("[OK] Bitcoin price fetched successfully")
        print(f"  Price: ${price_data['price']:,.2f}")
        print(f"  Market Cap: ${price_data['market_cap']:,.0f}")
        print(f"  24h Volume: ${price_data['volume_24h']:,.0f}")
        print(f"  24h Change: {price_data['price_change_24h']:+.2f}%")
        print(f"  Timestamp: {price_data['timestamp']}")
    else:
        print("[FAILED] Could not fetch Bitcoin price")

    # Test 2: Get market chart
    print("\nTest 2: Fetching 7-day market chart...")
    chart_data = mcp.get_market_chart(days=7)

    if chart_data:
        print("[OK] Market chart fetched successfully")
        print(f"  Price data points: {len(chart_data['prices'])}")
        print(f"  Latest price: ${chart_data['prices'][-1][1]:,.2f}")
        print(f"  Oldest price: ${chart_data['prices'][0][1]:,.2f}")
    else:
        print("[FAILED] Could not fetch market chart")

    # Test 3: Get trending coins
    print("\nTest 3: Fetching trending coins...")
    trending = mcp.get_trending_coins(limit=3)

    if trending:
        print("[OK] Trending coins fetched successfully")
        for i, coin in enumerate(trending, 1):
            print(f"  {i}. {coin['name']} ({coin['symbol']})")
    else:
        print("[FAILED] Could not fetch trending coins")

    # Print summary
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

    if price_data:
        print("[OK] CoinGecko MCP client working correctly")
    else:
        print("[WARNING] Some tests failed - check API key and rate limits")


if __name__ == "__main__":
    main()
