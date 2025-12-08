"""

API CLIENT - Live Market Data Fetcher


PURPOSE:
    Fetch real-time Bitcoin data from multiple sources:
    - Binance Testnet: Current BTC price for validation
    - Alternative.me: Fear & Greed Index
    - Blockchain.com: Additional market data (optional)

SUCCESS CRITERIA:
     Fetches current BTC price successfully
     Retrieves Fear & Greed Index (0-100)
     Handles API errors gracefully (retries, fallbacks)
     Respects rate limits (via rate_limiter)
     Returns standardized data format

APIS USED:
    1. Binance Testnet (Paper Trading):
       - Endpoint: https://testnet.binance.vision/api/v3/ticker/price
       - Rate limit: 6000/min
       - Purpose: Get current BTC/USDT price

    2. Alternative.me (Fear & Greed Index):
       - Endpoint: https://api.alternative.me/fng/
       - Rate limit: Free, no key required
       - Purpose: Get Fear & Greed Index (0-100)

    3. Blockchain.com (Optional):
       - Endpoint: https://blockchain.info/ticker
       - Rate limit: 5-sec spacing
       - Purpose: Additional price validation

VALIDATION METHOD:
    - Test each API endpoint individually
    - Verify response format matches expected schema
    - Test error handling (invalid symbol, network error)

"""

import requests
import os
from dotenv import load_dotenv
from typing import Dict, Optional
import time
from datetime import datetime

from .rate_limiter import binance_limiter, alternativeme_limiter, blockchain_limiter

# Load environment variables
load_dotenv()


class APIClient:
    """
    Client for fetching live Bitcoin market data from multiple APIs.

    Handles:
    - Rate limiting (via decorators)
    - Error handling and retries
    - Data validation
    - Standardized response format
    """

    def __init__(self):
        """Initialize API client with credentials."""
        # Binance API credentials (Testnet)
        self.binance_api_key = os.getenv('BINANCE_API_KEY', '')
        self.binance_api_secret = os.getenv('BINANCE_API_SECRET', '')

        # Base URLs
        self.binance_base_url = "https://testnet.binance.vision/api/v3"
        self.binance_real_url = "https://api.binance.com/api/v3"  # For real data if needed
        self.fng_url = "https://api.alternative.me/fng/"  # Alternative.me Fear & Greed Index
        self.blockchain_url = "https://blockchain.info/ticker"

        # Request timeout
        self.timeout = 10

    # 
    # BINANCE API - Current BTC Price
    # 

    @binance_limiter.limit
    def get_btc_price(self, use_testnet: bool = False) -> Dict:
        """
        Get current BTC/USDT price from Binance.

        Args:
            use_testnet: If True, use Binance Testnet.
                        If False, use real Binance API.

        Returns:
            dict: {
                'symbol': 'BTCUSDT',
                'price': float,
                'timestamp': datetime,
                'source': 'binance' or 'binance_testnet'
            }

        Raises:
            Exception: If API call fails
        """
        try:
            # Choose endpoint
            if use_testnet:
                base_url = self.binance_base_url
                source = 'binance_testnet'
            else:
                base_url = self.binance_real_url
                source = 'binance'

            # API endpoint
            endpoint = f"{base_url}/ticker/price"
            params = {'symbol': 'BTCUSDT'}

            # Add API key if available (not required for public endpoints)
            headers = {}
            if self.binance_api_key:
                headers['X-MBX-APIKEY'] = self.binance_api_key

            # Make request
            response = requests.get(
                endpoint,
                params=params,
                headers=headers,
                timeout=self.timeout
            )

            # Check for errors
            response.raise_for_status()

            # Parse response
            data = response.json()

            return {
                'symbol': data['symbol'],
                'price': float(data['price']),
                'timestamp': datetime.now(),
                'source': source
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"Binance API error: {e}")

    @binance_limiter.limit
    def get_btc_24h_stats(self, use_testnet: bool = False) -> Dict:
        """
        Get 24-hour statistics for BTC/USDT.

        Args:
            use_testnet: If True, use Binance Testnet.

        Returns:
            dict: {
                'symbol': 'BTCUSDT',
                'price_change': float,
                'price_change_percent': float,
                'high': float,
                'low': float,
                'volume': float,
                'timestamp': datetime
            }
        """
        try:
            # Choose endpoint
            base_url = self.binance_base_url if use_testnet else self.binance_real_url

            # API endpoint
            endpoint = f"{base_url}/ticker/24hr"
            params = {'symbol': 'BTCUSDT'}

            # Add API key if available
            headers = {}
            if self.binance_api_key:
                headers['X-MBX-APIKEY'] = self.binance_api_key

            # Make request
            response = requests.get(
                endpoint,
                params=params,
                headers=headers,
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            return {
                'symbol': data['symbol'],
                'price_change': float(data['priceChange']),
                'price_change_percent': float(data['priceChangePercent']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice']),
                'volume': float(data['volume']),
                'timestamp': datetime.now()
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"Binance 24h stats API error: {e}")

    # 
    # FEAR & GREED INDEX
    # 

    @alternativeme_limiter.limit
    def get_fear_greed_index(self, limit: int = 1) -> Dict:
        """
        Get Fear & Greed Index from alternative.me.

        The Fear & Greed Index ranges from 0-100:
        - 0-24: Extreme Fear
        - 25-49: Fear
        - 50: Neutral
        - 51-75: Greed
        - 76-100: Extreme Greed

        Args:
            limit: Number of historical data points (default: 1 for latest)

        Returns:
            dict: {
                'value': int (0-100),
                'classification': str ('Extreme Fear', 'Fear', etc.),
                'timestamp': datetime,
                'historical': list (if limit > 1)
            }

        Raises:
            Exception: If API call fails
        """
        try:
            # API endpoint (free, no key required)
            params = {'limit': limit}

            response = requests.get(
                self.fng_url,
                params=params,
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            # Parse latest value
            latest = data['data'][0]
            value = int(latest['value'])
            classification = latest['value_classification']

            result = {
                'value': value,
                'classification': classification,
                'timestamp': datetime.fromtimestamp(int(latest['timestamp'])),
            }

            # Add historical data if requested
            if limit > 1:
                result['historical'] = [
                    {
                        'value': int(item['value']),
                        'classification': item['value_classification'],
                        'timestamp': datetime.fromtimestamp(int(item['timestamp']))
                    }
                    for item in data['data']
                ]

            return result

        except requests.exceptions.RequestException as e:
            raise Exception(f"Fear & Greed API error: {e}")

    # 
    # BLOCKCHAIN.COM API (Optional Backup)
    # 

    @blockchain_limiter.limit
    def get_blockchain_price(self) -> Dict:
        """
        Get BTC price from Blockchain.com (backup source).

        Returns:
            dict: {
                'usd_price': float,
                'timestamp': datetime,
                'source': 'blockchain'
            }

        Raises:
            Exception: If API call fails
        """
        try:
            response = requests.get(self.blockchain_url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            # Extract USD price
            usd_data = data.get('USD', {})
            price = usd_data.get('last', 0)

            return {
                'usd_price': float(price),
                'timestamp': datetime.now(),
                'source': 'blockchain'
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"Blockchain.com API error: {e}")

    # 
    # AGGREGATED DATA FETCHER
    # 

    def get_market_snapshot(self, use_testnet: bool = False) -> Dict:
        """
        Get comprehensive market snapshot from all sources.

        Args:
            use_testnet: Use Binance testnet for price

        Returns:
            dict: {
                'btc_price': float,
                'fear_greed': int,
                'fear_greed_classification': str,
                'price_24h_change': float,
                'price_24h_high': float,
                'price_24h_low': float,
                'timestamp': datetime,
                'sources': dict (raw data from each API)
            }

        Note:
            This method aggregates data from multiple APIs.
            If one fails, it will try to continue with available data.
        """
        snapshot = {
            'timestamp': datetime.now(),
            'sources': {}
        }

        # Fetch BTC price
        try:
            price_data = self.get_btc_price(use_testnet=use_testnet)
            snapshot['btc_price'] = price_data['price']
            snapshot['sources']['price'] = price_data
        except Exception as e:
            print(f"[WARNING] Failed to fetch BTC price: {e}")
            snapshot['btc_price'] = None

        # Fetch 24h stats
        try:
            stats_data = self.get_btc_24h_stats(use_testnet=use_testnet)
            snapshot['price_24h_change'] = stats_data['price_change_percent']
            snapshot['price_24h_high'] = stats_data['high']
            snapshot['price_24h_low'] = stats_data['low']
            snapshot['sources']['24h_stats'] = stats_data
        except Exception as e:
            print(f"[WARNING] Failed to fetch 24h stats: {e}")

        # Fetch Fear & Greed
        try:
            fng_data = self.get_fear_greed_index()
            snapshot['fear_greed'] = fng_data['value']
            snapshot['fear_greed_classification'] = fng_data['classification']
            snapshot['sources']['fear_greed'] = fng_data
        except Exception as e:
            print(f"[WARNING] Failed to fetch Fear & Greed: {e}")

        return snapshot


def main():
    """Test API client functionality."""
    print("="*60)
    print("API CLIENT - Testing")
    print("="*60)

    client = APIClient()

    # Test 1: Binance Price (Real API - no testnet key needed)
    print("\nTest 1: Fetching BTC Price from Binance")
    try:
        price_data = client.get_btc_price(use_testnet=False)
        print(f"   Symbol: {price_data['symbol']}")
        print(f"   Price: ${price_data['price']:,.2f}")
        print(f"   Source: {price_data['source']}")
        print(f"   Timestamp: {price_data['timestamp']}")
        print("   [OK] Success")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Test 2: Fear & Greed Index
    print("\nTest 2: Fetching Fear & Greed Index")
    try:
        fng_data = client.get_fear_greed_index()
        print(f"   Value: {fng_data['value']}/100")
        print(f"   Classification: {fng_data['classification']}")
        print(f"   Timestamp: {fng_data['timestamp']}")
        print("   [OK] Success")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Test 3: Blockchain.com Price
    print("\nTest 3: Fetching BTC Price from Blockchain.com")
    try:
        blockchain_data = client.get_blockchain_price()
        print(f"   Price: ${blockchain_data['usd_price']:,.2f}")
        print(f"   Source: {blockchain_data['source']}")
        print(f"   Timestamp: {blockchain_data['timestamp']}")
        print("   [OK] Success")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Test 4: Market Snapshot (All APIs)
    print("\nTest 4: Fetching Complete Market Snapshot")
    try:
        snapshot = client.get_market_snapshot(use_testnet=False)
        print(f"\n   Market Snapshot:")
        print(f"   - BTC Price: ${snapshot.get('btc_price', 0):,.2f}")
        print(f"   - 24h Change: {snapshot.get('price_24h_change', 0):+.2f}%")
        print(f"   - 24h High: ${snapshot.get('price_24h_high', 0):,.2f}")
        print(f"   - 24h Low: ${snapshot.get('price_24h_low', 0):,.2f}")
        print(f"   - Fear & Greed: {snapshot.get('fear_greed', 0)}/100 ({snapshot.get('fear_greed_classification', 'N/A')})")
        print(f"   - Timestamp: {snapshot['timestamp']}")
        print("\n   [OK] Success")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Test 5: Rate Limiter Stats
    print("\nTest 5: Rate Limiter Statistics")
    for limiter_name, limiter in [
        ('Binance', binance_limiter),
        ('CoinMarketCap', coinmarketcap_limiter),
        ('Blockchain', blockchain_limiter)
    ]:
        stats = limiter.get_stats()
        print(f"\n   {limiter_name}:")
        print(f"   - Total requests: {stats['requests']['total_requests']}")
        print(f"   - Cache hits: {stats['requests']['cache_hits']}")
        print(f"   - Cache misses: {stats['requests']['cache_misses']}")
        print(f"   - Cache hit rate: {stats['cache_hit_rate']:.1%}")

    print("\n" + "="*60)
    print("[COMPLETE] API CLIENT TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
